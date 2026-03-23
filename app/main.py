from fastapi import FastAPI

from app.schemas import UserCreate, UserResponse

app = FastAPI()

users: dict[int, dict] = {}
next_id = 1


@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    global next_id
    user_data = {"id": next_id, "name": user.name, "email": user.email}
    users[next_id] = user_data
    next_id += 1
    return user_data


@app.get("/users/count")
def get_users_count():
    return {"count": len(users)}


@app.post("/users/reset", status_code=204)
def reset_users():
    global next_id
    users.clear()
    next_id = 1
