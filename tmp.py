import regex
from pawpaw import Ito, arborform

text = """\na\n\nQ So I do first want to bring up exhibit No. 46, which is in the binder 
in front of\nyou.\n\nAnd that is a letter [to] Alston\n& Bird...
\n\nIs that correct?\n\nA This is correct.\n\nQ Okay."""

splitter = arborform.Extract(regex.compile(r'((?<=^|\n+)(?<QA>Q_? (?<Q>.+?)(?:\n+(?:$|(?A_ ?(?<A>.+?)', regex.DOTALL))
for i, qa in enumerate(splitter(Ito(text))):
    print(f'Q/A pair {i:,}:')
    print(f'\tQ: {qa.children[0]:%substr!r}') # omit ':%substr!r' if you don't want the string repr'd
    if (len(qa.children) > 1):
        print(f'\tA: {qa.children[1]:%substr!r}')  # omit ':%substr!r' if you don't want the string repr'd
    print()

op = """
Q/A pair 0: 
    Q: 'So I do first want to bring up exhibit No. 46, which is in the binder in front of\nyou.\n\nAnd that is a letter [to] Alston\n& Bird...\n\n\nIs that correct?'
    A: This is correct.

Q/A pair 1: 
    Q: 'So I do first want to bring up exhibit No. 46, which is in the binder in front of\nyou.\n\nAnd that is a letter [to] Alston\n& Bird...\n\n\nIs that correct?'
    A: Okay.
"""    