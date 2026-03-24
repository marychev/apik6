import uuid

users: dict[str, dict] = {}


def prepare_user(name: str, email: str) -> dict:
    user_id = str(uuid.uuid4())
    user_data = {"id": user_id, "name": name, "email": email}
    users[user_id] = user_data
    return user_data


def get_users_count() -> int:
    return len(users)


def reset_users() -> None:
    users.clear()
