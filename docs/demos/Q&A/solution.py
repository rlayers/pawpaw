import regex
from pawpaw import Ito, arborform, visualization

# INPUT
text = """\na\n\nQ So I do first want to bring up exhibit No. 46, which is in the binder 
in front of\nyou.\n\nAnd that is a letter [to] Alston\n& Bird...
\n\nIs that correct?\n\nA This is correct.\n\nQ Okay."""

# BUILD PARSER
itor_split = arborform.Split(regex.compile(r'\n+(?=Q_? )', regex.DOTALL), desc='Q/A tuple')

itor_filt = arborform.Filter(lambda i: i.str_startswith('Q'))  # toss "random text" stuff
con = arborform.Connectors.Delegate(itor_filt)
itor_split.connections.append(con)

# Assumes only one answer per question
itor_qa_split = arborform.Split(regex.compile(r'\n+(?=A_? )', regex.DOTALL), limit=1)
con = arborform.Connectors.Children.Add(itor_qa_split)
itor_filt.connections.append(con)

itor_extract = arborform.Extract(
    regex.compile(r'([QA])_? (?<QorA>.+)', regex.DOTALL),
    desc=lambda match, group: match.group(1))
con = arborform.Connectors.Children.Add(itor_extract)
itor_qa_split.connections.append(con)

# OUTPUT TREE
root = Ito(text)
tree_vis = visualization.pepo.Tree()
for i in itor_split(root):
    print(tree_vis.dumps(i))
print()

# OUTPUT TUPLE
for i, tup in enumerate(itor_split(root)):
    print(f'{tup:%desc} {i:,}:')
    for qa in tup.children:
        print(f'\t{qa:%desc% : %substr!r}')
    print()
