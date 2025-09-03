import sqlite3
import hashlib

# Database connection
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        language TEXT,
        age INTEGER,
        role TEXT DEFAULT 'user',
        content_type_preference TEXT DEFAULT 'text'
    )
    """)
    conn.commit()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password, language, age, role="user", content_type="text"):
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password, language, age, role, content_type_preference) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, email, hash_password(password), language, age, role, content_type)
        )
        conn.commit()
        return True, "User registered successfully!"
    except sqlite3.IntegrityError:
        return False, "Email already registered"

def authenticate(email, password):
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        return None, "User not found"
    stored_password = row[3]
    if stored_password != hash_password(password):
        return None, "Invalid password"
    
    user = {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "language": row[4],
        "age": row[5],
        "role": row[6],
        "content_type": row[7]
    }
    return user, "Login successful"

def update_language(email, language):
    cursor.execute("UPDATE users SET language = ? WHERE email = ?", (language, email))
    conn.commit()
    return True, "Language updated successfully!"

def update_content_type(email, content_type):
    cursor.execute("UPDATE users SET content_type_preference = ? WHERE email = ?", (content_type, email))
    conn.commit()
    return True, "Content type updated successfully!"

def get_user_by_email(email):
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "language": row[4],
        "age": row[5],
        "role": row[6],
        "content_type": row[7]
    }
