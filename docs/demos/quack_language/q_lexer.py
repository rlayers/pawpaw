from __future__ import annotations
from abc import ABC

import regex
import pawpaw

# DEFINE PATTERNS

# string literals
STRING_PREFIXES = ['f', 'm', 'r']
string_literals: list[regex.Pattern] = [
    # strings
    regex.compile(r"(?P<LIT_STR>\L<prefix>?\'(?P<value>[^\\]|(\\.))*?\')", regex.DOTALL, prefix=STRING_PREFIXES),
]

# blank lines
NEWLINES = ['\n']
blank_lines: list[regex.Pattern] = [
    regex.compile(r'(?<=^|\L<newline>)(?:\s*\L<newline>)+', regex.DOTALL, newline=NEWLINES),
]

# other
others: list[regex.Pattern] = [
    regex.compile(r'(?<=^|\L<newline>)(?P<INDENT>\s+)', regex.DOTALL, newline=NEWLINES),
    regex.compile(r'(?<COMMENT>#.*?)(?=\L<newline>)', regex.DOTALL, newline=NEWLINES),
]


class Matcher(ABC):
    @abstractmethod
    def itor(self) -> pawpaw.arborform.Itorator:
        ...

class MatcherExact:
    def __init__(self, desc: str, pattern: str):
        self.desc = desc
        self.pattern = pattern

    def itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Itorator.wrap(lambda ito: Ito.clone(ito, desc=tag) if ito.str_eq(self.pattern) else None)

# Reserved words
reserved: list[regex.Pattern] = [
        regex.compile(r'(?P<ELIF>elif)', regex.DOTALL),
        regex.compile(r'(?P<IF>if)', regex.DOTALL),
        regex.compile(r'(?P<ELSE>else)', regex.DOTALL),
        
        regex.compile(r'(?P<CASE>case)', regex.DOTALL),

        regex.compile(r'(?P<FOR>for)', regex.DOTALL),

        regex.compile(r'(?P<DO>do)', regex.DOTALL),
        regex.compile(r'(?P<WHILE>while)', regex.DOTALL),
        regex.compile(r'(?P<UNTIL>until)', regex.DOTALL),

        regex.compile(r'(?P<BREAK>break)', regex.DOTALL),
        regex.compile(r'(?P<CONTINUE>continue)', regex.DOTALL),

    # Logical operators
        regex.compile(r'(?P<NOT>not)', regex.DOTALL),
        regex.compile(r'(?P<AND>and)', regex.DOTALL),
        regex.compile(r'(?P<OR>or)', regex.DOTALL),
        regex.compile(r'(?P<XOR>xor)', regex.DOTALL),

    # Set operators
        regex.compile(r'(?P<IN>in)', regex.DOTALL),

    # Types
        regex.compile(r'(?P<BOOL>bool)', regex.DOTALL),
        regex.compile(r'(?P<INT>int)', regex.DOTALL),
        regex.compile(r'(?P<FLOAT>float)', regex.DOTALL),
        regex.compile(r'(?P<COMPLEX>complex)', regex.DOTALL),
        regex.compile(r'(?P<CHAR>char)', regex.DOTALL),
        regex.compile(r'(?P<STR>str)', regex.DOTALL),

    # Bool literals
        regex.compile(r'(?P<LIT_BOOL_TRUE>true)', regex.DOTALL),
        regex.compile(r'(?P<LIT_BOOL_FALSE>false)', regex.DOTALL),

    # OOP
        regex.compile(r'(?P<CLASS>class)', regex.DOTALL),
)

