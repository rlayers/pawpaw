from __future__ import annotations
import enum
import types
import typing
import itertools

import regex
from pawpaw import Errors, Span, Ito, Types, type_magic
from pawpaw.arborform.itorator import Itorator, Extract


class Split(Itorator):
    @enum.unique
    class BoundaryRetention(enum.Enum):
        NONE = 0
        LEADING = 1
        TRAILING = 2
        ALL = 3

    def __init__(
            self,
            splitter: Itorator | regex.Pattern,
            limit: int | None = None,
            boundary_retention: BoundaryRetention = BoundaryRetention.NONE,
            return_zero_split: bool = True,
            desc: str | None = None,
            tag: str | None = None
    ):
        """Given P-O-O-S where P is prefix, - is boundary, O is/are middle segments(s), and S is suffix, the
        behavior is as follows:

          * BoundaryRetention.NONE -> P O O S : boundaries are discarded (this is an 'ordinary' split operation)

          * BoundaryRetention.LEADING -> -O -O -S : boundaries kept as prefixes, leading P is discarded

          * BoundaryRetention.TRAILING -> P- O- O- : boundaries kept as suffixes, trailing S is discarded

          * BoundaryRetention.ALL -> P – O – O – : all non-zero-length boundaries kept as distincts

        Zero-length boundaries are allowable, and any resulting empty Ito's are discarded

       Args:
        splitter: An Itorator used to generate boundariesto locate boundaries; if a regex.Pattern is supplied,
          splitter is set to a pawpaw.itorator.Extract as follows:

            splitter = pawpaw.itorator.Extract(
                re,
                desc = lambda match, group_key: None,
                group_filter = lambda m, gk: gk == 0,
                tag = f'generated Split for \\{re.pattern}\\'
            )

        re: A regex pattern used to find matches

        group_key: A key used to identify a group from the matches; the resulting group will be used as the
          boundary; defaults to 0 (the entire match)

        boundary_retention: A rule used to determine if boundaries are discarded, or else how they are kept

        return_zero_split: Indicates how to handle the zero-split condition; when True and splits occur,
          returns a list containing a clone of the input Ito; when False and no splits occur, returns an
          empty list

        desc: Value used for the .desc of any yielded non-boundary Itos.
        """
        super().__init__(tag)
        
        if isinstance(splitter, Itorator):
            self.splitter = splitter
        elif isinstance(splitter, regex.Pattern):
            self.splitter = Extract(
                splitter,
                desc = lambda match, group_key: None,
                group_filter = lambda m, gk: gk == 0,
                tag = f'generated Split for \\{splitter.pattern}\\'
            )
        else:
            raise Errors.parameter_invalid_type('splitter', splitter, Itorator, regex.Pattern)
        
        if not isinstance(limit, (int, type(None))):
            raise Errors.parameter_invalid_type('limit', limit, int, types.NoneType)
        self.limit = limit

        if not isinstance(boundary_retention, self.BoundaryRetention):
            raise Errors.parameter_invalid_type('boundary_retention', boundary_retention, self.BoundaryRetention)
        self.boundary_retention = boundary_retention

        if not isinstance(return_zero_split, bool):
            raise Errors.parameter_invalid_type('return_zero_split', return_zero_split, bool)
        self.return_zero_split = return_zero_split

        if not isinstance(desc, (str, type(None))):
            raise Errors.parameter_invalid_type('desc', desc, str, types.NoneType)
        self.desc = desc

    def clone(self, tag: str | None = None) -> Split:
        return type(self())(
            self.splitter,
            self.limit,
            self.boundary_retention,
            self.return_zero_split,
            self.desc,
            self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        if self.limit == 0 and self.return_zero_split:
            return ito.clone(desc=self.desc, clone_children=False),

        rv: typing.List[Ito] = []
        
        count = 0
        prior: Span | None = None
        for cur in itertools.takewhile(lambda i: self.limit is None or count < self.limit, self.splitter(ito)):
            if prior is None:
                if self.boundary_retention == self.BoundaryRetention.LEADING:
                    start = stop = 0
                else:
                    start = ito.start
                    if self.boundary_retention in (self.BoundaryRetention.NONE, self.BoundaryRetention.ALL):
                        stop = cur.start
                    else:  # TRAILING
                        stop = cur.stop
            else:
                if self.boundary_retention in (self.BoundaryRetention.NONE, self.BoundaryRetention.ALL):
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
                rv.append(ito.clone(start, stop, self.desc, False))

            if self.boundary_retention == self.BoundaryRetention.ALL and (cur.start < cur.stop):
                rv.append(cur)

            prior = cur

        if prior is not None and self.boundary_retention != self.BoundaryRetention.TRAILING:
            if self.boundary_retention in (self.BoundaryRetention.NONE, self.BoundaryRetention.ALL):
                start = prior.stop
            else:  # LEADING
                start = prior.start
            stop = ito.stop
            if start != stop:
                rv.append(ito.clone(start, stop, self.desc, False))

        if prior is None and len(rv) == 0 and self.return_zero_split:
            rv.append(ito.clone(desc=self.desc, clone_children=False))

        return rv
