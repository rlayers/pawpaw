from __future__ import annotations
import itertools
import typing

import regex
import pawpaw

# DEFINE PATTERNS

# string literals
STRING_PREFIXES = ['f', 'm', 'r']
string_literals = [
    # strings
    regex.compile(r"(?P<LIT_STR>(?P<prefix>\L<prefix>?)\'(?P<value>(?:[^\\]|\\.)*?)\')", regex.DOTALL, prefix=STRING_PREFIXES),
]

# blank lines
NEWLINES = ['\n']
WHITESPACE = [' ', '\t']
blank_lines = [
    regex.compile(r'\L<whitespace>*(?=\L<newline>)', regex.DOTALL, whitespace=WHITESPACE, newline=NEWLINES),
    regex.compile(r'(?:^|\L<newline>)\L<whitespace>*(?=\L<newline>|$)', regex.DOTALL, newline=NEWLINES, whitespace=WHITESPACE),
]

# indents
indents = [
    regex.compile(r'(?<BOF>^)', regex.DOTALL),
    regex.compile(r'(?<INDENT>(?:^|\L<newline>)(?P<value>\L<whitespace>*))(?!\L<newline>)', regex.DOTALL, newline=NEWLINES, whitespace=WHITESPACE),
    regex.compile(r'(?<EOF>(?:\L<newline>\L<whitespace>*)*$)', regex.DOTALL, newline=NEWLINES, whitespace=WHITESPACE),
]

# comments
comments = [
    regex.compile(r'(?<COMMENT>#(?P<value>.*))', regex.DOTALL),
]

# whitespace
whitespace: list[regex.Pattern] = [
    regex.compile(r'\L<whitespace>+', regex.DOTALL, whitespace=WHITESPACE),
]

# operators
operators: list[regex.Pattern] = [
    {
        # grouping
        ':': 'COLON',
        '(': 'LPAREN',
        ')': 'RPAREN',

        # comparitor
        '<=': 'LE',
        '<': 'LT',
        '>': 'GE',
        '>=': 'GT',
        '!=': 'NE',
        '==': 'EQ',

        # assignment
        '=': 'ASSIGN',
        '**=': 'ASSIGN_POW',
        '//=': 'ASSIGN_IDIV',
        '+=': 'ASSIGN_ADD',
        '-=': 'ASSIGN_SUB',
        '*=': 'ASSIGN_MUL',
        '/=': 'ASSIGN_DIV',
        '%=': 'ASSIGN_MOD',
        '&=': 'ASSIGN_BIT_AND',
        '|=': 'ASSIGN_BIT_OR',
        '~=': 'ASSIGN_BIT_NOT',
        '\^=': 'ASSIGN_BIT_XOR',
        '<<=': 'ASSIGN_BIT_LS',
        '>>=': 'ASSIGN_BIT_RS',

        # math
        '++': 'PLUSPLUS',
        '--': 'MINUSMINUS',
        '**': 'POW',
        '//': 'IDIV',
        '+': 'ADD',
        '-': 'SUB',
        '*': 'MUL',
        '/': 'DIV',
        '%': 'MOD',
        '&': 'BIT_AND',
        '|': 'BIT_OR',
        '~': 'BIT_NOT',
        '^': 'BIT_XOR',
        '<<': 'BIT_LS',
        '>>': 'BIT_RS',

        # null coalesce
        '??': 'NULL_COALESCE',
        '?.': 'NULL_CONDITIONAL',

        # range
        '..': 'RANGE',

        # lambda expr
        '=>': 'LAMBDA_EXPR',
    }
]

# IDs
"""
1. Identifiers must start with a unicode letter or underscore (_).
2. Identifiers may contain Unicode letter characters, decimal digit characters, Unicode connecting characters,
   Unicode combining characters, or Unicode formatting characters.
"""
ids: list[regex.Pattern] = [
    regex.compile(r'(?P<ID>[\p{Letter}_][\p{Letter}\p{Decimal_Number}\p{Connector_Punctuation}\p{Lm}_]*)', regex.DOTALL),
]

