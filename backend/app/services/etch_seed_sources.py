# Etch seed data source enum and path resolution for MACHINE/OES/RFM .mat files
from enum import Enum
from pathlib import Path


class EtchSeedSource(str, Enum):
    MACHINE = "MACHINE"
    OES = "OES"
    RFM = "RFM"


def resolve_mat_path(seed_dir: Path, source: EtchSeedSource) -> Path:
    # seed_dir e.g. backend/app/data/seed/process_etch
    mapping = {
        EtchSeedSource.MACHINE: "MACHINE_Data.mat",
        EtchSeedSource.OES: "OES_DATA.mat",
        EtchSeedSource.RFM: "RFM_DATA.mat",
    }
    return seed_dir / mapping[source]
