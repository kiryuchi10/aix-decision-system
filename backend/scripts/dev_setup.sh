#!/bin/bash

echo "🚀 Setting up AiX Backend..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat > .env << EOF
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/aix_system
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
EOF
    fi
    echo "⚠️  Please update .env with your configuration"
fi

# Create directories
echo "Creating directories..."
mkdir -p app/data/uploads/papers
mkdir -p app/data/uploads/datasets
mkdir -p app/data/seed
mkdir -p app/data/models
mkdir -p app/templates

# Run migrations (if using Alembic)
if [ -d "alembic" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

echo "✅ Backend setup complete!"
echo "Start server with: uvicorn app.main:app --reload"
