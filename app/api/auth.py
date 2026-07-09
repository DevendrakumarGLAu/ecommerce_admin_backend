"""Authentication endpoints: register, login, refresh, logout, current user, change password."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import SuccessResponse
from app.schemas.user import ProfileUpdateRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
    description="Creates a new customer account with a bcrypt-hashed password. Emails must be unique.",
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> SuccessResponse[UserResponse]:
    user = await AuthService(db).register(payload)
    return SuccessResponse(message="Account created successfully", data=UserResponse.model_validate(user))


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    summary="Authenticate and obtain an access/refresh token pair",
    description="Validates email/password credentials and returns a JWT access token and refresh token.",
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> SuccessResponse[TokenResponse]:
    tokens = await AuthService(db).login(payload)
    return SuccessResponse(message="Login successful", data=tokens)


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    summary="Exchange a refresh token for a new token pair",
    description="Rotates the refresh token: the old one is revoked and a new access/refresh pair is issued.",
)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> SuccessResponse[TokenResponse]:
    tokens = await AuthService(db).refresh(payload.refresh_token)
    return SuccessResponse(message="Token refreshed successfully", data=tokens)


@router.post(
    "/logout",
    response_model=SuccessResponse[None],
    summary="Revoke a refresh token",
    description="Blacklists the given refresh token in Redis so it can no longer be used to obtain new access tokens.",
)
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> SuccessResponse[None]:
    await AuthService(db).logout(payload.refresh_token)
    return SuccessResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get the current authenticated user",
    description="Returns the profile of the user identified by the bearer access token.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> SuccessResponse[UserResponse]:
    return SuccessResponse(data=UserResponse.model_validate(current_user))


@router.patch(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Update the current user's profile",
    description="Updates the caller's own first/last name, phone, and avatar URL. Email and role are not self-editable.",
)
async def update_me(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    user = await AuthService(db).update_profile(current_user, payload)
    return SuccessResponse(message="Profile updated successfully", data=UserResponse.model_validate(user))


@router.post(
    "/change-password",
    response_model=SuccessResponse[None],
    summary="Change the current user's password",
    description="Verifies the current password before setting a new bcrypt-hashed password.",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[None]:
    await AuthService(db).change_password(current_user, payload)
    return SuccessResponse(message="Password changed successfully")
