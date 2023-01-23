import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import regex
import pawpaw
from pawpaw import Ito
from pawpaw.visualization import sgr, Highlighter, pepo


v_compact = pepo.Compact()
v_tree = pepo.Tree()
v_xml = pepo.Xml()
v_json = pepo.Json()



import xml.etree.ElementTree as ET
from pawpaw import xml
text = \
"""<?xml version="1.0"?>
<music xmlns:mb="http://musicbrainz.org/ns/mmd-1.0#" xmlns="http://mymusic.org/xml/">
    <?display table-view?>
    <album genre="R&amp;B" mb:id="123-456-789-0">
        Robson Jorge &amp; Lincoln Olivetti <!-- 1982, Vinyl -->
    </album>
</music>"""
root = ET.fromstring(text, parser=xml.XmlParser())

highlighter = Highlighter(sgr.palettes.PAWPAW)
highlighter.print(root.ito)
exit(0)

print(pepo.Tree().dumps(root.ito))
exit(0)



import pawpaw.visualization.ascii_box as box

# Box tests:

c = '─'
bdc = box.BoxDrawingChar.from_char(c)
boxer = box.from_sides(bdc)
for line in boxer.from_srcs('Baby!'):
    print(line)

print()

c = '┃'
bdc = box.BoxDrawingChar.from_char(c)
boxer = box.from_sides(e=bdc)
for line in boxer.from_srcs('Baby!'):
    print(line)

print()

boxer = box.from_sides(n=box.BoxDrawingChar.from_char('┄'), s=box.BoxDrawingChar.from_char('═'))
for line in boxer.from_srcs('Baby!'):
    print(line)

print()

boxer = box.from_sides(n=box.BoxDrawingChar.from_char('┄'), s=box.BoxDrawingChar.from_char('═'))
for line in boxer.from_srcs('Baby!'):
    print(line)

print()

boxer = box.from_corners(box.BoxDrawingChar.from_char('╞'))
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

boxer = box.from_corners(box.BoxDrawingChar.from_char('╯'), box.BoxDrawingChar.from_char('╞'))
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

exit(0)

c = '╍'
bdc = box.BoxDrawingChar.from_char(c)
boxer = box.from_sides(s=bdc)
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

c = '║'
bdc = box.BoxDrawingChar.from_char(c)
boxer = box.from_sides(w=bdc)
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

c = '╬'
bdc = box.BoxDrawingChar.from_char(c)
boxer = box.from_sides(w=bdc)
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

boxer = box.from_sides(n=box.BoxDrawingChar.from_char('─'), w=box.BoxDrawingChar.from_char('║'))
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

c = '╬'
bdc = box.BoxDrawingChar.from_char(c)
boxer = box.from_corners(bdc)
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

c = '┞'
bdc = box.BoxDrawingChar.from_char(c)
boxer = box.from_corners(bdc)
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

boxer = box.from_corners(box.BoxDrawingChar.from_char('╬'))
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()

boxer = box.from_corners(box.BoxDrawingChar.from_char('╬'), box.BoxDrawingChar.from_char('╯'))
for line in boxer.from_srcs('Hello, world!'):
    print(line)

print()


exit(0)

# Test 1 = get from_char
c = '─'
bdc = box.BoxDrawingChar.from_char(c)
print(bdc)

# Test 2 = get from_name
n = 'BOX DRAWINGS LIGHT HORIZONTAL'
bdc = box.BoxDrawingChar.from_name(n)
print(bdc)

# Test 3 = get from_direction_styles with ordered direction styles
ds1 = box.DirectionStyle(box.Direction.W, box.Style())
ds2 = box.DirectionStyle(box.Direction.E, box.Style())
bdc = box.BoxDrawingChar.from_direction_styles(ds1, ds2)
print(bdc)

# Test 4 = get from_direction_styles with mis-ordered direction styles
bdc = box.BoxDrawingChar.from_direction_styles(ds2, ds1)
print(bdc)

# Test 10 = get from single corner
bdc = box.BoxDrawingChar.from_char('└')
bdc = box.BoxDrawingChar.from_char('┑')
boxer = box.from_corners(bdc)
for line in boxer.from_srcs('Hello, world!'):
    print(line)
exit(0)

boxer = pawpaw.visualization.ascii_box.from_corner_symmetric(
    # box.Style(path=box.Style.Path.ARC)
    box.Style(path=box.Style.Path.ARC)
)
for line in boxer.from_text('The quick\nbrown fox\njumped over the lazy\ndogs.'):
    print(line)

exit(0)

chars = set()
for orientation in box.Side.Orientation:
    print(f'Orientation: {orientation}')
    for count in box.Style.Count:
        for weight in box.Style.Weight:
            style = box.Style(weight, count)
            try:
                side = box.Side(style)
                char = side[orientation]
                chars.add(char)
                print(f'\t{char}')
            except:
                pass

