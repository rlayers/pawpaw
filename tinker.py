import random
import typing

import regex
from ito import Ito, Span
from ito.tests.rand import RandSpans



def dump_itos(*itos: Ito, indent='', __str__: bool = True):
    for i, ito in enumerate(itos):
        s = f' .__str__():"{ito.__str__()}"' if __str__ else ''
        print(f'{indent}{i:,}: .span={ito.span} .descriptor="{ito.descriptor}{s}"')
        dump_itos(*ito.children, indent=indent+'  ', __str__=__str__)
#
# s = 'one 1 two 2 three 3 '
# root = Ito(s)
# print(f'root:')
# dump_itos(root)
# print()
#
# # re = regex.compile(r'(?P<combo>(?:(?P<word>\w+) (?P<digits>\d+) )+)')
# re = regex.compile(r'(?P<combo>(?P<word>\w+) (?P<digits>\d+) )+')
# # re = regex.compile(r'(?:(?P<word>\w+) (?P<digits>\d+) )+')
# desc_func = lambda ito, m, g: 'root' if g == '' else g
# itor = Extract(re, extract_group_zero=True, descriptor_func=desc_func)
# dump_itos(*itor.traverse(root))
# print()
#
# print('Itor')


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