# Keywords
keywords = [
    {
        # Functions
        'func': 'FUNC',

        # Control structures
        'if': 'IF',
        'elif': 'ELIF',
        'else': 'ELSE',

        'case': 'CASE',

        'for': 'FOR',

        'do': 'DO',
        'while': 'WHILE',
        'until': 'UNTIL',

        'break': 'BREAK',
        'continue': 'CONTINUE',

        # Logical operators
        'not': 'NOT',
        'and': 'AND',
        'or': 'OR',
        'xor': 'XOR',

        # Set operators
        'in': 'IN',
        # union (+, ∪), intersection (+, ∩), complement (~), difference (-)

        # Types
        'bool': 'BOOL',
        'int': 'INT',
        'float': 'FLOAT',
        'complex': 'COMPLEX',
        'char': 'CHAR',
        'str': 'STR',

        # Bool literals
        'true': 'LIT_BOOL_TRUE',
        'false': 'LIT_BOOL_FALSE',

        # OOP
        'class': 'CLASS',
    }
]

# other_literals
other_literals: list[regex.Pattern] = [
    # int
    regex.compile(r'(?P<LIT_INT_DEC>\d(?:_?\d)*)', regex.DOTALL),  # no prefix
    regex.compile(r'(?P<LIT_INT_BIN>0[bB][01](?:_?[01])*)', regex.DOTALL),  # 0b or 0B prefix
    regex.compile(r'(?P<LIT_INT_OCT>0[oO][0..7](?:_?[0..7])*)', regex.DOTALL),  # 0o or 0O prefix
    regex.compile(r'(?P<LIT_INT_HEX>)0(?i:x[0..9a..z](?:_?[0..9a..z])*)', regex.DOTALL),  # 0x or 0X prefix

    # char
    regex.compile(r'(?P<LIT_CHAR>"(?P<value>[^\\]|\\.)")', regex.DOTALL),
]

# operators
finals: list[regex.Pattern] = [
    {
        # grouping
        '.': 'DOT',
    },

    regex.compile(r'(?<EOL>$)', regex.DOTALL),  # no prefix
]

# BUILD LEXER

Lexer = pawpaw.arborform.Reflect()

def to_connection(*args) -> pawpaw.arborform.Connector:
    itor: pawpaw.arborform.Itorator | None = None

    if len(args) == 1:
        if isinstance(re := args[0], regex.Pattern):
            e = pawpaw.arborform.Extract(re)
            itor = pawpaw.arborform.Gaps(e)

        elif isinstance(d := args[0], dict):
            re = regex.compile(r'(?P<__named_list__>\L<__named_list__>)', regex.DOTALL, __named_list__=list(d.keys()))
            e = pawpaw.arborform.Extract(re, desc_func=lambda i, m, gk: d[m[0]])
            itor = pawpaw.arborform.Gaps(e)

    elif len(args) == 2:
        desc, val = args

        if isinstance(val, str):
            re = regex.compile(rf'(?P<{desc}>{regex.escape(val)})', regex.DOTALL)
            return to_connection(re)

        if isinstance(val, regex.Pattern):
            itor = pawpaw.arborform.Split(
                val,
                group=0,
                boundary_retention=pawpaw.arborform.Split.BoundaryRetention.DISTINCT,
                boundary_desc=desc
            )

    if itor is None:
        raise ValueError(f'unknown action for args {args}')

    return pawpaw.arborform.Connectors.Recurse(itor, lambda ito: ito.desc is None)

def append_extractions(items: typing.Iterable) -> None:
    for i in items:
        con = to_connection(*i) if isinstance(i, tuple) else to_connection(i)
        Lexer.connections.append(con)

def append_deletes(res: typing.Iterable[regex.Pattern]) -> None:
    for re in res:
        s = pawpaw.arborform.Split(re, boundary_retention=pawpaw.arborform.Split.BoundaryRetention.NONE)
        con = pawpaw.arborform.Connectors.Recurse(s, lambda ito: ito.desc is None)
        Lexer.connections.append(con)

def append_exacts(items: typing.Iterable):
    for i in items:
        itor = pawpaw.arborform.Itorator.wrap(lambda ito: [ito.clone(desc=i[s])] if (s := str(ito)) in i.keys() else [ito])
        con = pawpaw.arborform.Connectors.Recurse(itor, lambda ito: ito.desc is None)
        Lexer.connections.append(con)

append_extractions(string_literals)

append_deletes(blank_lines)

append_extractions(itertools.chain(indents, comments))

append_deletes(whitespace)

append_extractions(operators)

append_exacts(keywords)

append_extractions(itertools.chain(ids, other_literals, finals))
