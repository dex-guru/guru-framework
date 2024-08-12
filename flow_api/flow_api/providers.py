from fastapi_admin.providers.login import UsernamePasswordProvider


class LoginProvider(UsernamePasswordProvider):
    pass

    # async def login(self, request: Request, redis: Redis = Depends(get_redis)):
    #     username = request.form.get("username")
    #     password = request.form.get("password")
    #     admin = await self.admin_model.get(username=username)
    #     if not admin:
    #         return {"error": "User not found"}
    #     if not check_password(admin.password, password):
    #         return {"error": "Password is incorrect"}
    #     access_token = await self.create_access_token(admin, redis)
    #     response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    #     response.set_cookie(
    #         key=self.access_token,
    #         value=access_token,
    #         httponly=True,
    #         max_age=constants.ACCESS_TOKEN_EXPIRE,
    #     )
    #     return response
