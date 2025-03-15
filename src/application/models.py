from __future__ import annotations

import logging
import string
from dataclasses import asdict, dataclass
from typing import Any, TypeAlias

logger = logging.getLogger(__name__)


UserTgId: TypeAlias = int


@dataclass(slots=True)
class UserDTO:
    id: int
    nickname: str | None = None
    phone: str | None = None
    name: str | None = None
    last_name: str | None = None
    role: str | None = None

    def to_dict(
        self,
        exclude: set[str] | None = None,
        include: dict[str, Any] | None = None,
        exclude_none: bool = False,
        sign_up: bool = False,
    ) -> dict[str, Any]:
        """
        Create a dictionary representation of the model.

        exclude: set of model fields, which should be excluded from dictionary representation.
        include: set of model fields, which should be included into dictionary representation.
        """

        data: dict[str, Any] = asdict(self)
        if exclude:
            for key in exclude:
                try:
                    del data[key]
                except KeyError:
                    pass
        if exclude_none:
            for k, v in list(data.items()):
                if v is None:
                    data.pop(k, None)
        if sign_up:
            data["phone"] = str(data["phone"])
            data.pop("id")
            data.pop("nickname")
            data.pop("role")

        if include:
            data.update(include)

        return data

    def compile_batch(self, row_id: int):
        batch = []
        for i, field in zip(string.ascii_lowercase, self.__annotations__.keys()):
            value = getattr(self, field)
            if value is not None:
                batch.append({"range": f"{i}{row_id}", "values": [[value]]})
        return batch

    @classmethod
    def parse_from_row(cls, values: list[str]) -> UserDTO:
        user_data = {}
        for k, v in zip(cls.__annotations__.keys(), values):
            if v:
                user_data[k] = v
        return UserDTO(**user_data)
