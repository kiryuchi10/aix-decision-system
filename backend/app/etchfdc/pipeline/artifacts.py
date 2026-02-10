# backend/app/etchfdc/pipeline/artifacts.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


def _kind_from_suffix(p: Path) -> str:
    s = p.suffix.lower().lstrip(".")
    if s in ("png", "jpg", "jpeg"):
        return "png"
    if s == "csv":
        return "csv"
    return "json" if s == "json" else "file"


def list_step_artifacts(data_dir: Path, dataset_id: str, step: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List artifacts under data_dir/reports/figures and data_dir/processed for dataset_id.
    data_dir = backend/app/data. Returns path as "app/data/..." relative to backend root.
    """
    out: List[Dict[str, Any]] = []
    step_figures = data_dir / "reports" / "figures" / dataset_id
    step_processed = data_dir / "processed" / dataset_id
    for base in (step_figures, step_processed):
        if not base.exists():
            continue
        steps = [step] if step else [d.name for d in base.iterdir() if d.is_dir()]
        for s in steps:
            sub = base / s
            if not sub.exists() or not sub.is_dir():
                continue
            for p in sorted(sub.iterdir()):
                if p.is_dir():
                    continue
                try:
                    rel = p.relative_to(data_dir)
                    rel_str = "app/data/" + rel.as_posix().replace("\\", "/")
                except ValueError:
                    rel_str = str(p)
                out.append({
                    "type": _kind_from_suffix(p),
                    "name": p.name,
                    "path": rel_str,
                    "created_at": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                })
    return out
