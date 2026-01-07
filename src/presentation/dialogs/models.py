from pydantic import BaseModel


class SignUpCallbackFactory(BaseModel):
    act_id: int
    message_id: str
    user_id: int
    user_phone: str
    num_row: str
    message: str
    cost: int | str = ''