# operators
operators: list[regex.Pattern] = [
    # grouping
    regex.compile(r'(?P<COLON>:)', regex.DOTALL),
    regex.compile(r'(?P<LPAREN>\()', regex.DOTALL),
    regex.compile(r'(?P<RPAREN>\))', regex.DOTALL),

    # comparitor
    regex.compile(r'(?P<LE>\<=)', regex.DOTALL),
    regex.compile(r'(?P<LT>\<)', regex.DOTALL),
    regex.compile(r'(?P<GE>\>=)', regex.DOTALL),
    regex.compile(r'(?P<GT>\>)', regex.DOTALL),
    regex.compile(r'(?P<NE>!=)', regex.DOTALL),
    regex.compile(r'(?P<EQ>==)', regex.DOTALL),

    # assignment
    regex.compile(r'(?P<ASSIGN>=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_POW>\*\*=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_IDIV>//=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_ADD>\+=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_SUB>-=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_MUL>\*=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_DIV>/=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_MOD>%=)', regex.DOTALL),

    regex.compile(r'(?P<ASSIGN_BIT_AND>&=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_BIT_OR>\|=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_BIT_NOT>~=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_BIT_XOR>\^=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_BIT_LS>\<\<=)', regex.DOTALL),
    regex.compile(r'(?P<ASSIGN_BIT_RS>\>\>=)', regex.DOTALL),

    # math
    regex.compile(r'(?P<PLUSPLUS>\+\+)', regex.DOTALL),
    regex.compile(r'(?P<MINUSMINUS>\-\-)', regex.DOTALL),
    regex.compile(r'(?P<POW>\*\*)', regex.DOTALL),
    regex.compile(r'(?P<IDIV>\/\/)', regex.DOTALL),
    regex.compile(r'(?P<ADD>\+)', regex.DOTALL),
    regex.compile(r'(?P<SUB>\-)', regex.DOTALL),
    regex.compile(r'(?P<MUL>\*)', regex.DOTALL),
    regex.compile(r'(?P<DIV>\/)', regex.DOTALL),
    regex.compile(r'(?P<MOD>%)', regex.DOTALL),

    regex.compile(r'(?P<BIT_AND>&)', regex.DOTALL),
    regex.compile(r'(?P<BIT_OR>\|)', regex.DOTALL),
    regex.compile(r'(?P<BIT_NOT>~)', regex.DOTALL),
    regex.compile(r'(?P<BIT_XOR>\^)', regex.DOTALL),
    regex.compile(r'(?P<BIT_LS>\<\<)', regex.DOTALL),
    regex.compile(r'(?P<BIT_RS>\>\>)', regex.DOTALL),
]

# other_literals
other_literals: list[regex.Pattern] = [
    # int
    regex.compile(r'(?P<LIT_INT_DEC>\d(?:_?\d)*)', regex.DOTALL),  # no prefix
    regex.compile(r'(?P<LIT_INT_BIN>0[bB][01](?:_?[01])*)', regex.DOTALL),  # 0b or 0B prefix
    regex.compile(r'(?P<LIT_INT_OCT>0[oO][0..7](?:_?[0..7])*)', regex.DOTALL),  # 0o or 0O prefix
    regex.compile(r'(?P<LIT_INT_HEX>)0(?i:x[0..9a..z](?:_?[0..9a..z])*)', regex.DOTALL),  # 0x or 0X prefix

    # char
    regex.compile(r'(?P<LIT_CHAR>"(?P<value>[^\\]|(\\.))")', regex.DOTALL, prefix=STRING_PREFIXES),
]

# ids
"""
1. Identifiers must start with a letter or underscore (_).
2. Identifiers may contain Unicode letter characters, decimal digit characters, Unicode connecting characters,
   Unicode combining characters, or Unicode formatting characters.
"""
ids: list[regex.Pattern] = [
    regex.compile(r'(?P<ID>[\p{Letter}_][\p{Letter}\p{Decimal_Number}\p{Connector_Punctuation}\p{Lm}\p{Bidi_Class}_]*)', regex.DOTALL),
]

# whitespace
whitespace: list[regex.Pattern] = [
    regex.compile(r'\s+', regex.DOTALL),
]

# BUILD LEXER

lexer = pawpaw.arborform.Reflect()

def extract(*res: regex.Pattern):
    for re in res:
        e = pawpaw.arborform.Extract(re)
        g = pawpaw.arborform.Gaps(e)
        c = pawpaw.arborform.Connectors.Recurse(g, lambda ito: ito.desc is None)
        lexer.connections.append(c)

def remove(*res: regex.Pattern):
    for re in res:
        s = pawpaw.arborform.Split(re, boundary_retention=pawpaw.arborform.Split.BoundaryRetention.NONE)
        c = pawpaw.arborform.Connectors.Recurse(s, lambda ito: ito.desc is None)
        lexer.connections.append(c)        

extract(*string_literals)

remove(*blank_lines)

extract(*others, *operators, *ids)

remove(*whitespace)


