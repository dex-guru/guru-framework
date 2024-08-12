import json
import re

import uuid
from functools import partial
from typing import Annotated, List, Optional

from aiocache import caches
from aiocache.decorators import cached
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.params import Path, Query
from pydantic import UUID4
from starlette.responses import JSONResponse
from tortoise.query_utils import Prefetch

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from bot.services.users import create_camunda_user
from fa_admin.art_models import Art, ArtCollection, Event, ArtLikes
from fa_admin.dependencies import (
    sys_key_depends,
    sys_key_or_jwt_depends,
    auth_dependency,
)
from fa_admin.flow_models import ExternalWorker, Strategy, Invite, Flow
from fa_admin.models import User
from fa_admin.rest_models.api_rest_models import UserRest, AuthTokenRest
from fa_admin.rest_models.art_rest_models import ArtRest, ArtCollectionRest, EventRest
from fa_admin.rest_models.flow_rest_models import (
    ExternalWorkerRest,
    StrategyRest,
    FlowRest,
)
from fa_admin.utils import (
    make_update_dict,
    CACHE_CONFIG,
    create_background_task as _create_background_task,
)

router = APIRouter()


# Configure the cache
caches.set_config({"default": CACHE_CONFIG})
background_tasks = set()
create_background_task = partial(_create_background_task, background_tasks)



def remove_hyphens_from_uuid(uuid_str: str) -> str:
    """Remove hyphens from a UUID string."""
    return uuid_str.replace('-', '')


def add_hyphens_to_uuid(uuid_str: str) -> str:
    """Add hyphens to a UUID string."""
    return re.sub(r'(\w{8})(\w{4})(\w{4})(\w{4})(\w{12})', r'\1-\2-\3-\4-\5', uuid_str)

@router.get("/health_check")
async def health():
    return {"status": "ok"}


@router.post(
    "/users",
    response_model=UserRest,
    response_model_by_alias=True,
)
async def create_user(
    token: Annotated[str, Depends(sys_key_depends)],
    webapp_user_id: uuid.UUID = Body(None),
    username: str = Body(""),
    first_name: str = Body(""),
    last_name: str = Body(""),
    email: str = Body(""),
    language_code: str = Body("en"),
    is_admin: bool = Body(False),
    is_suspicious: bool = Body(False),
    telegram_user_id: int = Body(None),
    is_block: bool = Body(False),
    is_premium: bool = Body(False),
):
    existing_user = await User.filter(webapp_user_id=webapp_user_id).first()
    if existing_user:
        return JSONResponse({"message": "User already exists"}, status_code=405)
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        language_code=language_code,
        is_admin=is_admin,
        is_suspicious=is_suspicious,
        telegram_user_id=telegram_user_id,
        camunda_user_id=None,
        camunda_key=str(uuid.uuid4()),
        webapp_user_id=webapp_user_id,
        is_block=is_block,
        is_premium=is_premium,
        email=email,
    )
    try:
        await user.save()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    try:
        user.camunda_user_id = remove_hyphens_from_uuid(str(user.id))
        await create_camunda_user(user)
        await user.save()
    except Exception as e:
        await user.delete()
        return JSONResponse({"error": str(e)}, status_code=400)

    try:
        rest_model = UserRest.model_validate(user)
        return rest_model
    except Exception as e:
        await user.delete()
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/users",
            response_model=UserRest,
            dependencies=[Depends(sys_key_or_jwt_depends)])