print(f'Expected Side character count: {len(box.Side._characters):n}')
print(f'Actual Side character count: {len(chars):n}')

print()

chars = set()
for orientation in box.Side.Orientation:
    print(f'Orientation: {orientation}')
    for hcount in box.Style.Count:
        for hweight in box.Style.Weight:
            hz_style = box.Style(hweight, hcount)
            for vcount in box.Style.Count:
                for vweight in box.Style.Weight:
                    vt_style = box.Style(vweight, vcount)
                    try:
                        corner = box.Corner(hz_style, vt_style)
                        char = corner[orientation]
                        chars.add(char)
                        print(f'\t{char}')
                    except:
                        pass

print(f'Expected Corner character count: {len(box.Corner._characters):n}')
print(f'Actual Corner character count: {len(chars):n}')

exit(0)

import nltk

s = 'Here is one sentence.  Here is another.'
i = Ito(s)

nltk_tok = nltk.tokenize
sent_itor = pawpaw.arborform.Itorator.wrap(lambda ito: ito.from_substrings(ito, *nltk_tok.sent_tokenize(str(ito))))

word_itor = pawpaw.arborform.Itorator.wrap(lambda ito: ito.from_substrings(ito, *nltk_tok.word_tokenize(str(ito))))
sent_itor.itor_children = word_itor

i.children.add(*(sent_itor.traverse(i)))
print(v_tree.dumps(i))
exit(0)


ws_tok = nltk.tokenize.WhitespaceTokenizer()
splitter = pawpaw.arborform.Split(regex.compile(ws_tok._pattern, ws_tok._flags))
i = pawpaw.Ito('The quick brown fox.')
[str(i) for i in splitter.traverse(i)]




# # VERSION
#
# print(pawpaw.__version__)
# print(pawpaw.__version__.major)
# print(pawpaw.__version__.pre_release)
# print(pawpaw.__version__._asdict())
# exit(0)

from pawpaw.arborform.itorator import Desc, Extract, Split, Wrap

s = 'nine 9 ten 10 eleven 11 TWELVE 12 thirteen 13'
re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)\s*)+')
match = re.fullmatch(s)

root = Ito.from_match_super2(match)
print(dump.Compact().dumps(root))
exit(0)

root = next(Ito.from_match(re, s))
# print(*root.find_all('**[d:digit]'), sep=', ')  # print all digits
# print(*root.find_all('**[d:number]{</*[s:i]}'), sep=',')  # print numbers having leter 'i' in their names


root = Ito(s, desc='root')

phrases = Split(regex.compile('(?<=\d )'), desc='Phrase')

wrds_nums = Extract(regex.compile(r'(?P<word>[a-z]+) (?P<number>\d+)'))
phrases.itor_children = wrds_nums

chrs_digs = Extract(regex.compile(r'(?P<char>[a-z])+|(?P<digit>\d)+'))
wrds_nums.itor_children = chrs_digs

root.children.add(*phrases.traverse(root))

print(dump.Compact().dumps(root))
exit(0)

    
# SGR    

for effect in sgr.Intensity, sgr.Italic, sgr.Underline, sgr.Blink, sgr.Invert, sgr.Conceal, sgr.Strike, sgr.Font, sgr.Fore, sgr.Back:
    print(f'{effect.__name__.upper()}')
    
    if effect in (sgr.Fore, sgr.Back):
        attrs = {nc.name: effect(nc) for nc in sgr.Colors.Named}
    else:
        names = filter(lambda n: n.isupper() and not n.startswith('_') and not n.startswith('RESET'), dir(effect))
        attrs = {name: getattr(effect, name) for name in names}
        
    for name, attr in attrs.items():
        print(f'\t{name}: Before Sgr... {attr}Sgr applied!{effect.RESET} Sgr turned off.')
    
    print()

from random import randint

for line in range(1, 50):
    for color in sgr.Fore, sgr.Back:
        for col in range(1, 120):
            rgb = sgr.Colors.Rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            print(effect(rgb), end='')
            print(chr(ord('A') + randint(0, 25)) + effect.RESET, end='')
        print()

exit()


# HIGHLIGHTER

s = 'The quick brown fox'
ito = pawpaw.Ito(s)
ito.children.add(*ito.split(regex.compile('\s+')))

highlighter = Highlighter(
    sgr.Colors.Named.BRIGHT_CYAN,
    sgr.Colors.Named.CYAN,
    sgr.Colors.Named.BRIGHT_BLUE,
    sgr.Colors.Named.BLUE,
    sgr.Colors.Named.MAGENTA,
)
highlighter.print(ito)
