from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import schemas, models
from app.auth.auth_handler import (
    create_reset_token, decode_token, get_db, hash_password, verify_password,
    create_access_token
)

from app.utils.mail import send_email

FRONTEND_URL = "https://vocablab.net"



router = APIRouter()

@router.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.useremail == user.useremail)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    hashed = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        useremail=user.useremail,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_access_token({"sub": new_user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.useremail == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer", "user": db_user}



@router.post("/forgot-password")
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.useremail == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate reset token (JWT)
    token = create_reset_token({"sub": db_user.username}, expires_minutes=30)
    reset_link = f"{FRONTEND_URL}/reset-password/{token}"

    # Send email
    send_email(
        to_email=db_user.useremail,
        subject="Password Reset Request",
        body=f"Hi {db_user.username},\n\nClick here to reset your password: {reset_link}\n\nThis link will expire in 30 minutes."
    )

    return {"msg": "Password reset email sent successfully"}


@router.post("/change-password")
def change_password(
    request: schemas.ChangePasswordRequest,
    token: str = Query(..., description="Password reset token from email link"),
    db: Session = Depends(get_db)
):
    try:
        # Decode token (contains username or email)
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=400, detail="Invalid token payload")

        # Find user
        db_user = db.query(models.User).filter(models.User.username == username).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update password
        db_user.hashed_password = hash_password(request.new_password)
        db.commit()

        return {"msg": "Password changed successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid or expired token: {e}")