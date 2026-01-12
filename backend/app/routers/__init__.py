# app/routers/__init__.py

from .auth import router as auth_router
from .papers import router as papers_router
from .datasets import router as datasets_router
from .seeds import router as seeds_router
from .generator import router as generator_router
from .chat import router as chat_router

# === Experimental / future routers ===
# 아래 파일들이 실제로 생기기 전까지는 import 하지 마세요
# from .kpi import router as kpi_router
# from .workflow import router as workflow_router
# from .fdc import router as fdc_router
# from .doe import router as doe_router
# from .coupling import router as coupling_router
