import random
import typing

import regex
from segments import Span, Ito, __version__
from segments.tests.util import RandSpans


print(__version__)
print(__version__.major)
print(__version__.pre_release)
print(__version__.asdict())
exit(0)


def dump_itos(*itos: Ito, indent='', __str__: bool = True):
    for i, ito in enumerate(itos):
        s = f' .__str__():"{ito.__str__()}"' if __str__ else ''
        print(f'{indent}{i:,}: .span={ito.span} .descriptor="{ito.descriptor}{s}"')
        dump_itos(*ito.children, indent=indent+'  ', __str__=__str__)


def test_add_hierarchical():
    string = ' ' * 1028
    root = Ito(string, descriptor='root')
    levels = 15
    parents = [root]

    # Add ordered
    for i in range(1, levels):
        next_parents = []
        for parent in parents:
            j = max(1, len(parent) // 5)
            rs = RandSpans((j, j + 2), (0, 2))
            children = [parent.clone(*s) for s in rs.generate(string, *parent.span)]
            parent.children.add(*children)
            next_parents.extend(children)
        parents = next_parents

    # Add shuffled
    descendants = [*root.walk_descendants()]
    print(f'len(descendants): {len(descendants):,}')
    root.children.clear()
    for d in descendants:
        d.children.clear()
    random.shuffle(descendants)
    root.children.add_hierarchical(*descendants)

    dump_itos(root, __str__=False)

test_add_hierarchical()

