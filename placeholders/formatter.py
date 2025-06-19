from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Coroutine

from .placeholder import Placeholder


@dataclass
class Replacement:
    """Replacement data."""

    placeholder: str = ...
    """Placeholder without identifiers."""
    depth: int = ...
    """Nesting level."""
    value: str | None = None
    """Processed value. Only available for children."""
    children: list[Replacement] = field(default_factory=list)
    """Inner placeholders."""
    start_index: int = ...
    """Start index including identifiers."""
    end_index: int = ...
    """End index including identifiers."""


class Formatter:
    """
    Placeholder formatter.

    Examples
    --------
    >>> class CountFormatter(Formatter):
    ...     def __init__(self, count: int) -> None:
    ...         super().__init__()
    ...
    ...         self.count: int = count
    ...
    ...     @placeholder("count")
    ...     async def count_handler(self) -> int:
    ...         return self.count
    ...
    >>> formatter = CountFormatter(5)
    >>> await formatter.format("Count is {count}")
    'Count is 5'
    """

    _preprocessed: list[Placeholder] = []

    def __init_subclass__(cls) -> None:
        cls._preprocessed = [
            i
            for c in reversed(cls.__mro__) 
            if issubclass(c, Formatter) 
            for i in c.__dict__.values()
            if isinstance(i, Placeholder) and hasattr(i, '__preprocess__')
        ]

    def __init__(
        self, 
        opener: str = '{', 
        closer: str = '}',
        *,
        escape: str | None = '\\'
    ) -> None:
        """
        Parameters
        ----------
        opener: `str`
            Left placeholder identifier.
        closer: `str`
            Right placeholder identifier.
        escape: `str`
            Escape string. 
            If opener or closer follows it, they are not identified.
        """        
        self.opener = opener
        self.closer = closer
        self.escape = escape
        self._placeholders: list[Placeholder] = []
        
        for ph in self._preprocessed:
            self.add_placeholder(ph)

    async def _process(self, data: Replacement) -> Any:
        raw = data.placeholder

        for ph in self._placeholders:
            if ph.pattern is None:
                kwargs = {}
            elif m := ph.pattern.fullmatch(raw):
                kwargs = m.groupdict()
            else:
                continue
            
            skip = False
            signature = inspect.signature(ph.handler)

            for param in signature.parameters.values():
                if param.name in kwargs:
                    base = param.annotation
                    if base is not inspect.Parameter.empty:
                        try:
                            kwargs[param.name] = base(kwargs[param.name])
                        except Exception:
                            skip = True 
                elif param.annotation is Replacement:
                    kwargs[param.name] = data
            
            if skip:
                continue
         
            if ph in self._preprocessed:
                result = ph.handler(self, **kwargs)
            else:
                result = ph.handler(**kwargs)

            if isinstance(result, Coroutine):
                result = await result

            return result
   
        return None
    
    @property
    def opener(self) -> str:
        """Placeholder start identifier."""
        return self._opener
    
    @opener.setter
    def opener(self, value: str) -> None:
        if not isinstance(value, str) or not value:
            raise ValueError("'opener' should be a non-empty string")
        
        self._opener = value

    @property
    def closer(self) -> str:
        """Placeholder end identifier."""
        return self._closer
    
    @closer.setter
    def closer(self, value: str) -> None:
        if not isinstance(value, str) or not value:
            raise ValueError("'closer' should be a non-empty string")
        
        self._closer = value

    @property
    def escape(self) -> str:
        """Escape sequence for identifiers."""
        return self._escape
    
    @escape.setter
    def escape(self, value: str) -> None:
        if (isinstance(value, str) and not value) and value is not None:
            raise ValueError("'escape' should be a non-empty string or None")
        
        self._escape = value
    
    @property
    def placeholders(self) -> list[Placeholder]:
        return self._placeholders
    
    def add_placeholder(self, ph: Placeholder, /) -> None:
        """
        Add a placeholder handler.

        Parameters
        ----------
        ph: `Placeholder`
            Placeholder to add.
        """
        if not isinstance(ph, Placeholder):
            raise TypeError(f"expected '{Placeholder.__name__}', not '{type(ph)}'")
        
        self._placeholders.append(ph)

    def remove_placeholder(self, ph: Placeholder, /) -> None:
        """
        Remove the placeholder handler.

        Parameters
        ----------
        ph: `Placeholder`
            Placeholder to remove.
        """
        if not isinstance(ph, Placeholder):
            raise TypeError(f"expected '{Placeholder.__name__}', not '{type(ph)}'")
        
        self._placeholders.remove(ph)

    async def format(self, text: str) -> str:
        """
        Replace placeholders in the text.

        Parameters
        ----------
        text: `str`
            Text to format.
        """
        opener = self.opener
        closer = self.closer
        escape = self.escape
        opener_len = len(opener)
        closer_len = len(closer)
        escape_len = len(escape) if escape else 0
        same = self.opener == self.closer
        current = text
        prev_escape = False
        stack: list[Replacement] = []
        index = 0

        while index < len(current):
            # check for escape string
            if escape and current[index : index + escape_len] == escape:
                # previously found escape string, keep only one
                if prev_escape:
                    current = ''.join((
                        current[: index - escape_len],
                        current[index:]
                    ))

                prev_escape = not prev_escape
                index += escape_len
            # check for opener 
            # if opener and closer are the same and there
            # is not opened brace, trigger closer 'elif'
            elif (
                current[index : index + opener_len] == opener 
                and not (same and stack)
            ):
                # save opener if escape string not found before
                if not prev_escape:
                    stack.append(Replacement(start_index=index))
                else:
                    prev_escape = False
                    current = ''.join((
                        current[: index - escape_len],
                        current[index:]
                    ))

                index += opener_len
            # check for closer
            elif current[index : index + closer_len] == closer:
                # process placeholder if there is open brace
                # and escape string not found before
                if not prev_escape:
                    if stack:
                        open_ph = stack.pop()
                        start_index = open_ph.start_index
                        ph = current[start_index + opener_len : index]

                        # process the placeholder
                        open_ph.placeholder = ph
                        open_ph.depth = len(stack)
                        open_ph.end_index = index + closer_len
                        value = await self._process(open_ph)
                        open_ph.value = value

                        if stack:
                            stack[-1].children.append(open_ph)
            
                        # if value is None keep original placeholder
                        replacement = (
                            str(value) 
                            if value is not None else 
                            ''.join((opener, ph, closer))
                        )
                        
                        # replace placeholder in the text
                        current = ''.join((
                            current[:start_index],
                            replacement,
                            current[index + closer_len :]
                        ))
                        index = start_index + len(replacement)
                    else:
                        index += closer_len
                else:
                    prev_escape = False
                    current = ''.join((
                        current[: index - len(escape)],
                        current[index:]
                    ))
            # skip any other character
            else:
                index += 1

        return current