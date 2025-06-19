[![python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads)

# placeholders
Fast and Pythonic way to process placeholders.

## Examples
```python
import asyncio
from placeholders import Formatter, placeholder


class MyFormatter(Formatter):
    @placeholder(r"upper_(?P<text>.*)")
    def upper_ph(self, text: str) -> str:
        return text.upper()
    

async def main():
    formatter = MyFormatter()
    result = await formatter.format("Hello, {upper_world}")
    print(result) # Hello, WORLD


asyncio.run(main())
```