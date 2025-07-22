from aiogram.filters.callback_data import CallbackData


class SignUpCallback(CallbackData, prefix='signup'):
    message_id: str
    action: str


class PaymentCallback(CallbackData, prefix='payment'):
    message_id: str
    action: str
