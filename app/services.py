import uuid

from app.schemas import UserCreate, UserResponse


def prepare_user(user: UserCreate) -> UserResponse:
    return UserResponse(id=str(uuid.uuid4()), name=user.name, email=user.email)
