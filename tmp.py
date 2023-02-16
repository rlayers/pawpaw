import regex
from pawpaw import Ito, arborform

# INPUT
text = """\na\n\nQ So I do first want to bring up exhibit No. 46, which is in the binder 
in front of\nyou.\n\nAnd that is a letter [to] Alston\n& Bird...
\n\nIs that correct?\n\nA This is correct.\n\nQ Okay."""

# BUILD PARSER
itor_split = arborform.Split(regex.compile(r'\n+(?=Q_? )', regex.DOTALL), desc='Q/A tuple')

itor_filt = arborform.Filter(lambda i: i.str_startswith('Q'))  # toss "random text" stuff
itor_split.itor_next = itor_filt

itor_qa_split = arborform.Split(regex.compile(r'\n+(?=A_? )', regex.DOTALL))
itor_filt.itor_children = itor_qa_split

itor_extract = arborform.Extract(
    regex.compile(r'([QA])_? (?<QorA>.+)', regex.DOTALL),
    desc_func=lambda ito, match, group: match.group(1))
itor_qa_split.itor_next = itor_extract

# from pawpaw import visualization
# root = Ito(text)
# root.children.add(*itor_split(root))
# print(visualization.pepo.Tree().dumps(root))
# exit(0)

# OUTPUT
for i, tup in enumerate(itor_split(Ito(text))):
    print(f'{tup:%desc} {i:,}:')
    for qa in tup.children:
        print(f'\t{qa:%desc% : %substr!r}')
    print()

op = """
Q/A tuple 0:
    Q: 'So I do first want to bring up exhibit No. 46, which is in the binder \nin front of\nyou.\n\nAnd that is a letter [to] Alston\n& Bird...\n\n\nIs that correct?'
    A: 'This is correct.'

Q/A tuple 1: 
    Q: 'Okay.'
"""    