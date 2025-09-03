from fastapi import FastAPI, Body, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import bcrypt

from backend.db import get_conn

# ---------------------------
# Load env
# ---------------------------
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(title="Text Summarisation Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = HTTPBearer()

# ---------------------------
# JWT Helpers
# ---------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: dict = Depends(oauth2_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def home():
    return {"message": "Backend is running!"}

@app.post("/register")
def register_user(data: dict = Body(...)):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (data["email"],))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash password
        password_hash = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert new user
        sql = """
        INSERT INTO users (username, email, password_hash, age, language_preference, role, content_type, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data["username"],
            data["email"],
            password_hash,
            data.get("age", 20),
            data.get("language", "en"),
            data.get("role", "user"),
            data.get("content_type", "text"),
            datetime.now()
        )
        cursor.execute(sql, values)
        conn.commit()

        # Get inserted user
        user_id = cursor.lastrowid

        # Generate JWT
        access_token = create_access_token(data={"sub": data["email"], "role": data.get("role","user")})

        # Return full user object
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": data["username"],
                "email": data["email"],
                "age": data.get("age", 20),
                "role": data.get("role", "user"),
                "content_type": data.get("content_type", "text")
            }
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/login")
def login_user(data: dict = Body(...)):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (data["email"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not bcrypt.checkpw(data["password"].encode('utf-8'), user["password_hash"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid password")

        access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "age": user["age"],
                "role": user["role"],
                "content_type": user["content_type"]
            }
        }
    finally:
        cursor.close()
        conn.close()

@app.put("/update-language")
def update_language(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET language_preference=%s WHERE email=%s", (data["language"], current_user["sub"]))
        conn.commit()
        return {"detail": "Language updated!"}
    finally:
        cursor.close()
        conn.close()

@app.put("/update-content-type")
def update_content_type(data: dict = Body(...), current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET content_type=%s WHERE email=%s", (data["content_type"], current_user["sub"]))
        conn.commit()
        return {"detail": "Content type updated!"}
    finally:
        cursor.close()
        conn.close()

@app.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id AS id, username, email, age, role, content_type FROM users WHERE email=%s", (current_user["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user": user}
    finally:
        cursor.close()
        conn.close()
