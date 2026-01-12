#!/bin/bash

echo "🗄️  Setting up MySQL Database..."

DB_NAME="aix_system"
DB_USER="${MYSQL_USER:-root}"
DB_PASS="${MYSQL_PASSWORD:-password}"

# Check if MySQL is available
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL client not found. Please install MySQL first."
    exit 1
fi

# Create database
echo "Creating database '$DB_NAME'..."
mysql -u "$DB_USER" -p"$DB_PASS" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
    echo "Please enter MySQL root password:"
    mysql -u "$DB_USER" -p -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
}

echo "✅ Database '$DB_NAME' created"

# Run schema.sql if exists
if [ -f "schema.sql" ]; then
    echo "Running schema.sql..."
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < schema.sql 2>/dev/null || {
        echo "Please enter MySQL root password:"
        mysql -u "$DB_USER" -p "$DB_NAME" < schema.sql
    }
    echo "✅ Database schema applied"
fi

# Run Alembic migrations if available
if [ -d "alembic" ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head
    echo "✅ Migrations applied"
fi

echo "🎉 MySQL setup complete!"
