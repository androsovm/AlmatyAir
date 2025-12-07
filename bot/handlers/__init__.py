from aiogram import Router

from .start import router as start_router
from .callbacks import router as callbacks_router

def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(callbacks_router)
    return router

__all__ = ["setup_routers"]
