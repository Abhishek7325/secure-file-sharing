from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.database import users_collection, files_collection
from app.auth import decode_access_token
from cryptography.fernet import Fernet
import os
from bson.objectid import ObjectId
from datetime import datetime
import shutil

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

SECRET_ENC_KEY = Fernet.generate_key()  # in production, keep this in env
fernet = Fernet(SECRET_ENC_KEY)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    token_data = decode_access_token(token)
    if not token_data or not token_data.email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await users_collection.find_one({"email": token_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "ops":
        raise HTTPException(status_code=403, detail="Only Ops can upload files")
    
    if not file.filename.endswith((".pptx", ".docx", ".xlsx")):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_doc = {
        "filename": file.filename,
        "uploaded_by": current_user["email"],
        "path": file_path,
        "created_at": datetime.utcnow()
    }
    result = await files_collection.insert_one(file_doc)
    return {"message": "File uploaded", "file_id": str(result.inserted_id)}

@router.get("/list")
async def list_files(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only Clients can list files")

    files = files_collection.find()
    return [{"id": str(file["_id"]), "filename": file["filename"]} async for file in files]

@router.get("/download-link/{file_id}")
async def get_download_link(file_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only Clients can get download link")

    encrypted_id = fernet.encrypt(file_id.encode()).decode()
    download_url = f"/file/download/{encrypted_id}"
    return {"download-link": download_url, "message": "success"}

@router.get("/download/{encrypted_id}")
async def download_file(encrypted_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only Clients can download files")

    try:
        file_id = fernet.decrypt(encrypted_id.encode()).decode()
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired link")

    file = await files_collection.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "filename": file["filename"],
        "message": f"File ready to be served from: {file['path']}"
    }
