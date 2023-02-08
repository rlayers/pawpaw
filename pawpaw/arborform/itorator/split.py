from __future__ import annotations
import enum
import typing

import regex
from pawpaw import Span, Ito, Types
from pawpaw.arborform.itorator import Itorator


class Split(Itorator):
    @enum.unique
    class BoundaryRetention(enum.Enum):
        NONE = 0
        LEADING = 1
        TRAILING = 2

    def __init__(
            self,
            re: regex.Pattern,
            group: int | str = 0,
            boundary_retention: BoundaryRetention = BoundaryRetention.NONE,
            return_zero_split: bool = True,
            desc: str | None = None,
            tag: str | None = None
    ):
        """Given P-O-O-S where P is prefix, - is boundary, O is/are middle part(s), and S is suffix, the
        behavior is as follows:

          * BoundaryRetention.NONE -> P O O S : boundaries are discarded (this is an 'ordinary' split operation)

          * BoundaryRetention.LEADING -> -O -O -S : boundaries kept as prefixes, leading P is discarded

          * BoundaryRetention.TRAILING -> P- O- O- : boundaries kept as suffixes, trailing S is discarded

        Zero-length boundaries are allowable, and any resulting empty Ito's are discarded

       Args:
        re: A regex pattern used to find matches
        group: A key used to identify a group from the matches; the resulting group will be used as the
          boundary; defaults to 0 (the entire match)
        boundary_retention: A rule used to determine if boundaries are discarded, or else how they are kept
        return_zero_split: Indicates how to handle the zero-split condition; when True and splits occur,
          returns a list containing a clone of the input Ito; when False and no splits occur, returns an
          empty list
        desc: Value used for the .desc of any returned Itos; note that a returned Ito can be surrounded by
          0, 1, or 2 boundaries, i.e., there is no clear mapping from a result to a boundary
        """
        super().__init__(tag)
        self.re = re
        self.group = group
        self.boundary_retention = boundary_retention
        self.return_zero_split = return_zero_split
        self.desc = desc

    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
        rv: typing.List[Ito] = []
        prior: Span | None = None
        for m in ito.regex_finditer(self.re):
            cur = Span(*m.span(self.group))
            if prior is None:
                if self.boundary_retention == self.BoundaryRetention.LEADING:
                    start = stop = 0
                else:
                    start = ito.start
                    if self.boundary_retention == self.BoundaryRetention.NONE:
                        stop = cur.start
                    else:  # TRAILING
                        stop = cur.stop
            else:
                if self.boundary_retention == self.BoundaryRetention.NONE:
                    start = prior.stop
                    stop = cur.start
                elif self.boundary_retention == self.BoundaryRetention.LEADING:
                    start = prior.start
                    stop = cur.start
                else:  # TRAILING
                    start = prior.stop
                    stop = cur.stop

            if start != stop:
                rv.append(ito.clone(start, stop, self.desc))

            prior = cur

        if prior is not None and self.boundary_retention != self.BoundaryRetention.TRAILING:
            if self.boundary_retention == self.BoundaryRetention.NONE:
                start = prior.stop
            else:  # LEADING
                start = prior.start
            stop = ito.stop
            if start != stop:
                rv.append(ito.clone(start, stop, self.desc))

        if len(rv) == 0 and self.return_zero_split:
            rv.append(ito.clone(desc=self.desc))

        return rv
