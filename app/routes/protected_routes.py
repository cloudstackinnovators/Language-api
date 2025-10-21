from fastapi import APIRouter, Depends
from app.auth.auth_handler import get_current_user
from app.models import User

router = APIRouter()

@router.get("/")
def protected(current_user: User = Depends(get_current_user)):
    return {"message": f"Welcome, {current_user.username}!"}


