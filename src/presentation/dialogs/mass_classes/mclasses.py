import logging
from typing import Any

from aiogram.types import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll

from src.infrastracture.database.sqlite import get_all_mclasses

logger = logging.getLogger(__name__)


async def get_mclasses_page(dialog_manager: DialogManager, **_kwargs):
    scroll: ManagedScroll = dialog_manager.find("scroll")
    media_number = await scroll.get_page()
    mclasses = dialog_manager.dialog_data.get("mclasses", [])
    if not mclasses:
        mclasses = dialog_manager.start_data.get("mclasses", [])
        dialog_manager.dialog_data["mclasses"] = mclasses
    l_mclasses = len(mclasses)
    mclass = mclasses[media_number]
    dialog_manager.dialog_data["mclass"] = mclass
    image = None
    if mclass["file_id"]:
        image = MediaAttachment(
            file_id=MediaId(mclass["file_id"]),
            type=ContentType.PHOTO,
        )
    return {
        "media_number": media_number,
        "next_p": (l_mclasses - media_number) > 1,
        "mc_count": l_mclasses,
        "mclass": mclass,
        "image": image,
    }


async def store_mclasses(start_data: Any, manager: DialogManager):
    mclasses = [
        {
            "id": mclass.id,
            "name": mclass.name,
            "description": mclass.description,
            "file_id": mclass.file_id,
        }
        for mclass in await get_all_mclasses()
    ]
    manager.dialog_data["mclasses"] = mclasses
