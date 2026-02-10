#!/usr/bin/env python3
"""
Create a default user so you can log in without signing up.
Email: admin@aix.com  Password: admin123

Run from backend directory:
  python scripts/create_default_user.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.routers.auth import get_password_hash

DEFAULT_EMAIL = "admin@aix.com"
DEFAULT_PASSWORD = "admin123"


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEFAULT_EMAIL).first()
        if user:
            print(f"[skip] User already exists: {DEFAULT_EMAIL} (id={user.id})")
            return
        user = User(
            email=DEFAULT_EMAIL,
            password_hash=get_password_hash(DEFAULT_PASSWORD),
            full_name="Admin",
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[ok] Created user id={user.id} email={DEFAULT_EMAIL} password={DEFAULT_PASSWORD}")
        print("     You can now log in on the login page.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
