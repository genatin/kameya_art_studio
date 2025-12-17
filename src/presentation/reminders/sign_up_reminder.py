import asyncio
import logging
import zoneinfo
from datetime import date, datetime, time, timedelta
from typing import Any

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from src.application.domen.models.activity_type import ActivityTypeFactory
from src.application.domen.text import RU
from src.config import get_config
from src.infrastracture.adapters.repositories.activities import ActivityRepository
from src.infrastracture.database.redis.repository import RedisRepository
from src.infrastracture.repository.users import UsersService
from src.presentation.message_sender import send_messages_to_user

logger = logging.getLogger(__name__)

_MINUTE = 60
_HOUR = _MINUTE * 60
_DAY = _HOUR * 24
_DAYS_14 = _DAY * 14


class SignUpReminder:
    REMINDER_KEY_PREFIX: str = 'signup:pending:'
    MAX_REMINDER_COUNT: int = 2
    zone_info: zoneinfo.ZoneInfo = get_config().zone_info

    def __init__(
        self,
        bot: Bot,
        redis_repository: RedisRepository,
        scheduler: AsyncIOScheduler,
        user_service: UsersService,
        act_repository: ActivityRepository,
    ) -> None:
        self.redis_repository = redis_repository
        self.bot = bot
        self._user_service = user_service
        self._act_repository = act_repository
        self.__scheduler = scheduler

    async def get_keys_by_pattern(self) -> list[str]:
        return [
            key.encode('utf-8')
            async for key in self.redis_repository.client.scan_iter(
                match=f'{self.REMINDER_KEY_PREFIX}*'
            )
        ]

    async def setup_reminders(self) -> None:
        keys = await self.get_keys_by_pattern()
        for key in keys:
            reminder_data = await self._get_reminder_data(key)
            if reminder_data:
                reminder_count = int(reminder_data['reminder_count'])
                user_id = reminder_data['user_id']
                if reminder_count < self.MAX_REMINDER_COUNT:
                    await self._schedule_reminder(user_id, reminder_data)
                else:
                    await self.delete_reminder(user_id)

    async def add_reminder(
        self,
        user_id: int,
        act_id: int,
    ) -> None:
        last_reminded = datetime.now(self.zone_info).timestamp()
        reminder_data = {
            'user_id': user_id,
            'reminder_count': 0,
            'last_reminded': last_reminded,
            'run_date': None,
            'act_id': act_id,
        }
        await self._schedule_reminder(
            user_id,
            reminder_data,
        )

    async def _schedule_reminder(self, user_id: int, reminder_data: dict | None) -> None:
        act_id = reminder_data.get('act_id')
        if not reminder_data or act_id is None:
            await self.delete_reminder(user_id)
            return
        current_count = int(reminder_data['reminder_count'])

        activity = await self._act_repository.get_activity_by_id(act_id)
        run_date = datetime.combine(
            activity.date_time.date(), activity.date_time.time(), self.zone_info
        ) - timedelta(days=1)
        if (
            current_count >= self.MAX_REMINDER_COUNT
            or (datetime.now(self.zone_info) - run_date).days > 1
        ):
            await self.delete_reminder(user_id)
            return None
        if datetime.now(self.zone_info) > run_date:
            current_count += 1
            run_date += timedelta(days=1, hours=-2)

        reminder_data['run_date'] = run_date

        job_key = self._generate_job_key(user_id)

        if self.__scheduler.get_job(job_key):
            logger.info('job for user to signup %s has already exists', user_id)
        else:
            self.__scheduler.add_job(
                self._process_reminder,
                trigger=DateTrigger(run_date=run_date),
                args=(user_id, current_count),
                id=job_key,
            )
            await asyncio.sleep(0.1)
            logger.info(
                'add sheduler job for %s with date %s',
                user_id,
                run_date,
            )

        reminder_key = self._get_reminder_key(user_id)
        await self._set_reminder_data(reminder_key, reminder_data)

    def _generate_job_key(self, user_id: int) -> str:
        return f'signup_reminder_{user_id}'

    async def _process_reminder(
        self,
        user_id: int,
        current_count: int,
    ) -> None:
        reminder_key = self._get_reminder_key(user_id)
        reminder_data = await self._get_reminder_data(reminder_key)

        if not reminder_data:
            return

        # Обновляем данные напоминания
        reminder_data['reminder_count'] = current_count + 1

        if current_count < self.MAX_REMINDER_COUNT:
            # Отправляем напоминание
            try:
                act_time = reminder_data['act_time'].strftime('%H:%M')
                topic = reminder_data['topic']
                act_type = ActivityTypeFactory.activity_human_readable['activity_type']
                match current_count:
                    case 0:
                        remind_messages = [
                            RU.sweet_remind,
                            (
                                f'Напоминаем Вам, что завтра в <u>{act_time}</u>'
                                f' состоится {act_type}'
                                f' на тему <b>{topic}</b>!'
                            ),
                        ]
                    case 1:
                        remind_messages = [
                            RU.sweet_remind,
                            (
                                f'Напоминаем Вам, что сегодня в <u>{act_time}</u>'
                                f' состоится {act_type}'
                                f' на тему <b>{topic}</b>!'
                            ),
                        ]

                user = await self._user_service.get_user(user_id)
                hello_user = f'Привет, {user.name}!\n'
                connect_us = (
                    f'<i>\nВозникли вопросы? Напишите нам {RU.kameya_tg_contact}</i>'
                )
                await send_messages_to_user(
                    self.bot, [hello_user, *remind_messages, connect_us], user_id
                )
                reminder_data['last_reminded'] = datetime.now(self.zone_info).timestamp()
            except Exception as exc:
                logger.error('Failed to send reminder to %s: %s', user_id, exc)

            await self._set_reminder_data(reminder_key, reminder_data)
            # Планируем следующее
            reminder_data['run_date'] = datetime.fromtimestamp(
                float(reminder_data.get('run_date')), self.zone_info
            ) + timedelta(days=1, hours=-2)
            await self._schedule_reminder(user_id, reminder_data)
        else:
            # Удаляем после последнего напоминания
            await self.delete_reminder(reminder_key)

    def _get_reminder_key(self, user_id: int) -> str:
        return f'{self.REMINDER_KEY_PREFIX}{user_id}'

    async def _get_reminder_data(self, key: str) -> dict[str, Any] | None:
        try:
            return await self.redis_repository.hgetall(key)
        except AttributeError:
            return None

    async def _set_reminder_data(self, key: str, data: dict[str, Any]) -> None:
        await self.redis_repository.hset(key, mapping=data, ex=_DAY * 3)

    async def delete_reminder(self, user_id: int) -> None:
        redis_key_reminder = f'{self.REMINDER_KEY_PREFIX}{user_id}'
        await self.redis_repository.delete(redis_key_reminder)
        logger.info('removed from redis %s', redis_key_reminder)
        job_key = self._generate_job_key(user_id)
        if self.__scheduler.get_job(job_key):
            self.__scheduler.remove_job(job_key)
            logger.info('removed from sheduler %s', job_key)
