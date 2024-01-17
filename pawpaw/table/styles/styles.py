from pawpaw.table import TableStyle

"""
Notes:

MUST HAVE CHARACTERISTICS:

    - Must be able to determine start and stop in order to identify within larger
        unstructured text

    - Have way to distinguish columns and ROWS (i.e., a table represented with tabs
        doesn't allow for row delineations

    - Optionally has a header row(s)
"""

"""
Style 1 [Unnamed]

-----+-----+-----
  A  |  B  |  C
-----+-----+-----      
 aaa | bbb | ccc
-----+-----+-----      
"""

p = r'(?:-{2,}(?:\+-+)+)'
TYPE_1 = TableStyle(
    table_start_pat = p,
    row_sep_pat = p,
    equi_distant_indent=False
)
del p


"""
Style 2 [Unnamed]

-------------------
|  A  |  B  |  C  |
|-----------------|
| aaa | bbb | ccc |
-------------------     
"""

p = r'-{2,}'
TYPE_2 = TableStyle(
    table_start_pat = p,
    row_sep_pat = r'\|(?:-+\|)+',
    table_end_pat = p,
    equi_distant_indent=True
)
del p


"""
markdown

    | A | B | C |
    |---|:-:|--:|
    | a | b | c |
    | d | e | f |
"""

"""
reStructuredText

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
"""

"""
ASCII doc

    [cols="e,m,^,>s",width="25%"]
    |============================
    |1 >s|2 |3 |4
    ^|5 2.2+^.^|6 .3+<.>m|7
    ^|8
    |9 2+>|10
    |============================
"""
    
"""
ASCII Misc

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

