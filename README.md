[![pypi](https://img.shields.io/pypi/v/emplace)](https://pypi.org/project/emplace)
[![python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads)
[![codecov](https://codecov.io/gh/eeemoon/emplace/graph/badge.svg?token=4CGDOZ7ADZ)](https://codecov.io/gh/eeemoon/emplace)

# emplace
Modern and easy way to handle placeholders.

This package allows you to define text placeholders and process them dynamically. It's like `str.format()`, but gives you much more flexibility.

## Features
- **Reg**ular **Ex**pressions to find placeholders.
- Custom delimiters (`%var%`, `{var}`, `${var}` etc.).
- Modern API using asyncio and decorators.
- Nested placeholders (`{greet_{name}}`).
- Type safety using annotations.
- No additional dependencies.

## Installation
To install this module, run the following command:
```
pip install emplace
```

## Usage
Example of creating a formatter with single placeholder.
```python
from emplace import Formatter, placeholder

class MyFormatter(Formatter):
    @placeholder(r"upper_(?P<text>.*)")
    def upper_ph(self, text: str) -> str:
        return text.upper()
    
formatter = MyFormatter()
result = await formatter.format("Hello, {upper_world}!")
print(result) # Hello, WORLD!
```

## Examples
You can check out more examples [here](examples).