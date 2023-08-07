from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient
from bson.objectid import ObjectId
import shutil
import os

app = FastAPI()

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["user_registration"]
users_collection = db["users"]
profile_collection = db["profile"]

class UserRegistration(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str

class UserProfile(BaseModel):
    user_id: str
    profile_picture: str

@app.on_event("startup")
def startup_event():
    # Create the collections if they don't exist
    if "users" not in db.list_collection_names():
        db.create_collection("users")
    if "profile" not in db.list_collection_names():
        db.create_collection("profile")

@app.post("/register")
async def register_user(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    profile_picture: UploadFile = File(...)
):
    # Check if email or phone already exist
    existing_user = users_collection.find_one({"$or": [{"email": email}, {"phone": phone}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or phone already exists")

    # Insert user details
    user_data = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "phone": phone
    }
    user_id = str(users_collection.insert_one(user_data).inserted_id)

    profile_picture_data = profile_picture.file.read()

    # Insert profile picture path into the database
    profile_data = {
        "user_id": user_id,
        "profile_picture": profile_picture_data
    }
    profile_collection.insert_one(profile_data)

    return {"message": "User registered successfully"}

@app.get("/user/{user_id}")
def get_user(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    profile = profile_collection.find_one({"user_id": user_id})
    if not user or not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_details = {
        "user_id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user["phone"],
        "profile_picture": str(profile["profile_picture"])
    }
    return user_details