@cached(ttl=5, **CACHE_CONFIG)
async def get_user_by(
        token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
        webapp_user_id: Optional[UUID4] = Query(None),
        telegram_user_id: Optional[int] = Query(None),
        camunda_user_id: Optional[str] = Query(None),
):
    if webapp_user_id is None and camunda_user_id is None and telegram_user_id is None:
        raise HTTPException(status_code=400, detail="Either webapp_user_id or camunda_user_id must be provided")

    user = None
    if webapp_user_id:
        user = await User.filter(webapp_user_id=webapp_user_id).first()
    if not user and camunda_user_id:
        user = await User.filter(camunda_user_id=camunda_user_id).first()
    if telegram_user_id:
        user = await User.filter(telegram_user_id=telegram_user_id).first()

    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)

    try:
        rest_model = UserRest.model_validate(user)
        return rest_model
    except Exception as e:
        await user.delete()
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/login/{webapp_user_id}", response_model=AuthTokenRest)
@cached(ttl=5, **CACHE_CONFIG)
async def login(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    webapp_user_id: uuid.UUID = Path(...),
):
    if not webapp_user_id:
        return JSONResponse({"message": "No form data received"}, status_code=400)
    user = await User.filter(webapp_user_id=webapp_user_id).first()
    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)
    user_claims = {
        "id": str(user.id),
        "is_admin": user.is_admin,
        "is_suspicious": user.is_suspicious,
        "is_block": user.is_block,
        "is_premium": user.is_premium,
        "webapp_user_id": str(user.webapp_user_id),
        "username": str(user.username),
        "first_name": str(user.first_name),
        "last_name": str(user.last_name),
        "language_code": user.language_code,
        # TODO remove when migrated to JWT on FE
        "camunda_user_id": user.camunda_user_id,
        "camunda_key": str(user.camunda_key),
        "telegram_user_id": user.telegram_user_id,
    }
    access_token: bytes | str = await auth.create_access_token(
        subject=str(user.id), user_claims=user_claims
    )
    refresh_token: bytes | str = await auth.create_refresh_token(
        subject=str(user.id), user_claims=user_claims
    )

    if isinstance(access_token, bytes):
        access_token = access_token.decode()
    if isinstance(refresh_token, bytes):
        refresh_token = refresh_token.decode()
    return AuthTokenRest(access_token=access_token, refresh_token=refresh_token)


@router.get("/refresh", dependencies=[Depends(AuthJWTBearer())])
async def refresh_token(auth: AuthJWT = Depends(AuthJWTBearer())):
    await auth.jwt_refresh_token_required()
    user_id = await auth.get_jwt_subject()
    user_claims = await auth.get_raw_jwt()
    access_token = await auth.create_access_token(
        subject=user_id, user_claims=user_claims
    )
    return {"access_token": access_token}


@router.get(
    "/arts",
    response_model=list[ArtRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=10, **CACHE_CONFIG)
async def get_arts_sys(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    limit: int = 10,
    offset: int = 0,
    parameters: str = Query(..., description="Query parameters as JSON string"),
):
    await token.jwt_optional()
    user_id = await token.get_jwt_subject()
    if parameters:
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            return JSONResponse({"message": "Invalid parameters"}, status_code=400)
        arts = (
            await Art.filter(**params)
            .limit(limit)
            .offset(offset)
            .prefetch_related(
                "likes",
                Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
                "nft_metadata",
            )
        )
    else:
        arts = (
            await Art.all()
            .limit(limit)
            .offset(offset)
            .prefetch_related(
                "likes",
                Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
                "nft_metadata",
            )
        )
    data = [
        ArtRest.parse_obj(
            dict(
                art,
                likes=len(art.likes),
                is_liked=bool(art.liked),
                token_id=art.nft_metadata[0].token_id if art.nft_metadata else None,
            )
        )
        for art in arts
    ]
    return data


@router.post(
    "/art",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_depends)],
)
async def create_art(
    token: Annotated[AuthJWT, Depends(sys_key_depends)],
    name: str | None = Body(None),
    description: str | None = Body(None),
    img_picture: str | None = Body(None),
    description_prompt: str | None = Body(None),
    art_type: str = Body(..., validation_alias="type", alias="type"),
    tags: List[str] = Body([]),
    parent_id: str = Body(None),
    reference_id: str = Body(None),
    camunda_user_id: str = Body(None),
    user_id: str = Body(None),
    webapp_user_id: str = Body(None),
):
    # await auth.jwt_required()
    # user_id = await auth.get_jwt_subject()
    if not user_id:
        if camunda_user_id:
            user = await User.filter(camunda_user_id=camunda_user_id).first()
        elif webapp_user_id:
            user = await User.filter(webapp_user_id=webapp_user_id).first()
        else:
            return {
                "message": "user_id, camunda_user_id or webapp_user_id required"
            }, 404
        if user:
            user_id = user.id
        else:
            raise HTTPException(status_code=404, detail="User not found")
    art_properties = {
        "name": name,
        "description": description,
        "img_picture": img_picture,
        "description_prompt": description_prompt,
        "type": art_type,
        "tags": tags,
        "user_id": user_id,
    }
    if reference_id:
        art_properties["reference_id"] = reference_id
    if parent_id:
        art_properties["parent_id"] = parent_id
    art = Art(**art_properties)
    try:
        create_background_task(art.save())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    try:
        model = ArtRest.parse_obj(dict(art))
        return model
    except Exception as e:
        create_background_task(art.delete())
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/art/{art_id}",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_art_id(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    art_id: str = Path(...),
):
    user_id = await auth.get_jwt_subject()
    art_id = art_id.strip()
    art = await Art.get_or_none(id=art_id).prefetch_related(
        "nft_metadata",
        "likes",
        Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
    )

    if not art:
        raise HTTPException(status_code=404, detail="Art not found")

    # If nft_metadata is prefetched, it will be in art.nft_metadata
    token_id = None
    if art.nft_metadata:
        token_id = art.nft_metadata[0].token_id

    return ArtRest.parse_obj(
        dict(art, likes=len(art.likes), token_id=token_id, is_liked=bool(art.liked))
    )


