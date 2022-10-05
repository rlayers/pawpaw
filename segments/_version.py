import typing


class PreRelease(typing.NameTuple):
    kind: str
    number: int

    def __str__(self) -> str:
        return f'{self.kind}{self.number}'
      
      
class Version(typing.NameTuple):
    major: int
    minor: int
    micro: int
    pre_release: PreRelease | None

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}.{self.micro}{self.pre_release}'


__version__ = Version(2, 0, 0, PreRelease('a', 3))
