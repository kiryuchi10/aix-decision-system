# backend/app/etchfdc/pipeline/context.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineContext:
    dataset_id: str
    base_dir: Path  # backend/app/data

    @property
    def processed_dir(self) -> Path:
        return self.base_dir / "processed" / self.dataset_id

    @property
    def figures_dir(self) -> Path:
        return self.base_dir / "reports" / "figures" / self.dataset_id

    def step_processed_dir(self, step: str) -> Path:
        d = self.processed_dir / step
        d.mkdir(parents=True, exist_ok=True)
        return d

    def step_figures_dir(self, step: str) -> Path:
        d = self.figures_dir / step
        d.mkdir(parents=True, exist_ok=True)
        return d
