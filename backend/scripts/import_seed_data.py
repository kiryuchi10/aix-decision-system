#!/usr/bin/env python3
"""
Import seed CSV files into database and register them in seed_catalog.
Run from backend directory: python scripts/import_seed_data.py
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import engine, get_db
from app.models.seed import SeedCatalog, SourceType
from sqlalchemy.orm import Session

SEED_DIR = backend_dir / "app" / "data" / "seed"

def import_csv_to_table(csv_path: Path, table_name: str) -> bool:
    """Import CSV to database table"""
    try:
        print(f"📥 Reading {csv_path.name}...")
        df = pd.read_csv(csv_path)
        
        # Clean datetime columns
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'ts', 'created', 'updated']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        # Import to database
        print(f"💾 Importing {len(df)} rows to table '{table_name}'...")
        df.to_sql(
            table_name, 
            con=engine, 
            if_exists='replace', 
            index=False, 
            method='multi', 
            chunksize=1000
        )
        print(f"✅ Imported {len(df)} rows from {csv_path.name} -> {table_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to import {csv_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def register_seed_folders():
    """Register CSV files in seed_catalog"""
    db: Session = next(get_db())
    registered = 0
    
    print("\n📋 Registering seed files in catalog...")
    
    # Look for CSV files in seed directory
    for csv_file in SEED_DIR.glob("*.csv"):
        # Extract process type from filename (e.g., "etch_data.csv" -> "etch")
        filename = csv_file.stem
        if '_' in filename:
            process_type = filename.split('_')[0]
        elif filename.startswith('sensor'):
            process_type = 'sensor'
        elif filename.startswith('recipe'):
            process_type = 'recipe'
        else:
            process_type = 'general'
        
        # Check if already registered
        existing = db.query(SeedCatalog).filter(
            SeedCatalog.seed_path == csv_file.name
        ).first()
        
        if existing:
            print(f"⏭️  Already registered: {csv_file.name}")
            continue
        
        # Read CSV to get schema
        try:
            df_sample = pd.read_csv(csv_file, nrows=5)  # Just read first 5 rows for schema
            df_full = pd.read_csv(csv_file)  # Full count
            
            schema = {
                "process_type": process_type,
                "columns": df_sample.columns.tolist(),
                "dtypes": df_sample.dtypes.astype(str).to_dict(),
                "row_count": len(df_full)
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
            print(f"✅ Registered: {csv_file.name} (process_type: {process_type}, rows: {len(df_full)})")
        except Exception as e:
            print(f"⚠️  Could not register {csv_file.name}: {e}")
    
    db.commit()
    print(f"\n✅ Registered {registered} new seed files in catalog")
    db.close()

def main():
    print("🚀 Starting seed data import...")
    print(f"📁 Seed directory: {SEED_DIR}")
    
    if not SEED_DIR.exists():
        print(f"❌ Seed directory not found: {SEED_DIR}")
        return
    
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
    
    print("\n📊 Step 1: Importing CSV files to database tables...")
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
    print("\n📋 Step 2: Registering seed files in catalog...")
    register_seed_folders()
    
    print("\n🎉 Seed data import complete!")

if __name__ == "__main__":
    main()
