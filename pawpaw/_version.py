from __future__ import annotations

import typing

__version__ = '1.0.0.a5'
"""The str literal that build, setup, documentation, and other tools typically want
"""

class _PreRelease(typing.NamedTuple):
    kind: str  # 'a', 'b', or 'rc' : see https://peps.python.org/pep-0440/
    number: int

    def __str__(self) -> str:
        return f'{self.kind}{self.number}'
      
      
class _Version(typing.NamedTuple):
    major: int
    minor: int
    micro: int
    pre_release: _PreRelease | None

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}.{self.micro}{self.pre_release}'

    @classmethod
    def _from(cls, version: str):
        parts = version.split('.')
        if len(parts) == 4:
            pr = parts[-1]  # must have len > 2
            i = 1 if pr[1].isnumeric() else 2
            pre_release = _PreRelease(pr[:i], int(pr[i:]))
        else:
            pre_release = None

        mmm = [int(i) for i in parts[:3]]
        return cls(*mmm, pre_release)


Version = _Version._from(__version__)
