#!/bin/bash

echo "🗄️  Setting up AiX Decision System Database..."

# Configuration
DB_NAME="${MYSQL_DATABASE:-aix_system}"
DB_USER="${MYSQL_USER:-root}"
DB_PASS="${MYSQL_PASSWORD:-password}"
DB_HOST="${MYSQL_HOST:-localhost}"
DB_PORT="${MYSQL_PORT:-3306}"

SEED_DIR="./app/data/seed"
SCHEMA_FILE="./schema.sql"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if MySQL client is available
if ! command -v mysql &> /dev/null; then
    print_error "MySQL client not found. Please install MySQL first."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "Python not found. Please install Python first."
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)

# Step 1: Create database
echo ""
echo "Step 1: Creating database..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
    echo "Please enter MySQL root password:"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
}
print_success "Database '$DB_NAME' created"

# Step 2: Run schema.sql
if [ -f "$SCHEMA_FILE" ]; then
    echo ""
    echo "Step 2: Running schema.sql..."
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$SCHEMA_FILE" 2>/dev/null || {
        echo "Please enter MySQL root password:"
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p "$DB_NAME" < "$SCHEMA_FILE"
    }
    print_success "Schema applied"
else
    print_warning "Schema file not found: $SCHEMA_FILE"
fi

# Step 3: Import seed CSV files
if [ -d "$SEED_DIR" ]; then
    echo ""
    echo "Step 3: Importing seed CSV files..."
    
    # Create Python script to import CSVs
    cat > /tmp/import_seeds.py << 'PYEOF'
import sys
import os
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, get_db
from app.models.seed import SeedCatalog, SourceType
from sqlalchemy.orm import Session

SEED_DIR = Path(__file__).parent.parent / "app" / "data" / "seed"

def import_csv_to_table(csv_path, table_name):
    """Import CSV to database table"""
    try:
        df = pd.read_csv(csv_path)
        
        # Clean datetime columns
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower() or 'ts' in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        # Import to database
        df.to_sql(table_name, con=engine, if_exists='replace', index=False, method='multi', chunksize=1000)
        print(f"✅ Imported {len(df)} rows from {csv_path.name} -> {table_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to import {csv_path.name}: {e}")
        return False

def register_seed_folders():
    """Register CSV files in seed_catalog"""
    db = next(get_db())
    registered = 0
    
    # Look for CSV files in seed directory
    for csv_file in SEED_DIR.glob("*.csv"):
        # Extract process type from filename (e.g., "etch_data.csv" -> "etch")
        process_type = csv_file.stem.split('_')[0] if '_' in csv_file.stem else 'general'
        
        # Check if already registered
        existing = db.query(SeedCatalog).filter(
            SeedCatalog.seed_path == csv_file.name
        ).first()
        
        if not existing:
            # Read CSV to get schema
            try:
                df = pd.read_csv(csv_file, nrows=5)  # Just read first 5 rows for schema
                schema = {
                    "process_type": process_type,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                    "row_count": len(pd.read_csv(csv_file))  # Full count
                }
                
                seed = SeedCatalog(
                    process_type=process_type,
                    seed_path=csv_file.name,
                    schema_json=str(schema),
                    source_type=SourceType.DATASET,
                    source_id=None
                )
                db.add(seed)
                registered += 1
            except Exception as e:
                print(f"⚠️  Could not register {csv_file.name}: {e}")
    
    db.commit()
    print(f"✅ Registered {registered} seed files in catalog")
    db.close()

if __name__ == "__main__":
    print(f"📁 Seed directory: {SEED_DIR}")
    
    # Import CSV files to tables
    csv_files = {
        "recipes": "recipes.csv",
        "sensor_data": "sensor_data_10000.csv",
        "alarms": "alarms.csv",
        "recommendations": "recommendations.csv",
        "workflow_events": "workflow_events.csv",
        "experiments": "experiments.csv",
        "kpi_hourly": "kpi_hourly.csv",
    }
    
    imported = 0
    for table_name, filename in csv_files.items():
        csv_path = SEED_DIR / filename
        if csv_path.exists():
            if import_csv_to_table(csv_path, table_name):
                imported += 1
        else:
            print(f"⚠️  File not found: {filename}")
    
    print(f"\n✅ Imported {imported}/{len(csv_files)} CSV files")
    
    # Register in seed catalog
    print("\n📋 Registering seed files in catalog...")
    register_seed_folders()
    
    print("\n🎉 Database setup complete!")
PYEOF

    # Run the import script
    cd "$(dirname "$0")/.." || exit 1
    $PYTHON_CMD /tmp/import_seeds.py
    
    if [ $? -eq 0 ]; then
        print_success "Seed files imported"
    else
        print_warning "Some seed files may not have been imported. Check the output above."
    fi
    
    # Cleanup
    rm -f /tmp/import_seeds.py
else
    print_warning "Seed directory not found: $SEED_DIR"
fi

# Step 4: Run Alembic migrations (if available)
if [ -d "alembic" ]; then
    echo ""
    echo "Step 4: Running Alembic migrations..."
    alembic upgrade head 2>/dev/null && print_success "Migrations applied" || print_warning "Alembic migrations failed or not configured"
fi

echo ""
print_success "Database setup complete!"
echo ""
echo "📊 Database: $DB_NAME"
echo "👤 User: $DB_USER"
echo "🌐 Host: $DB_HOST:$DB_PORT"
echo ""
echo "You can now start the backend server with:"
echo "  uvicorn app.main:app --reload"
