from pydantic import BaseModel


class Signup(BaseModel):
    full_name: str
    username: str | None = None
    email: str
    phone_number: str | None = None
    password: str

class SignupResponse(BaseModel):
    message: str = "User created successfully"
    id: str
    email: str
    username: str | None = None
    full_name: str
    phone_number: str | None = None


class GetUserResponse(BaseModel):
    id: str
    email: str
    username: str | None = None
    full_name: str
    phone_number: str | None = None
    is_active: bool
    hashed_password: str