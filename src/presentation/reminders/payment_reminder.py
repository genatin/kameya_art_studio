import asyncio
import logging
import zoneinfo
from datetime import datetime, timedelta
from typing import Any

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from src.application.domen.text import RU
from src.config import get_config
from src.infrastracture.database.redis.repository import RedisRepository

logger = logging.getLogger(__name__)

_MINUTE = 60
_HOUR = _MINUTE * 60
_DAY = _HOUR * 24
_DAYS_14 = _DAY * 14


class PaymentReminder:
    REMINDER_KEY_PREFIX: str = 'payment:pending:'
    MAX_REMINDER_COUNT: int = 3
    zone_info: zoneinfo.ZoneInfo = get_config().zone_info

    def __init__(self, bot: Bot, redis_repository: RedisRepository) -> None:
        self.redis_repository = redis_repository
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    async def get_keys_by_pattern(self) -> list[str]:
        return [
            key.encode('utf-8')
            async for key in self.redis_repository.client.scan_iter(
                match=f'{self.REMINDER_KEY_PREFIX}*'
            )
        ]

    async def start(self) -> None:
        self.scheduler.start()
        await self.setup_reminders()

    async def setup_reminders(self) -> None:
        keys = await self.get_keys_by_pattern()
        for key in keys:
            reminder_data = await self._get_reminder_data(key)
            if reminder_data:
                reminder_count = int(reminder_data['reminder_count'])
                if reminder_count < self.MAX_REMINDER_COUNT:
                    await self._schedule_reminder(reminder_data['user_id'], reminder_data)
                else:
                    await self.delete_payment(reminder_data['user_id'])

    async def add_reminder(self, user_id: int) -> None:
        last_reminded = datetime.now(self.zone_info).timestamp()
        reminder_data = {
            'user_id': user_id,
            'reminder_count': 0,
            'last_reminded': last_reminded,
            'run_date': None,
        }
        await self._schedule_reminder(
            user_id,
            reminder_data,
        )

    async def _schedule_reminder(self, user_id: int, reminder_data: dict) -> None:
        last_reminded = reminder_data['last_reminded']
        if last_reminded:
            last_reminded_date = datetime.fromtimestamp(
                float(last_reminded), self.zone_info
            )
        else:
            last_reminded_date = datetime.now(self.zone_info)
            reminder_data['last_reminded'] = last_reminded_date

        run_date = reminder_data.get('run_date')
        current_count = int(reminder_data['reminder_count'])
        if run_date:
            run_date = datetime.fromtimestamp(float(run_date), self.zone_info)
            if datetime.now(self.zone_info) > run_date:
                run_date = self.adjust_to_work_hours(datetime.now(self.zone_info))
        else:
            run_date = self.calculate_next_notification_time(
                last_reminded_date, current_count
            )
            reminder_data['run_date'] = run_date.timestamp()
        if current_count >= self.MAX_REMINDER_COUNT:
            return None

        job_key = self.get_job_key(user_id)

        if self.scheduler.get_job(job_key):
            logger.info('job for user %s has already exists', user_id)
        else:
            self.scheduler.add_job(
                self._process_reminder,
                trigger=DateTrigger(run_date=run_date),
                args=(user_id, current_count),
                id=job_key,
            )
            await asyncio.sleep(0.3)
            logger.info(
                'add sheduler job for %s with date %s and count=%s',
                user_id,
                run_date,
                current_count,
            )

        reminder_key = self._get_reminder_key(user_id)
        await self._set_reminder_data(reminder_key, reminder_data)

    def adjust_to_work_hours(self, time: datetime) -> datetime:
        if time.hour >= 20:
            next_day = time.date() + timedelta(days=1)
        elif time.hour < 9:
            next_day = time.date()
        else:
            return time
        return datetime.combine(
            next_day, datetime.min.time(), tzinfo=self.zone_info
        ).replace(hour=9)

    def calculate_next_notification_time(
        self, last_sent_time: datetime, attempt_number: int
    ) -> datetime:
        if (datetime.now(self.zone_info) - last_sent_time).total_seconds() / 60 > 1:
            return self.adjust_to_work_hours(datetime.now(self.zone_info))

        delta_hours = (attempt_number + 1) * 4

        next_time = last_sent_time + timedelta(hours=delta_hours)

        # Корректируем время с учетом рабочего времени
        adjusted_time = self.adjust_to_work_hours(next_time)

        # Если корректировка привела к переносу на следующий день,
        # проверяем не попадает ли новое время снова на нерабочее время
        if adjusted_time != next_time:
            adjusted_time = self.adjust_to_work_hours(adjusted_time)

        return adjusted_time

    def get_job_key(self, user_id: int) -> str:
        return f'reminder_{user_id}'

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
                match current_count:
                    case 0:
                        message = RU.payment_reminder_1
                    case 1:
                        message = RU.payment_reminder_2
                    case 2:
                        message = RU.payment_reminder_3

                connect_us = (
                    f'<i>\nВозникли вопросы? Напишите нам {RU.kameya_tg_contact}</i>'
                )
                await self.bot.send_message(
                    user_id, message + connect_us, parse_mode=ParseMode.HTML
                )
                reminder_data['last_reminded'] = datetime.now(self.zone_info).timestamp()
            except Exception as exc:
                logger.error('Failed to send reminder to %s: %s', user_id, exc)

            # Проверяем нужно ли продолжать напоминания
            await self._set_reminder_data(reminder_key, reminder_data)

            # Планируем следующее
            reminder_data['run_date'] = None
            await self._schedule_reminder(user_id, reminder_data)
        else:
            # Удаляем после последнего напоминания
            await self.delete_payment(reminder_key)

    def _get_reminder_key(self, user_id: int) -> str:
        return f'{self.REMINDER_KEY_PREFIX}{user_id}'

    async def _get_reminder_data(self, key: str) -> dict[str, Any] | None:
        try:
            return await self.redis_repository.hgetall(key)
        except AttributeError:
            return None

    async def _set_reminder_data(self, key: str, data: dict[str, Any]) -> None:
        await self.redis_repository.hset(key, mapping=data, ex=_DAY * 3)

    async def delete_payment(self, user_id: int) -> None:
        redis_key_reminder = f'{self.REMINDER_KEY_PREFIX}{user_id}'
        await self.redis_repository.delete(redis_key_reminder)
        logger.info('removed from redis %s', redis_key_reminder)
        job_key = self.get_job_key(user_id)
        if self.scheduler.get_job(job_key):
            self.scheduler.remove_job(job_key)
            logger.info('removed from sheduler %s', job_key)
