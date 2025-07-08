import asyncio

from colorama import Fore, init

from emplace import Formatter, Replacement, placeholder


class Highlighter(Formatter):
    COLORS: tuple[str] = (Fore.YELLOW, Fore.MAGENTA, Fore.BLUE)

    @placeholder()
    async def wildcard(self, data: Replacement) -> str:
        color = self.COLORS[data.depth % len(self.COLORS)] 
   
        return ''.join((
            color,
            self.opener,
            Fore.RESET,
            data.placeholder,
            color,
            self.closer,
            Fore.RESET
        ))
    

async def main():
    init()

    formatter = Highlighter()

    result = await formatter.format("{{example}_{of}} {highlighting_{based_{{on}_{the}}}} {{nesting}_level}")
    print(result)


asyncio.run(main())