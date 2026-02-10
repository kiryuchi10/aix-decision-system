#!/usr/bin/env python3
"""
Register seed .mat files as Datasets so they appear in /datasets and Viz Automation.
- Copies app/data/seed/process_etch/*.mat → app/data/uploads/datasets/
- Creates Dataset records (user_id, filename, storage_path, stage=DRAFT, committed=False)

Run from backend directory:
  python scripts/import_seed_as_datasets.py

Optional: set SEED_DATASETS_USER_ID=1 (or your user id) in env.
Otherwise uses first user in DB.
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.dataset import Dataset
from app.models.user import User

SEED_DIR = backend_dir / "app" / "data" / "seed" / "process_etch"
UPLOAD_DIR = backend_dir / "app" / "data" / "uploads" / "datasets"
# storage_path format matches datasets router (relative to backend root)
UPLOAD_DIR_REL = "./app/data/uploads/datasets"


def get_user_id(db: Session) -> int:
    uid = os.environ.get("SEED_DATASETS_USER_ID")
    if uid is not None:
        try:
            return int(uid)
        except ValueError:
            pass
    user = db.query(User).first()
    if not user:
        raise SystemExit("No user in DB. Create a user (e.g. sign up) then run this script.")
    return user.id


def main():
    if not SEED_DIR.exists():
        print(f"[error] Seed dir not found: {SEED_DIR}")
        sys.exit(1)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    db: Session = SessionLocal()
    try:
        user_id = get_user_id(db)
        print(f"[*] Using user_id={user_id}")

        for p in sorted(SEED_DIR.glob("*.mat")):
            dst = UPLOAD_DIR / p.name
            if not dst.exists():
                dst.write_bytes(p.read_bytes())
                print(f"[copy] {p.name} -> {dst}")

            storage_path = f"{UPLOAD_DIR_REL}/{p.name}"
            exists = db.query(Dataset).filter(Dataset.storage_path == storage_path).first()
            if exists:
                print(f"[skip] already registered: {p.name} (id={exists.id})")
                continue

            ds = Dataset(
                user_id=user_id,
                filename=p.name,
                storage_path=storage_path,
                row_count=None,
                column_count=None,
                schema_json=None,
                stage="DRAFT",
                committed=False,
            )
            db.add(ds)
            db.commit()
            db.refresh(ds)
            print(f"[ok] registered dataset id={ds.id} file={ds.filename}")
    finally:
        db.close()

    print("[done] Go to Datasets → Preview → Commit, then Viz Automation → Run step.")


if __name__ == "__main__":
    main()