@router.post("/art/{art_id}/like", response_model=ArtRest, response_model_by_alias=True)
async def like_art(
    art_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art = await Art.get_or_none(id=art_id).prefetch_related(
        Prefetch("likes", queryset=ArtLikes.filter(user_id=user_id), to_attr="liked")
    )
    if not art:
        return JSONResponse({"message": "Art not found"}, status_code=404)
    if art.liked:
        create_background_task(art.liked[0].delete())
        return ArtRest.parse_obj(dict(art, likes=len(art.likes) - 1, is_liked=False))
    create_background_task(ArtLikes(art_id=art_id, user_id=user_id).save())
    return ArtRest.parse_obj(dict(art, likes=len(art.likes) + 1, is_liked=True))


@router.get(
    "/arts/{art_id}",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_arts_id(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    art_id: str = Path(...),
):
    user_id = await token.get_jwt_subject()
    art_id = art_id.strip()
    art = await Art.get_or_none(id=art_id).prefetch_related(
        "nft_metadata",
        "likes",
        Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
    )

    if not art:
        raise HTTPException(status_code=404, detail="Art not found")

    # If nft_metadata is prefetched, it will be in art.nft_metadata
    token_id = None
    if art.nft_metadata:
        token_id = art.nft_metadata[0].token_id

    return ArtRest.parse_obj(
        dict(art, likes=len(art.likes), token_id=token_id, is_liked=bool(art.liked))
    )


@router.put(
    "/art/{art_id}",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def update_art(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    art_id: str = Path(...),
    name: str | None = Body(None),
    description: str | None = Body(None),
    img_picture: str | None = Body(None),
    description_prompt: str | None = Body(None),
    art_type: str = Body(..., validation_alias="type", alias="type"),
    tags: List[str] = Body(None),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    art = await Art.filter(id=art_id).first()
    if not art:
        return JSONResponse({"message": "Art not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        description_prompt=description_prompt,
        type=art_type,
        tags=tags,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    try:
        art = await art.update_from_dict(update_dict)
        art.created_at = (
            art.created_at.replace(tzinfo=None)
            if art.created_at.tzinfo
            else art.created_at
        )
        await art.save()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    try:
        model = ArtRest.parse_obj(dict(art))
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.delete(
    "/art/{art_id}",
    dependencies=[Depends(AuthJWTBearer())],
)
async def delete_external_worker(
    art_id: str = Path(...), auth: AuthJWT = Depends(AuthJWTBearer())
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()

    art = await Art.filter(user_id=user_id, id=art_id).first()
    if not art:
        return JSONResponse({"message": "Art not found"}, status_code=404)
    await art.delete()
    return JSONResponse({"message": "Art deleted"}, status_code=200)


@router.get(
    "/art_collection",
    response_model=list[ArtCollectionRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_collections(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    limit: int = 10,
    offset: int = 0,
):
    art_collections = await ArtCollection.all().limit(limit).offset(offset)
    return [
        ArtCollectionRest.model_validate(art_collection)
        for art_collection in art_collections
    ]


@router.post(
    "/art_collection",
    response_model=ArtCollectionRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def create_collection(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    name: str = Body(...),
    symbol: str = Body(...),
    base_uri: str | None = Body(None),
    arts: List = Body([]),
    collection_type: str = Body(..., validation_alias="type", alias="type"),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    new_strategy = ArtCollection(
        name=name,
        user_id=user_id,
        base_uri=base_uri,
        symbol=symbol,
        arts=arts,
        type=collection_type,
    )
    try:
        model = ArtCollectionRest.model_validate(new_strategy)
        await new_strategy.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/art_collection/{collection_id}",
    response_model=ArtCollectionRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_collection(
    collection_id: str = Path(...), auth: AuthJWT = Depends(sys_key_or_jwt_depends)
):
    collection = await ArtCollection.filter(id=collection_id).first()
    if not collection:
        return JSONResponse({"message": "collection not found"}, status_code=404)
    return ArtCollectionRest.model_validate(collection)


@router.put(
    "/art_collection/{collection_id}",
    response_model=ArtCollectionRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def update_collection(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    collection_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    img_event_cover: str = Body(None),
    collection_type: str = Body(None, validation_alias="type", alias="type"),
    address: str = Body(None),
    location: str = Body(None),
    collections: dict = Body(None),
    reference_id: int = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_collection = await ArtCollection.filter(
        user_id=user_id, id=collection_id
    ).first()
    if not art_collection:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_event_cover=img_event_cover,
        type=collection_type,
        address=address,
        location=location,
        reference_id=reference_id,
        collections=collections,
    )
    update_art_collection = await art_collection.update_from_dict(update_dict)
    model = ArtCollectionRest.model_validate(update_art_collection)
    await update_art_collection.save()
    return model


@router.delete(
    "/art_collection/{collection_id}", dependencies=[Depends(AuthJWTBearer())]
)
async def delete_collection(
    collection_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_collection = await ArtCollection.filter(
        user_id=user_id, id=collection_id
    ).first()
    if not art_collection:
        return JSONResponse({"message": "Art Collection not found"}, status_code=404)
    await art_collection.delete()
    return JSONResponse({"message": "Art Collection deleted"}, status_code=200)


@router.get(
    "/event",
    response_model=list[EventRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_collections(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    limit: int = 10,
    offset: int = 0,
):
    event_collections = await Event.all().limit(limit).offset(offset)
    return [
        EventRest.model_validate(event_collection)
        for event_collection in event_collections
    ]


@router.post(
    "/event",
    response_model=EventRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def create_event(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    name: str = Body(...),
    description: str = Body(...),
    address: str | None = Body(None),
    location: str | None = Body(None),
    img_event_cover: str | None = Body(None),
    collections: dict | None = Body(None),
    event_type: str = Body(..., validation_alias="type", alias="type"),
    reference_id: str | None = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    if not reference_id:
        reference_id = user_id
    new_strategy = Event(
        name=name,
        user_id=user_id,
        description=description,
        address=address,
        location=location,
        img_event_cover=img_event_cover,
        collections=collections,
        type=event_type,
        reference_id=reference_id,
    )
    try:
        model = EventRest.model_validate(new_strategy)
        await new_strategy.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/event/{event_id}",
    response_model=EventRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_event(event_id: str = Path(...), auth: AuthJWT = Depends(AuthJWTBearer())):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    event = await Event.filter(user_id=user_id, id=event_id).first()
    return EventRest.model_validate(event)


@router.put(
    "/event/{event_id}",
    response_model=EventRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def update_event(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    event_id: str = Path(...),
    name: str = Body(...),
    description: str = Body(...),
    address: str | None = Body(None),
    location: str | None = Body(None),
    img_event_cover: str | None = Body(None),
    collections: dict | None = Body(None),
    event_type: str = Body(..., validation_alias="type", alias="type"),
    reference_id: str | None = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_event = await Event.filter(user_id=user_id, id=event_id).first()
    if not art_event:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        user_id=user_id,
        description=description,
        address=address,
        location=location,
        img_event_cover=img_event_cover,
        collections=collections,
        type=event_type,
        reference_id=reference_id,
    )
    update_art_event = await art_event.update_from_dict(update_dict)
    model = EventRest.model_validate(update_art_event)
    await update_art_event.save()
    return model


@router.delete("/art/event/{event_id}", dependencies=[Depends(AuthJWTBearer())])
async def delete_event(
    event_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_event = await Event.filter(user_id=user_id, id=event_id).first()
    if not art_event:
        return JSONResponse({"message": "Art Collection not found"}, status_code=404)
    await art_event.delete()
    return JSONResponse({"message": "Art Collection deleted"}, status_code=200)


@router.get(
    "/external_workers",
    response_model=list[ExternalWorkerRest],
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_external_workers(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    limit: int = 10,
    offset: int = 0,
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    external_workers = (
        await ExternalWorker.filter(user_id=user_id).limit(limit).offset(offset)
    )
    return [
        ExternalWorkerRest.model_validate(external_worker)
        for external_worker in external_workers
    ]


@router.post(
    "/external_workers",
    response_model=ExternalWorkerRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
async def create_external_worker(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    name: str = Body(...),
    description: str = Body(...),
    external_worker_type: str = Body(..., validation_alias="type", alias="type"),
    img_picture: str | None = Body(None),
    schema: dict | None = Body(None),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    new_external_worker = ExternalWorker(
        name=name,
        user_id=user_id,
        description=description,
        img_picture=img_picture,
        schema=schema,
        type=external_worker_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    model = ExternalWorkerRest.model_validate(new_external_worker)
    await new_external_worker.save()
    return model


@router.get(
    "/external_workers/{external_worker_id}",
    response_model=ExternalWorkerRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_external_worker(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    external_worker_id: str = Path(...),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    external_worker = await ExternalWorker.filter(
        user_id=user_id, id=external_worker_id
    ).first()
    return ExternalWorkerRest.model_validate(external_worker)


@router.put(
    "/external_workers/{external_worker_id}",
    response_model=ExternalWorkerRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
async def update_external_worker(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    external_worker_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    schema: dict = Body(None),
    img_picture: str = Body(None),
    external_worker_type: str = Body(None, validation_alias="type", alias="type"),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    external_worker = await ExternalWorker.filter(
        user_id=user_id, id=external_worker_id
    ).first()
    if not external_worker:
        return JSONResponse({"message": "External worker not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        type=external_worker_type,
        parent_id=parent_id,
        reference_id=reference_id,
        schema=schema,
    )
    try:
        updated_worker = await external_worker.update_from_dict(update_dict)
        model = ExternalWorkerRest.model_validate(updated_worker)
        await updated_worker.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.delete(
    "/external_workers/{external_worker_id}",
    dependencies=[Depends(auth_dependency)],
)
async def delete_external_worker(
    external_worker_id: str = Path(...), auth: AuthJWT = Depends(AuthJWTBearer())
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()

    external_worker = await ExternalWorker.filter(
        user_id=user_id, id=external_worker_id
    ).first()
    if not external_worker:
        return JSONResponse({"message": "External worker not found"}, status_code=404)
    await external_worker.delete()
    return JSONResponse({"message": "External worker deleted"}, status_code=200)


@router.get(
    "/strategy",
    response_model=list[StrategyRest],
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_strategies(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    limit: int = 10,
    offset: int = 0,
):
    strategies = await Strategy.all().limit(limit).offset(offset)
    return [StrategyRest.model_validate(strategy) for strategy in strategies]


@router.get(
    "/flows",
    response_model=list[FlowRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_flows(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    limit: int = 10,
    offset: int = 0,
):
    flows = await Flow.all().limit(limit).offset(offset)
    return [FlowRest.model_validate(flow) for flow in flows]


@router.get(
    "/flow/{flow_id}",
    response_model=FlowRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_flow(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    flow_id: str = Path(...),
):
    flow = await Flow.filter(id=flow_id).first()
    return FlowRest.model_validate(flow)


@router.put(
    "/flow/{flow_id}",
    response_model=FlowRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def update_flow(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    flow_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    img_picture: str = Body(None),
    flow_type: str = Body(None, validation_alias="type", alias="type"),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    flow = await Flow.filter(id=flow_id).first()
    if not flow:
        return JSONResponse({"message": "Flow not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        type=flow_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    updated_flow = await flow.update_from_dict(update_dict)
    model = FlowRest.model_validate(flow)
    await updated_flow.save()
    return model


@router.delete("/flow/{flow_id}", dependencies=[Depends(auth_dependency)])
async def delete_flow(
    flow_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    flow = await Flow.filter(user_id=user_id, id=flow_id).first()
    if not flow:
        return JSONResponse({"message": "Flow not found"}, status_code=404)
    await flow.delete()
    return JSONResponse({"message": "Flow deleted"}, status_code=200)


@router.post(
    "/flow",
    response_model=FlowRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def create_flow(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    reference_id: str | None = Body(None),
    parent_id: str | None = Body(None),
    user_id: str | None = Body(None),
    name: str = Body(...),
    description: str = Body(...),
    img_picture: str | None = Body(None),
    flow_type: str = Body(..., validation_alias="type", alias="type"),
):
    # TODO: here there is an issue if user loggined through GPT he can specify othe user_id and p[ost from him, need to fix
    # if not user_id:
    #     user_id = await auth.get_jwt_subject()
    if not reference_id:
        reference_id = user_id
    if not parent_id:
        parent_id = user_id
    new_flow = Flow(
        name=name,
        user_id=user_id,
        description=description,
        img_picture=img_picture,
        type=flow_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    try:
        model = FlowRest.model_validate(new_flow)
        await new_flow.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post(
    "/strategy",
    response_model=StrategyRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
async def create_strategy(
    auth: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    reference_id: str | None = Body(None),
    parent_id: str | None = Body(None),
    user_id: str | None = Body(None),
    name: str = Body(...),
    description: str = Body(...),
    img_picture: str | None = Body(None),
    schema: dict | None = Body(None),
    strategy_type: str = Body(..., validation_alias="type", alias="type"),
):
    # TODO: here there is an issue if user loggined through GPT he can specify othe user_id and p[ost from him, need to fix
    if not user_id:
        user_id = await auth.get_jwt_subject()
    if not reference_id:
        reference_id = user_id
    if not parent_id:
        parent_id = user_id
    new_strategy = Strategy(
        name=name,
        user_id=user_id,
        description=description,
        img_picture=img_picture,
        schema=schema,
        type=strategy_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    try:
        model = StrategyRest.model_validate(new_strategy)
        await new_strategy.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/strategy/{strategy_id}",
    response_model=StrategyRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **CACHE_CONFIG)
async def get_strategy(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    strategy_id: str = Path(...),
):
    strategy = await Strategy.filter(id=strategy_id).first()
    return StrategyRest.model_validate(strategy)


@router.put(
    "/strategy/{strategy_id}",
    response_model=StrategyRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def update_strategy(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    strategy_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    img_picture: str = Body(None),
    strategy_type: str = Body(None, validation_alias="type", alias="type"),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    strategy = await Strategy.filter(id=strategy_id).first()
    if not strategy:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        type=strategy_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    updated_strategy = await strategy.update_from_dict(update_dict)
    model = StrategyRest.model_validate(strategy)
    await updated_strategy.save()
    return model


@router.delete("/strategy/{strategy_id}", dependencies=[Depends(auth_dependency)])
async def delete_strategy(
    strategy_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    strategy = await Strategy.filter(user_id=user_id, id=strategy_id).first()
    if not strategy:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    await strategy.delete()
    return JSONResponse({"message": "Strategy deleted"}, status_code=200)


@router.post(
    "/invites/chain/{chain_id}/token/{token_id}",
    include_in_schema=False,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def invite_user(
    chain_id: int = Path(...),
    token_id: int = Path(...),
    wallet_address: str = Body(),
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
):
    if not await Invite.filter(wallet_address=wallet_address):
        invite = Invite(
            token_id=token_id, chain_id=chain_id, wallet_address=wallet_address.lower()
        )
        await invite.save()
        return JSONResponse({"id": str(invite.id)}, status_code=200)
    return JSONResponse({"message": "User already invited"}, status_code=200)


@router.post(
    "/invites/chain/{chain_id}",
    include_in_schema=False,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def mark_users_as_updated(
    chain_id: int = Path(...),
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
):
    updated = []
    invites = await Invite.filter(chain_id=chain_id, is_updated_merkle_root=False).all()
    for invite in invites:
        invite.is_updated_merkle_root = True
        updated.append(invite)
    await Invite.bulk_update(
        updated, fields=["id", "is_updated_merkle_root"], batch_size=1000
    )
    return JSONResponse({"message": "Users marked as updated"}, status_code=200)


@router.get(
    "/invites/chain/{chain_id}",
)
@cached(ttl=5, **CACHE_CONFIG)
async def get_invited_wallets(
    auth: AuthJWT = Depends(sys_key_depends),
    chain_id: int = Path(...),
    only_updated: bool = Query(True),
) -> list[str]:
    if only_updated:
        invites = await Invite.filter(chain_id=chain_id, is_updated_merkle_root=True)
    else:
        invites = await Invite.filter(chain_id=chain_id)
    return list({invite.wallet_address.lower() for invite in invites})


@router.get(
    "/invites/chain/{chain_id}/token/{token_id}",
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=5, **CACHE_CONFIG)
async def get_invited_wallets_by_token_id(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    chain_id: int = Path(...),
    token_id: int = Path(...),
) -> list[str]:
    invites = await Invite.filter(token_id=token_id, chain_id=chain_id)
    return [invite.wallet_address for invite in invites]
