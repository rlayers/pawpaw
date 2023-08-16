from __future__ import annotations
import enum
import typing
import itertools

import regex
from pawpaw import Span, Ito, Types
from pawpaw.arborform.itorator import Itorator


class Split(Itorator):
    @enum.unique
    class BoundaryRetention(enum.Enum):
        NONE = 0
        LEADING = 1
        TRAILING = 2
        DISTINCT = 3

    def __init__(
            self,
            re: regex.Pattern,
            limit: int | None = None,
            group: int | str = 0,
            boundary_retention: BoundaryRetention = BoundaryRetention.NONE,
            return_zero_split: bool = True,
            boundary_desc: str | Types.F_M_GK_2_DESC | None = None,
            non_boundary_desc: str | None = None,
            tag: str | None = None
    ):
        """Given P-O-O-S where P is prefix, - is boundary, O is/are middle segments(s), and S is suffix, the
        behavior is as follows:

          * BoundaryRetention.NONE -> P O O S : boundaries are discarded (this is an 'ordinary' split operation)

          * BoundaryRetention.LEADING -> -O -O -S : boundaries kept as prefixes, leading P is discarded

          * BoundaryRetention.TRAILING -> P- O- O- : boundaries kept as suffixes, trailing S is discarded

          * BoundaryRetention.DISTINCT -> P – O – O – : all non-zero-length boundaries kept as distincts

        Zero-length boundaries are allowable, and any resulting empty Ito's are discarded

       Args:
        re: A regex pattern used to find matches
        group: A key used to identify a group from the matches; the resulting group will be used as the
          boundary; defaults to 0 (the entire match)
        boundary_retention: A rule used to determine if boundaries are discarded, or else how they are kept
        return_zero_split: Indicates how to handle the zero-split condition; when True and splits occur,
          returns a list containing a clone of the input Ito; when False and no splits occur, returns an
          empty list
        boundary_desc: If supplied, this value will be passed to Ito.from_match for boundary segments when
          BoundaryRetention.DISTINCT is selected.  Note that a boundary match can have multiple named-groups,
          however, the resulting ito will span the entire regex match (i.e., it corresponds to capture group zero).
          This parameter allows you to override the resulting "0" desc for something else.
        non_boundary_desc: Value used for the .desc of any returned Itos; note that a returned Ito can be surrounded by
          0, 1, or 2 boundaries, i.e., there is no clear mapping from a result to a boundary.
        """
        super().__init__(tag)
        self.re = re
        self.limit = limit
        self.group = group
        self.boundary_retention = boundary_retention
        self.return_zero_split = return_zero_split
        self.boundary_desc = boundary_desc
        self.non_boundary_desc = non_boundary_desc

    def clone(self, tag: str | None = None) -> Split:
        return type(self())(
            self._re,
            self.limit,
            self.group,
            self.boundary_retention,
            self.return_zero_split,
            self.boundary_desc,
            self.non_boundary_desc,
            self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        if self.limit == 0:
            return ito,

        boundary_ito_kwargs = {} if self.boundary_desc is None else {'desc': self.boundary_desc}

        rv: typing.List[Ito] = []
        
        count = 0
        prior: Span | None = None
        for m in itertools.takewhile(lambda i: self.limit is None or count < self.limit, ito.regex_finditer(self.re)):
            cur = Span(*m.span(self.group))
            if prior is None:
                if self.boundary_retention == self.BoundaryRetention.LEADING:
                    start = stop = 0
                else:
                    start = ito.start
                    if self.boundary_retention in (self.BoundaryRetention.NONE, self.BoundaryRetention.DISTINCT):
                        stop = cur.start
                    else:  # TRAILING
                        stop = cur.stop
            else:
                if self.boundary_retention in (self.BoundaryRetention.NONE, self.BoundaryRetention.DISTINCT):
                    start = prior.stop
                    stop = cur.start
                elif self.boundary_retention == self.BoundaryRetention.LEADING:
                    start = prior.start
                    stop = cur.start
                else:  # TRAILING
                    start = prior.stop
                    stop = cur.stop

            count += 1

            if start != stop:
                rv.append(ito.clone(start, stop, self.non_boundary_desc, False))

            if self.boundary_retention == self.BoundaryRetention.DISTINCT and (cur.start < cur.stop):
                rv.append(ito.from_match(m, **boundary_ito_kwargs))

            prior = cur

        if prior is not None and self.boundary_retention != self.BoundaryRetention.TRAILING:
            if self.boundary_retention in (self.BoundaryRetention.NONE, self.BoundaryRetention.DISTINCT):
                start = prior.stop
            else:  # LEADING
                start = prior.start
            stop = ito.stop
            if start != stop:
                rv.append(ito.clone(start, stop, self.non_boundary_desc, False))

        if prior is None and len(rv) == 0 and self.return_zero_split:
            rv.append(ito.clone(desc=self.non_boundary_desc, clone_children=False))

        return rv
