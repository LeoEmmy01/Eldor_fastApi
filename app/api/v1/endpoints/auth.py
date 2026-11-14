from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    UserCreate, UserLogin, Token, PasswordRecoveryRequest, PasswordResetRequest,
)
from app.core.security import (
    get_password_hash, verify_password, create_access_token, decode_access_token,
)
from app.core.email import send_password_reset_email

router = APIRouter()


@router.post("/register", summary="Register a new User")
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    new_user = User(email=user_in.email, hashed_password=get_password_hash(user_in.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "email": new_user.email}


@router.post("/login", response_model=Token, summary="Authenticate User and get JWT access token")
def login_user(form_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/recover-password", summary="Request a password recovery link")
def recover_password(
    payload: PasswordRecoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    generic = {"message": "If the email exists, password recovery instructions have been sent."}

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.is_active:
        return generic  # same answer either way, to prevent email enumeration

    reset_token = create_access_token(
        data={"sub": user.email, "purpose": "password_reset"},
        expires_delta=timedelta(minutes=15),
    )
    # Delivered only to the account's email address, never in the API response.
    # Sending in the background keeps response time the same for existing and unknown emails.
    background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    return generic


@router.post("/reset-password", summary="Reset password using recovery token")
def reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    claims = decode_access_token(payload.token)
    if (
        not claims
        or claims.get("purpose") != "password_reset"
        or claims.get("sub") != payload.email
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password has been successfully reset."}