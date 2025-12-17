from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.presentation.reminders.payment_reminder import PaymentReminder
from src.presentation.reminders.sign_up_reminder import SignUpReminder


class MainReminder:
    def __init__(
        self,
        scheduler: AsyncIOScheduler,
        payment_reminder: PaymentReminder,
        signup_reminder: SignUpReminder,
    ) -> None:
        self.payment_reminder = payment_reminder
        self.signup_reminder = signup_reminder
        self.__scheduler = scheduler

    async def start_reminders(self) -> None:
        self.__scheduler.start()
        await self.refresh_reminders()

    async def refresh_reminders(self) -> None:
        await self.signup_reminder.setup_reminders()
        await self.payment_reminder.setup_reminders()

    async def add_reminder(self, user_id: int, **kwargs) -> None:
        await self.payment_reminder.add_reminder(user_id, **kwargs)
        await self.signup_reminder.add_reminder(user_id, **kwargs)

    async def delete_reminder(self, user_id: int) -> None:
        await self.payment_reminder.delete_reminder(user_id)
        await self.signup_reminder.delete_reminder(user_id)
