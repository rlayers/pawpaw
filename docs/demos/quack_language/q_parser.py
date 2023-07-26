from __future__ import annotations
import itertools
import typing

import regex
import pawpaw
from q_lexer import Lexer, NEWLINES


def line_col(ito: pawpaw.Ito) -> str:
    lc = ito.to_line_col(NEWLINES[0])
    return f'Ln {lc[0]}, Col {lc[1]}'

def Parser(source: str) -> typing.Iterable[str]:
    indents = list[pawpaw.Ito]()
    expression = list[pawpaw.Ito]()

    def do_expression() -> typing.Iterable[str]:
        yield 'EXPRESSION_START'
        yield f'expr: {pawpaw.Ito.join(*expression):%substr!r}'
        # yield f'expr: {[i.desc for i in expression]}'
        expression.clear()
        yield 'EXPRESSION_STOP'

    yield 'PROGRAM_START'

    final = pawpaw.Ito(source, -1, desc='EOF')
    for ito in itertools.chain.from_iterable([Lexer(pawpaw.Ito(source)), (final,)]):

        if ito.desc is None:
            raise Exception(f'unknown token {ito:%substr!r} at {ito.to_line_col(NEWLINES[0])}')
        
        if ito.desc in ('INDENT', 'EOF'):
            if len(indents) == 0:
                if ito.desc == 'INDENT':
                    yield 'BLOCK_START'
                    indents.append(ito)
            
            else:
                indent_cur = 0 if ito.desc == 'EOF' else len(ito.find('*[d:value]'))
                
                while len(indents) > 0:
                    indent_last = len(indents[-1].find('*[d:value]'))

                    if indent_cur > indent_last:
                        if len(expression) > 0 and expression[-1].desc == 'COLON':
                            yield from do_expression()
                            yield 'BLOCK_START'
                            indents.append(ito)
                        break

                    if len(expression) > 0 and expression[-1].desc == 'COLON':
                        raise Exception(f'missing indent at {line_col(ito)} following colon at {line_col(expression[-1])}')

                    if len(expression) > 0:
                        yield from do_expression()
                        
                    if indent_cur < indent_last or ito.desc == 'EOF':
                        yield 'BLOCK_STOP'
                        indents.pop()

                    if ito.desc == 'INDENT' and indent_cur == indent_last:
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

