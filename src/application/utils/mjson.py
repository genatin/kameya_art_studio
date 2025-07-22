import logging

from collections.abc import Callable
from typing import Any
from typing import Final

from msgspec.json import Decoder
from msgspec.json import Encoder
from pydantic import BaseModel


def pydantic_hook(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump(exclude_defaults=True)
    return str(obj)


decode: Final[Callable[..., Any]] = Decoder[dict[str, Any]]().decode
bytes_encode: Final[Callable[..., bytes]] = Encoder(enc_hook=pydantic_hook).encode

logger = logging.getLogger(__name__)


def encode(obj: Any) -> str:
    data: bytes = bytes_encode(obj)
    return data.decode()
