import re


def remove_hyphens_from_uuid(uuid_str: str) -> str:
    """Remove hyphens from a UUID string."""
    return uuid_str.replace('-', '')


def add_hyphens_to_uuid(uuid_str: str) -> str:
    """Add hyphens to a UUID string."""
    return re.sub(r'(\w{8})(\w{4})(\w{4})(\w{4})(\w{12})', r'\1-\2-\3-\4-\5', uuid_str)
