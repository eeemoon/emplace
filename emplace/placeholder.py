import inspect
import re
from typing import Callable


class Placeholder:
    """Placeholder handler."""

    def __init__(
        self, 
        pattern: str | re.Pattern | None, 
        handler: Callable
    ) -> None:
        """
        Parameters
        ----------
        pattern: `str` | `Pattern` | `None`
            Regex pattern to match placeholder. If `None`, match any string.
        handler: `Callable`
            Function that processes placeholder.
        """
        self.pattern = pattern
        self.handler = handler

        if self.pattern:
            Placeholder._validate_handler(self.handler, self.pattern)

    @classmethod
    def _validate_handler(
        cls, 
        handler: Callable, 
        pattern: re.Pattern
    ) -> None:
        signature = inspect.signature(handler)
        for group_name in pattern.groupindex.keys():
            param = signature.parameters.get(group_name)

            if not param:
                raise ValueError(f"handler must handle '{group_name}' parameter")
            if param.kind not in {
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            }:
                raise ValueError(
                    f"parameter '{param.name}' should be either positional or keyword"
                )

    def __repr__(self) -> str:
        return (
            f"<Placeholder pattern='{self.pattern.pattern if self.pattern else None}',"
            f" handler={self.handler.__qualname__}>"
        )

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Placeholder)
            and self.pattern == value.pattern
            and self.handler == value.handler
        )

    @property
    def pattern(self) -> re.Pattern | None:
        """Regex pattern to match placeholder."""
        return self._pattern
    
    @pattern.setter
    def pattern(self, value: str | re.Pattern | None) -> None:
        if isinstance(value, str):
            self._pattern = re.compile(value)
        elif isinstance(value, re.Pattern) or value is None:
            self._pattern = value
        else:
            raise TypeError(f"expected 'str', 'Pattern' or 'None', not '{type(value)}'")

    @property
    def handler(self) -> Callable:
        """Function that processes placeholder."""
        return self._handler

    @handler.setter
    def handler(self, value: Callable) -> None:
        if not callable(value):
            raise ValueError("handler is not callable")
        
        self._handler = value


def placeholder(
    pattern: str | re.Pattern | None = None
) -> Callable[[Callable], Placeholder]:
    """
    Decorator to make a method a placeholder handler.

    Parameters
    ----------
    pattern: `str` | `Pattern` | `None`
        Regex pattern to match the placeholder. If `None`, matches any string.
    """

    def wrapper(func: Callable) -> Placeholder:
        ph = Placeholder(pattern, func)
        ph.__preprocess__ = True
        return ph

    return wrapper
