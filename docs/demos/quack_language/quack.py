import os

from pawpaw import Ito, visualization
from q_lexer import Lexer
from q_parser import Parser


vis_boxer = visualization.ascii_box.from_corners('└')
vis_compact = visualization.pepo.Compact()

source = """x = 11
    + 12

# Here is a comment

f_str = f'x: {x}'

my_str = 'Long
    text with
    
blank lines'

y = (x + 30) * 4  
   """
print(*vis_boxer.from_srcs('SOURCE',), sep=os.linesep)
print(source)

print(*vis_boxer.from_srcs('LEXER',), sep=os.linesep)
print(vis_compact.dumps(*Lexer(Ito(source))))

print(*vis_boxer.from_srcs('PARSER',), sep=os.linesep)
for p in Parser(source):
    print(p)
