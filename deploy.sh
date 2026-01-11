#!/bin/bash

# AiX Decision System - Production Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 AiX Decision System - Production Deployment"
echo "Environment: $ENVIRONMENT"
echo "Compose file: $COMPOSE_FILE"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.prod to .env and configure it."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models logs ml_experiments ssl monitoring/grafana/{dashboards,datasources}

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Build custom images
echo "🔨 Building custom images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Start services
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🏥 Performing health checks..."

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -f $COMPOSE_FILE logs backend
    exit 1
fi

# Check frontend
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose -f $COMPOSE_FILE logs frontend
    exit 1
fi

# Check database
if docker-compose -f $COMPOSE_FILE exec -T mysql mysqladmin ping -h localhost > /dev/null 2>&1; then
    echo "✅ Database is healthy"
else
    echo "❌ Database health check failed"
    docker-compose -f $COMPOSE_FILE logs mysql
    exit 1
fi

# Initialize database (if needed)
echo "🗄️ Initializing database..."
docker-compose -f $COMPOSE_FILE exec -T backend python -c "
from app.core.database import engine, Base
from app.models.experiment import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

# Show running services
echo "📊 Running services:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📱 Access URLs:"
echo "   Frontend:    http://localhost"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo "   Grafana:     http://localhost:3000"
echo "   Prometheus:  http://localhost:9090"
echo ""
echo "📋 Next steps:"
echo "   1. Configure SSL certificates (if using HTTPS)"
echo "   2. Set up monitoring alerts"
echo "   3. Configure backup schedules"
echo "   4. Review security settings"
echo ""
echo "📖 For more information, see: README.md"