from datetime import timedelta
from datetime import datetime, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from auth.schemas import GetUserResponse, SignupResponse
from config import SECRET_KEY, ALGORITHM
from .db_connection import users_collection
from .models import TokenData, Users


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/signin")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)


def get_user(email: str) -> None | GetUserResponse:
    """
    Retrieve a user from the database by email.

    :param email: The email address of the user to retrieve.
    :return: The user as a dictionary, or None if the user does not exist.
    """
    user: dict = users_collection.find_one({"email": email})

    if not user:
        return None
    
    user_in_db = GetUserResponse(
        id=str(user["_id"]),
        email=user["email"],
        username=user.get("username"),
        full_name=user["full_name"],
        phone_number=user.get("phone_number"),
        is_active=user["is_active"],
        hashed_password=user["hashed_password"]
    )

    return user_in_db


def authenticate_user(email: str, password: str):
    """
    Authenticate a user by email and password. Return the user if
    authentication is successful, and False otherwise.
    """
    user = get_user(email)

    if not user:
        return False
    
    if not verify_password(password, user.hashed_password):
        return False
    
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = timedelta(minutes=300)):
    """
    Create an access token for the given user data.

    :param data: The data to encode in the access token.
    :param expires_delta: The time delta for which the token is valid.
    :return: The encoded access token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        email = payload.get("email")
        id = payload.get("id")

        if email is None:
            raise credentials_exception
        token_data = TokenData(
            username=username,
            email=email,
            id=id
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = get_user(email=token_data.email)

    if user is None:
        raise credentials_exception
    
    return user.id


# insert new user
def create_user(user: Users) -> SignupResponse:
    new_user = users_collection.insert_one(user.model_dump())

    new_user_response = SignupResponse(
        message="User created successfully",
        id=str(new_user.inserted_id),
        email=user.email,
        username=user.username,
        full_name=user.full_name
    )

    return new_user_response


    