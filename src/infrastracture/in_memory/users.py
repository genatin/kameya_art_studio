from collections import OrderedDict
from copy import copy
from typing import Iterator, MutableMapping, TypeVar

from src.application.in_memory.interfaces import InMemoryUsersAbstractRepository
from src.application.models import UserDTO, UserTgId

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")

import logging

logger = logging.getLogger(__name__)


class LimitedSizeDict(OrderedDict, MutableMapping[_KT, _VT]):
    def __init__(self, *args, **kwds):
        self.size_limit = kwds.pop("size_limit", None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem(last=False)


class InMemoryUsers(InMemoryUsersAbstractRepository):
    def __init__(self):
        self.__cached_users: LimitedSizeDict[UserTgId, UserDTO] = LimitedSizeDict(
            size_limit=1000
        )

    def get_user(self, user_id: UserTgId) -> UserDTO | None:
        return self.__cached_users.get(user_id)

    def remove_user(self, user_id: UserTgId) -> None:
        self.__cached_users.pop(user_id, None)

    def update_cache(self, user: dict[UserTgId, UserDTO] | UserDTO) -> None:
        if isinstance(user, UserDTO):
            self.__cached_users[user.id] = user
        elif isinstance(user, dict):
            self.__cached_users.update(user)
        else:
            raise NotImplementedError

    def get_admins(self) -> Iterator[UserDTO]:
        for user in self.__cached_users.values():
            if user.id and user.role == "admin":
                yield user
