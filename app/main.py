## Project: Secure File Sharing System (FastAPI Backend)

# Step 1: Entry point - main.py
from fastapi import FastAPI
from app.routes import user, file

app = FastAPI()

# Include routes
app.include_router(user.router, prefix="/user")
app.include_router(file.router, prefix="/file")

@app.get("/")
def root():
    return {"message": "Secure File Sharing System API"}
