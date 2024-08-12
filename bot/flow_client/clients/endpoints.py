from typing import ClassVar


class FlowUrls:
    users = "/api/users"

    @classmethod
    def get_users(cls) -> str:
        return f"{cls.users}"

    @classmethod
    def add_users(cls) -> str:
        return f"{cls.users}"
