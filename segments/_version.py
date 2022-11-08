import typing


class PreRelease(typing.NamedTuple):
    kind: str  # 'a', 'b', or 'rc' : see https://peps.python.org/pep-0440/
    number: int

    def __str__(self) -> str:
        return f'{self.kind}{self.number}'
      
      
class Version(typing.NamedTuple):
    major: int
    minor: int
    micro: int
    pre_release: PreRelease | None

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}.{self.micro}{self.pre_release}'

    @classmethod
    def _from(cls, version: str):
        parts = version.split('.')
        if len(parts) == 4:
            pr = parts[-1]  # must have len > 2
            i = 1 if pr[1].isnumeric() else 2
            pre_release = PreRelease(pr[:i], int(pr[i:]))
        else:
            pre_release = None

        mmm = [int(i) for i in parts[:3]]
        return Version(*mmm, pre_release)


__VER_STR__ = '2.0.0.a3'  # string literal to be used for build, setup, and documentation tools

__version__ = Version._from(__VER_STR__)
