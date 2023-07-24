import sys
import os.path
import fnmatch
import typing

import regex
import pawpaw

# Build pawpaw parser
re = regex.compile(r'(?<=^|\n)(?=MODEL \d+)', regex.DOTALL)
splitter = pawpaw.arborform.Split(re)

pat = r"""
(?P<model>
    MODEL\ 
    (?<tag>\d+)
    (?:\n
        (?<remark>
            REMARK\ 
            (?<tag>[^\s]+)\ 
            (?<value>[^\n]+)
        )
    )+
    (?:\n
        (?>!=REMARK)
        (?<text>.+)
    )?
)+
"""
re = regex.compile(pat, regex.VERBOSE | regex.DOTALL)
extractor = pawpaw.arborform.Extract(re)
con = pawpaw.arborform.Connectors.Delegate(extractor)
splitter.connections.append(con)

# Prints using fixed-width for visibility: change to delimited if needed
def dump_row(cols: list) -> None:
    print(*(f'{v: <18}' for v in cols))  

# Select desired remark columns
desired_remarks = ['minimizedAffinity', 'CNNscore', 'CNNaffinity']

# Headers
headers = ['Compound', 'Model']
headers.extend(desired_remarks)
dump_row(headers)

# Create rows from compound file
def compound_vals(compound: str, ito: pawpaw.Ito) -> typing.Iterable[list[str]]:
    for model in ito.children:
        vals = [compound]
        vals.append(str(model.find('*[d:tag]')))
        for dr in desired_remarks:
            vals.append(str(model.find(f'*[d:remark]/*[d:tag]&[s:{dr}]/>[d:value]')))
        yield vals

# Read files and dump contents of each
for path in os.scandir(os.path.join(sys.path[0])):
    if path.is_file() and fnmatch.fnmatch(path.name, 'compound_*.txt'):
        compound = path.name.split('_', 1)[-1].split('.', 1)[0]  # compound number
        with open(os.path.join(sys.path[0], path)) as f:
            ito = pawpaw.Ito(f.read(), desc='all')
            ito.children.add(*splitter(ito))
            for vals in compound_vals(compound, ito):
                dump_row(vals)
