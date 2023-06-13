import sys
import os.path
import fnmatch

import regex
import pawpaw

# Build pawpaw parser
re = regex.compile(r'(?<=^|\n)(?=MODEL \d+)', regex.DOTALL)
splitter = pawpaw.arborform.Split(re)

re = regex.compile(r'(?<model>MODEL (?<tag>\d+)((?:\n(?<remark>REMARK (?<tag>[^\s]+) (?<value>[^\n]+)))+))', regex.DOTALL)
extractor = pawpaw.arborform.Extract(re)
con = pawpaw.arborform.Connectors.Delegate(extractor)
splitter.connections.append(con)

# Select desired remark columns
desired_remarks = ['minimizedAffinity', 'CNNscore', 'CNNaffinity']

# Dump first line (column headers)
column_headers = ['Compound', 'Model']
column_headers.extend(desired_remarks)
print('\t'.join(column_headers))

def dump(compound: str, ito: pawpaw.Ito) -> str:
    rows = []
    for model in ito.children:
        columns = [compound]
        columns.append(model.find('*[d:tag]'))
        for dr in desired_remarks:
            columns.append(model.find(f'*[d:remark]/*[d:tag]&[s:{dr}]/>[d:value]'))
        rows.append('\t'.join(str(c) for c in columns))
    return '\n'.join(rows)

# Read files and dump contents of each
for path in os.scandir(os.path.join(sys.path[0])):
    if path.is_file() and fnmatch.fnmatch(path.name, 'compound_*.pdbqt'):
        compound = path.name.split('_', 1)[-1].split('.', 1)[0]  # compound number
        with open(os.path.join(sys.path[0], path)) as f:
            ito = pawpaw.Ito(f.read(), desc='all')
            ito.children.add(*splitter(ito))
            print(dump(compound, ito))
