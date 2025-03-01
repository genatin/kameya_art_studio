from collections import OrderedDict
from typing import Any, Iterator, MutableMapping, TypeVar

from src.application.in_memory.interfaces import InMemoryUsersAbstractRepository
from src.application.models import UserDTO, UserTgId

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class LRUDict(MutableMapping[_KT, _VT]):
    def __init__(self, maxsize: int, items: dict[str, Any] | None = None) -> None:  # type: ignore[misc]
        self._maxsize = maxsize
        self.d: OrderedDict[str, Any] = OrderedDict()  # type: ignore[misc]
        if items:
            for k, v in items:  # type: ignore[misc]
                self[k] = v  # type: ignore[has-type]

    @property
    def maxsize(self) -> int:
        return self._maxsize

    def __getitem__(self, key: Any) -> Any:  # type: ignore[misc]
        self.d.move_to_end(key)
        return self.d[key]

    def __setitem__(self, key: Any, value: Any) -> None:  # type: ignore[misc]
        if key in self.d:
            self.d.move_to_end(key)
        elif len(self.d) == self._maxsize:
            self.d.popitem(last=False)
        self.d[key] = value

    def __delitem__(self, key: Any) -> None:  # type: ignore[misc]
        del self.d[key]

    def __iter__(self) -> Iterator[Any]:  # type: ignore[misc]
        return self.d.__iter__()

    def __len__(self) -> int:
        return len(self.d)


class InMemoryUsers(InMemoryUsersAbstractRepository):
    def __init__(self):
        self.__cached_users: LRUDict[UserTgId, UserDTO] = LRUDict(maxsize=1000)

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
