#!/usr/bin/env python3
"""
Test script to verify auth endpoints and database connection
Run: python test_auth.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, get_db
from app.models.user import User, UserRole
from app.routers.auth import get_password_hash, verify_password
from sqlalchemy.orm import Session

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure MySQL is running and DATABASE_URL is correct in .env")
        return False

def test_user_operations():
    """Test user creation and retrieval"""
    print("\n🔍 Testing user operations...")
    try:
        db: Session = next(get_db())
        
        # Test creating a user
        test_email = "test@aix.com"
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()
        
        user = User(
            email=test_email,
            password_hash=get_password_hash("test123"),
            full_name="Test User",
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created user: {user.email} (ID: {user.id})")
        
        # Test password verification
        if verify_password("test123", user.password_hash):
            print("✅ Password verification works!")
        else:
            print("❌ Password verification failed!")
        
        # Test retrieving user
        found = db.query(User).filter(User.email == test_email).first()
        if found:
            print(f"✅ User retrieval works! Found: {found.email}")
        else:
            print("❌ User retrieval failed!")
        
        # Cleanup
        db.delete(user)
        db.commit()
        print("✅ Test user cleaned up")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ User operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_demo_user():
    """Test demo user creation"""
    print("\n🔍 Testing demo user...")
    try:
        db: Session = next(get_db())
        
        demo_email = "demo@aix.com"
        user = db.query(User).filter(User.email == demo_email).first()
        
        if user:
            print(f"✅ Demo user exists: {user.email} (Role: {user.role.value})")
        else:
            print("⚠️  Demo user doesn't exist yet (will be created on first demo-login)")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Demo user test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Auth System\n")
    
    db_ok = test_database_connection()
    if not db_ok:
        print("\n❌ Cannot continue without database connection")
        sys.exit(1)
    
    user_ok = test_user_operations()
    demo_ok = test_demo_user()
    
    print("\n" + "="*50)
    if db_ok and user_ok and demo_ok:
        print("✅ All tests passed!")
        print("\n💡 You can now:")
        print("   1. Start server: uvicorn app.main:app --reload")
        print("   2. Test demo login: POST http://localhost:8000/api/v1/auth/demo-login")
        print("   3. Test signup: POST http://localhost:8000/api/v1/auth/signup")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)
