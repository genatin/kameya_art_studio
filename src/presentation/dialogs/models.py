from pydantic import BaseModel


class SignUpCallbackFactory(BaseModel):
    message_id: str
    user_id: int
    user_phone: str
    activity_type: str
    num_row: str
    message: str
    cost: int | str = ''
