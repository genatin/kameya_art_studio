from __future__ import annotations

import logging
import threading

import cachetools.func

from src.infrastracture.adapters.repositories.gspread_storage import gspread_storage

logger = logging.getLogger(__name__)

_TTL_HOUR_2 = 60 * 60 * 2


class DataCache:

    @classmethod
    @cachetools.func.ttl_cache(ttl=_TTL_HOUR_2)
    def lessons(cls):
        return {"description": gspread_storage.lessons()}
