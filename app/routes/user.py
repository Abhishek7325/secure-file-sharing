# app/routes/user.py
from fastapi import APIRouter, HTTPException, Depends, status
from app.models import UserCreate, UserOut
from app.database import users_collection
from app.auth import get_password_hash, verify_password, create_access_token
from app.auth import decode_access_token
from bson.objectid import ObjectId
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

router = APIRouter()

@router.post("/signup", response_model=UserOut)
async def signup(user: UserCreate):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pwd = get_password_hash(user.password)
    user_data = {
        "email": user.email,
        "password": hashed_pwd,
        "role": user.role,
        "is_verified": False
    }

    res = await users_collection.insert_one(user_data)
    uid = str(res.inserted_id)

    # Return dummy encrypted URL
    encrypted_url = f"/user/verify-email/{uid}"

    return {
        "id": uid,
        "email": user.email,
        "role": user.role,
        "verify_link": encrypted_url
    }

@router.get("/verify-email/{user_id}")
async def verify_email(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_verified": True}})
    return {"message": "Email verified successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_verified", False):
        raise HTTPException(status_code=401, detail="Email not verified")

    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=timedelta(minutes=30))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"]
    }