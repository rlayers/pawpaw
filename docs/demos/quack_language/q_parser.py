from __future__ import annotations
import itertools
import typing

import regex
import pawpaw
from q_lexer import Lexer, NEWLINES


def Parser(source: str) -> typing.Iterable[str]:
    indents = list[pawpaw.Ito]()
    expression = list[pawpaw.Ito]()

    final = pawpaw.Ito(source, -1, desc='INDENT')
    final.children.add(final.clone(desc='value'))

    yield 'PROGRAM_START'

    for ito in itertools.chain.from_iterable([Lexer(pawpaw.Ito(source)), (final,)]):
        if ito.desc is None:
            raise f'unknown token {ito:%substr!r} at {ito.to_line_col(NEWLINES[0])}'
        
        if ito.desc in ('INDENT'):
            if len(indents) == 0:
                if ito.desc == 'INDENT':
                    yield 'BLOCK_START'
                    yield 'EXPRESSION_START'
                    indents.append(ito)
            
            else:
                while len(indents) > 0:
                    indent_cur = 0 if ito.desc == 'EOF' else len(ito.find('*[d:value]'))
                    indent_last = len(indents[-1].find('*[d:value]'))

                    if indent_cur > indent_last:
                        break

                    if len(expression) > 0:
                        yield f'expr: {[str(i) for i in expression]}'
                        expression.clear()
                        yield 'EXPRESSION_STOP'
                        
                    if indent_cur < indent_last:
                        yield 'BLOCK_STOP'
                        indents.pop()

                    elif indent_cur == indent_last:
                        yield 'EXPRESSION_START'
                        break

        else:
            expression.append(ito)

    yield 'PROGRAM_END'

# program ::= {statement}
# statement ::= "PRINT" (expression | string) nl
#     | "IF" comparison "THEN" nl {statement} "ENDIF" nl
#     | "WHILE" comparison "REPEAT" nl {statement} "ENDWHILE" nl
#     | "LABEL" ident nl
#     | "GOTO" ident nl
#     | "LET" ident "=" expression nl
#     | "INPUT" ident nl
# comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
# expression ::= term {( "-" | "+" ) term}
# term ::= unary {( "/" | "*" ) unary}
# unary ::= ["+" | "-"] primary
# primary ::= number | ident
# nl ::= '\n'+



# grammar Expr;
# prog:	expr EOF ;
# expr:	expr ('*'|'/') expr
#     |	expr ('+'|'-') expr
#     |	INT
#     |	'(' expr ')'
#     ;
# NEWLINE : [\r\n]+ -> skip;
# INT     : [0-9]+ ;

