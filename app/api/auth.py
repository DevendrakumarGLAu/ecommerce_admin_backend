"""Authentication endpoints: register, login, refresh, logout, current user, change password."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    CaptchaResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from app.schemas.common import SuccessResponse
from app.schemas.user import ProfileUpdateRequest, UserResponse
from app.services import captcha_service
from app.services.auth_service import AuthService
from app.services.password_reset_service import PasswordResetService

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
    "/register-admin",
    response_model=SuccessResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Sign up for an admin account and get logged in immediately",
    description=(
        "Creates a new admin-role account and returns an access/refresh token pair right away. "
        "Used exclusively by the admin panel's signup screen — unlike /register, this always "
        "assigns the admin role."
    ),
)
async def register_admin(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> SuccessResponse[TokenResponse]:
    tokens = await AuthService(db).register_admin(payload)
    return SuccessResponse(message="Admin account created successfully", data=tokens)


@router.get(
    "/captcha",
    response_model=SuccessResponse[CaptchaResponse],
    summary="Get a login captcha challenge",
    description=(
        "Returns a short-lived, self-hosted captcha (SVG image + id). Submit both, along with what "
        "the user typed, as `captcha_id`/`captcha_text` on POST /auth/login. Single-use — request a "
        "new one for every login attempt (a failed attempt consumes the challenge)."
    ),
)
async def get_captcha() -> SuccessResponse[CaptchaResponse]:
    captcha_id, svg = await captcha_service.generate()
    return SuccessResponse(
        data=CaptchaResponse(captcha_id=captcha_id, svg=svg, expires_in_minutes=settings.CAPTCHA_EXPIRY_MINUTES)
    )


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    summary="Authenticate and obtain an access/refresh token pair",
    description="Validates the captcha and email/password credentials, returning a JWT access/refresh pair.",
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


@router.post(
    "/forgot-password",
    response_model=SuccessResponse[ForgotPasswordResponse],
    summary="Request a password-reset OTP",
    description=(
        "Generates a 6-digit OTP valid for a few minutes and hands it to the OTP notifier. "
        "When `OTP_DEBUG_MODE` is on (the default, for local dev without a real email/SMS "
        "provider) the OTP is also returned in this response — turn it off in production."
    ),
)
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[ForgotPasswordResponse]:
    result = await PasswordResetService(db).request_reset(payload.email)
    return SuccessResponse(message=result.message, data=result)


@router.post(
    "/verify-otp",
    response_model=SuccessResponse[VerifyOtpResponse],
    summary="Verify a password-reset OTP",
    description=(
        "Verifies the 6-digit OTP from /forgot-password. On success, issues a short-lived "
        "`reset_token` — pass that (not the OTP) to /reset-password to actually change the password."
    ),
)
async def verify_otp(
    payload: VerifyOtpRequest, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[VerifyOtpResponse]:
    result = await PasswordResetService(db).verify_otp(payload.email, payload.otp)
    return SuccessResponse(message="OTP verified successfully", data=result)


@router.post(
    "/reset-password",
    response_model=SuccessResponse[None],
    summary="Reset password after OTP verification",
    description="Sets a new password. Requires the `reset_token` obtained from a successful /verify-otp call.",
)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    await PasswordResetService(db).reset_password(payload.email, payload.reset_token, payload.new_password)
    return SuccessResponse(message="Password reset successfully")
