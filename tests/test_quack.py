from __future__ import annotations

import regex
import pawpaw

lexer = pawpaw.arborform.Reflect()

STRING_PREFIXES = ['f', 'm', 'r']
itor_string = pawpaw.arborform.Split(
    regex.compile(r"\L<prefix>?\'([^\\]|(\\.))*?\'", regex.DOTALL, prefix=STRING_PREFIXES),
    boundary_retention=pawpaw.arborform.Split.BoundaryRetention.DISTINCT,
    boundary_desc='LIT_STR'
)
con = pawpaw.arborform.Connectors.Recurse(itor_string, lambda ito: ito.desc is None)
lexer.connections.append(con)

NEWLINES = ['\n']
itor_blank_lines = pawpaw.arborform.Split(
    regex.compile(r'(?<=^|\L<newline>)(?:\s*\n)+', regex.DOTALL, newline=NEWLINES),
    boundary_retention=pawpaw.arborform.Split.BoundaryRetention.NONE,
)
con = pawpaw.arborform.Connectors.Recurse(itor_blank_lines, lambda ito: ito.desc is None)
lexer.connections.append(con)

itor_indent = pawpaw.arborform.Split(
    regex.compile(r'(?<=^|\L<newline>)\s+', regex.DOTALL, newline=NEWLINES),
    boundary_retention=pawpaw.arborform.Split.BoundaryRetention.DISTINCT,
    boundary_desc='INDENT'
)
con = pawpaw.arborform.Connectors.Recurse(itor_indent, lambda ito: ito.desc is None)
lexer.connections.append(con)

itor_comment = pawpaw.arborform.Split(
    regex.compile(r'#.*?(?=\L<newline>)', regex.DOTALL, newline=NEWLINES),
    boundary_retention=pawpaw.arborform.Split.BoundaryRetention.DISTINCT,
    boundary_desc='COMMENT'
)
con = pawpaw.arborform.Connectors.Recurse(itor_comment, lambda ito: ito.desc is None)
lexer.connections.append(con)

itor_ws_splitter = pawpaw.arborform.Split(
    regex.compile(r'\s+', regex.DOTALL),
    boundary_retention=pawpaw.arborform.Split.BoundaryRetention.NONE
)
con = pawpaw.arborform.Connectors.Recurse(itor_ws_splitter, lambda ito: ito.desc is None)
lexer.connections.append(con)


# t_LIT_INT_DEC = r'\d(?:_?\d)*'  # no prefix
# t_LIT_INT_BIN = r'0[bB][01](?:_?[01])*'  # 0b or 0B prefix
# t_LIT_INT_OCT = r'0[oO][0..7](?:_?[0..7])*'  # 0o or 0O prefix
# t_LIT_INT_HEX = r'0(?i:x[0..9a..z](?:_?[0..9a..z])*)'  # 0x or 0X prefix

source = """
x = 1
    + 2

# Here is a comment

my_str = 'Long
    text with
    
blank lines'

y = x + 3
"""

for i in lexer(pawpaw.Ito(source)):
    print(f'({i:<%desc> %span \'%substr!1r1:40…% \'})')
