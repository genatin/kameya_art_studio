import string

from pydantic import BaseModel


class UserDTO(BaseModel):
    id: int
    nickname: str | None = None
    phone: str | int | None = None
    name: str | None = None
    last_name: str | None = None

    def compile_batch(self, row_id: int):
        batch = []
        for i, field in zip(string.ascii_lowercase, self.__fields__.keys()):
            value = getattr(self, field)
            if value is not None:
                batch.append({"range": f"{i}{row_id}", "values": [[value]]})
        return batch
