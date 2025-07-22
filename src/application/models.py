from __future__ import annotations

import contextlib
import logging

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import TypeAlias

logger = logging.getLogger(__name__)


UserTgId: TypeAlias = int


@dataclass(slots=True)
class UserDTO:
    id: int
    nickname: str | None = None
    phone: str | None = None
    name: str | None = None
    last_name: str | None = None

    def to_dict(
        self,
        exclude: set[str] | None = None,
        include: dict[str, Any] | None = None,
        exclude_none: bool = False,
        sign_up: bool = False,
    ) -> dict[str, Any]:
        """Create a dictionary representation of the model.

        exclude: set of model fields,
            which should be excluded from dictionary representation.
        include: set of model fields,
            which should be included into dictionary representation.
        """

        data: dict[str, Any] = asdict(self)
        if exclude:
            for key in exclude:
                with contextlib.suppress(KeyError):
                    del data[key]
        if exclude_none:
            for k, v in list(data.items()):
                if v is None:
                    data.pop(k, None)
        if sign_up:
            data['phone'] = str(data['phone'])
            data.pop('id')
            data.pop('nickname')

        if include:
            data.update(include)

        return data

    def reg_is_complete(self) -> bool:
        return (
            None
            in self.to_dict(
                exclude={
                    'nickname',
                }
            ).values()
        )
