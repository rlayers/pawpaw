import string
import typing

import regex

__version__ = '1.0.1'
"""The str literal that build, setup, documentation, and other tools typically want."""

class Version:
    _canonical_re = regex.compile(r'^([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?(?:\+[a-z0-9]+(?:[-_\.][a-z0-9]+)*)?$')
    """This pattern taken from https://peps.python.org/pep-0440/#appendix-b-parsing-version-strings-with-regular-expressions
    and expanded to support optional "local version identifier" (see https://peps.python.org/pep-0440/#local-version-identifiers)."""

    @classmethod
    def is_canonical(cls, version: str) -> bool:
        return cls._canonical_re.match(version) is not None

    _parse_pat = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>a|b|c|rc|alpha|beta|pre|preview)
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""
    """Taken from https://peps.python.org/pep-0440/#appendix-b-parsing-version-strings-with-regular-expressions and
    corrected so that group pre_l has no sub-group and behaves like post_l and dev_l groups"""

    parse_re = regex.compile(r"^\s*" + _parse_pat + r"\s*$", regex.VERBOSE | regex.IGNORECASE)
    """regex that could be used by pawpaw to create a parse tree for a version str"""

if not Version.is_canonical(__version__):
    raise ValueError(f'__version__ is non-canonical with pep-0440')
