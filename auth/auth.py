from datetime import timedelta, datetime
from typing import Annotated
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from config import ACCESS_TOKEN_EXPIRE
from .dependencies import authenticate_user, create_access_token, create_user, get_user, hash_password
from auth.db_connection import db
from auth.models import Token, Users
from auth.schemas import Signup


auth_route = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@auth_route.post("/signin")
async def sign_in(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    access_token = create_access_token(
        data = {
            "sub": user.username,
            "email": user.email,
            "id": str(user.id)
        },
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@auth_route.post("/signup")
async def sign_up(user: Signup):
    # check if user already exists
    already_exists = get_user(user.email)

    if already_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    # hash password
    hashed_password = hash_password(user.password)

    # new user
    new_user = Users(
        _id=ObjectId(),
        username=user.username,
        full_name=user.full_name,
        phone_number=user.phone_number,
        email=user.email,
        hashed_password=hashed_password,
        updated_at=datetime.now(),
        last_login=datetime.now(),
        is_active=True,
    )
    
    created_user = create_user(new_user)

    return created_user