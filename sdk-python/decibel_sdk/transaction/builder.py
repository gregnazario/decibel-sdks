"""Transaction payload construction for Move entry function calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransactionPayload:
    """Represents a Move entry function call payload."""

    function: str
    type_arguments: list[str] = field(default_factory=list)
    arguments: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "function": self.function,
            "type_arguments": self.type_arguments,
            "arguments": self.arguments,
        }
