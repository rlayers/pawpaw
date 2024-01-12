from pawpaw.nlp import TableStyle, StyledTable

"""
Notes:

MUST HAVE CHARACTERISTICS:

    - Must be able to determine start and stop in order to identify within larger
        unstructured text

    - Have way to distinguish columns and ROWS (i.e., a table represented with tabs
        doesn't allow for row delineations

    - Optionally has a header row(s)

STYLES:

Style 1: md style

    | A | B | C |
    |---|:-:|--:|
    | a | b | c |
    | d | e | f |

Style 2: rst

    2.a rst Simple Table

    =====  =====  =======
    A      B      A and B
    =====  =====  =======
    False  False  False
    True   False  False
    False  True   False
    True   True   True
    =====  =====  =======

    2.b rst Grid Table

    +------------+------------+-----------+
    | Header 1   | Header 2   | Header 3  |
    +============+============+===========+
    | body row 1 | column 2   | column 3  |
    +------------+------------+-----------+
    | body row 2 | Cells may span columns.|
    +------------+------------+-----------+
    | body row 3 | Cells may  | - Cells   |
    +------------+ span rows. | - contain |
    | body row 4 |            | - blocks. |
    +------------+------------+-----------+

Style 3: Ascii doc

    [cols="e,m,^,>s",width="25%"]
    |============================
    |1 >s|2 |3 |4
    ^|5 2.2+^.^|6 .3+<.>m|7
    ^|8
    |9 2+>|10
    |============================
"""
    
"""
Style 4: Misc ASCII

    pipe, hypen, plus
    
    +---+---+---+
    | A | B | C |
    +---+---+---+
    | a | b | c |
    +---+---+---+
    | d | e | f |
    +---+---+---+

    pipe, em-dash, plus

    +———+———+———+
    | A | B | C |
    +———+———+———+
    | a | b | c |
    +———+———+———+
    | d | e | f |
    +———+———+———+

    misc ascii box drawing line styles
    
    ┌───┬───┬───┐
    │ A │ B │ C │
    ├───┼───┼───┤
    │ a │ b │ c │
    ├───┼───┼───┤
    │ d │ e │ f │
    └───┴───┴───┘    

    ┏━━━┳━━━┳━━━┓
    ┃ A ┃ B ┃ C ┃
    ┣━━━╋━━━╋━━━┫
    ┃ a ┃ b ┃ c ┃
    ┣━━━╋━━━╋━━━┫
    ┃ d ┃ e ┃ f ┃
    ┗━━━┻━━━┻━━━┛

    ┏━━━┳━━━┳━━━┓
    ┃ A ┃ B ┃ C ┃
    ┡━━━╇━━━╇━━━┩
    │ a │ b │ c │
    ├───┼───┼───┤
    │ d │ e │ f │
    └───┴───┴───┘
        
    ╔═══╦═══╦═══╗
    ║ A ║ B ║ C ║
    ╠═══╬═══╬═══╣
    ║ a ║ b ║ c ║
    ╠═══╬═══╬═══╣
    ║ d ║ e ║ f ║
    ╚═══╩═══╩═══╝    

    ╔═══╤═══╤═══╗
    ║ A │ B │ C ║
    ╟───┼───┼───╢
    ║ a │ b │ c ║
    ╟───┼───┼───╢
    ║ d │ e │ f ║
    ╚═══╧═══╧═══╝    
"""

"""
Style 5 [Unamed]

-----+-----+-----
  A  |  B  |  C
-----+-----+-----      
 aaa | bbb | ccc
-----+-----+-----      

"""

p = r'-{2,}[\-\+]*-{2,}'
style = TableStyle(p, None, p, None)
TYPE_5 = StyledTable(style, 'Table Style 5')
del style
del p

"""
Style 6 [Unamed]

-------------------
|  A  |  B  |  C  |
-------------------     
| aaa | bbb | ccc |
-------------------     

"""

p = r'-{2,}'
style = TableStyle(p, None, p, None)
TYPE_6 = StyledTable(style, 'Table Style 6')
del style
del p
