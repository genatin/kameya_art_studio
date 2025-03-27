import logging
from typing import Any

from aiogram.types import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll

from src.application.domen.models import LessonActivity
from src.infrastracture.database.sqlite import get_all_activity_by_type

logger = logging.getLogger(__name__)
FILE_ID = "file_id"


async def get_activity_page(dialog_manager: DialogManager, **_kwargs):
    scroll: ManagedScroll | None = dialog_manager.find("scroll")
    media_number = await scroll.get_page() if scroll else 0
    activities = dialog_manager.dialog_data.get("activities", [])
    len_activities = len(activities)
    if not activities:
        return {FILE_ID: None, "activity": None, "media_number": 0, "len_activities": 0}
    activity = activities[media_number]
    dialog_manager.dialog_data["activity"] = activity
    image = None
    if activity[FILE_ID]:
        image = MediaAttachment(
            file_id=MediaId(activity[FILE_ID]),
            type=ContentType.PHOTO,
        )
    return {
        "media_number": media_number,
        "next_p": (len_activities - media_number) > 1,
        "len_activities": len_activities,
        "activity": activity,
        FILE_ID: image,
    }


async def store_activities_by_type(start_data: Any, manager: DialogManager):
    # function passed getter on start dialog
    # you can pass ActivityType
    act_type = None
    if start_data:
        if isinstance(start_data, dict):
            la: LessonActivity | None = start_data.get("lesson_activity")
            if la:
                act_type = la.activity_type
        if not act_type:
            act_type = start_data.get("act_type")

    activities = [
        {
            "id": activity.id,
            "theme": activity.theme,
            "description": activity.description,
            FILE_ID: activity.file_id,
        }
        for activity in await get_all_activity_by_type(
            activity_type=act_type.human_name
        )
    ]
    manager.dialog_data["act_type"] = act_type.human_name
    manager.dialog_data["activities"] = activities
