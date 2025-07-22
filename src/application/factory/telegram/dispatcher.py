from aiogram import Dispatcher


def create_dispatcher(storage, **handlers) -> Dispatcher:
    """:return: Configured ``Dispatcher``"""
    dispatcher = Dispatcher(storage=storage, **handlers)
    return dispatcher
