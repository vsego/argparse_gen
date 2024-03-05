"""
Utility functions for the rest of the package.
"""

import enum
import textwrap
from typing import Type


class EnumType:
    """
    Wrapper class to use for representation of `enum.Enum` parameter's type.
    """

    def __init__(self, param_type: Type[enum.Enum]) -> None:
        self.param_type = param_type

    @property
    def __name__(self) -> str:
        """
        Return string to be used in :py:meth:`ArgumentParser.add_argument`.
        """
        return f"lambda value: getattr({self.param_type.__name__}, value)"


class EnumValue:
    """
    Wrapper class to use for representation of `enum.Enum` parameter's value.
    """

    def __init__(self, value: enum.Enum) -> None:
        self.value = value

    def __repr__(self) -> str:
        """
        Return string to be used in :py:meth:`ArgumentParser.add_argument`.
        """
        return f"{self.value.__class__.__name__}.{self.value.name}"


def str_as_arg(name: str, value: str, max_width: int = 72) -> str:
    """
    Return `f"{name}={value}"` properly capped at `max_width` width.
    """
    lead_size = len(name) + 1
    if lead_size + len(value) + 1 > max_width:
        quote = value[0]
        if not value.endswith(quote):
            raise ValueError(f"non-repr string {value!r}")
        value = value[1:-1]
        lead_size += max(0, 4 - len(name))
        return (
            "\n".join(
                [
                    f"        {quote} {line}{quote}"
                    if line_idx else
                    f"{name}=(\n        {quote}{line}{quote}"
                    for line_idx, line in enumerate(
                        textwrap.wrap(
                            value,
                            max_width - lead_size - 4,
                            break_long_words=False,
                            break_on_hyphens=False,
                        ),
                    )
                ],
            )
            + "\n    )"
        )
    else:
        return f"{name}={value}"
