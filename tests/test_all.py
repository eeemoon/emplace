import pytest

from emplace import Formatter, Placeholder, Replacement, placeholder


class MyFormatter(Formatter):
    def __init__(self, value: str = "empty") -> None:
        super().__init__()

        self.value: str = value
    
    @placeholder("value")
    def value_ph(self):
        return self.value
    
    @placeholder(r"upper_(?P<text>.*)")
    async def upper_ph(self, text: str):
        return text.upper()
    
    @placeholder("same")
    def same_ph(self):
        return "{same}"
    
    @placeholder("info")
    async def info_ph(self, replacement: Replacement):
        return f"from={replacement.start_index}, to={replacement.end_index}, level={replacement.depth}"
    
    @placeholder(r"nest_(?P<text>.*)")
    async def nest_ph(self, text: str):
        return text
    
    
class DerivedFormatter(MyFormatter):
    @placeholder("new")
    def new_ph(self):
        return "new-value"
    

@pytest.mark.asyncio
async def test_empty():
    formatter = Formatter()

    assert await formatter.format("Hello, {World}") == "Hello, {World}"


@pytest.mark.asyncio
async def test_subclass():
    formatter = MyFormatter("orange")

    assert await formatter.format("the color is {value}") == "the color is orange"
    assert await formatter.format("{upper_capital} of Great Britain") == "CAPITAL of Great Britain"
    assert await formatter.format("{upper_{value}}") == "ORANGE"
    assert await formatter.format("the color is \\{value}") == "the color is {value}"
    assert await formatter.format("{upper_{same}}") == "{SAME}"


@pytest.mark.asyncio
async def test_add_placeholder():
    fmt1 = Formatter()
    fmt2 = Formatter()

    fmt2.add_placeholder(Placeholder(r"decorate_(?P<text>.*)", lambda text: '-'.join(text)))

    assert await fmt1.format("{decorate_qiwi}") == "{decorate_qiwi}"
    assert await fmt2.format("{decorate_qiwi}") == "q-i-w-i"


@pytest.mark.asyncio
async def test_identifiers():
    formatter = Formatter('$[', ']', escape='+')
    formatter.add_placeholder(Placeholder("value", lambda: "test"))

    assert await formatter.format("{value}") == "{value}"
    assert await formatter.format("$[value]") == "test"
    assert await formatter.format("$[value+]") == "$[value]"

    formatter.opener = "%"
    formatter.closer = "%"

    assert await formatter.format("%value%") == "test"


@pytest.mark.asyncio
async def test_replacement_info():
    formatter = MyFormatter()

    assert await formatter.format("{info}") == "from=0, to=6, level=0"
    assert await formatter.format("{nest_{info}}") == "from=6, to=12, level=1"


@pytest.mark.asyncio
async def test_inheritance():
    formatter = DerivedFormatter()

    assert await formatter.format("{upper_{new}}") == "NEW-VALUE"