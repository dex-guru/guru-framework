import dataclasses


@dataclasses.dataclass(frozen=True, slots=True)
class AuthData:
    username: str
    password: str = dataclasses.field(repr=False)
