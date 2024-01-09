from abc import ABC, abstractmethod, abstractproperty
import dataclasses

import regex
import pawpaw
from pawpaw import nuco


@dataclasses.dataclass(frozen=True)
class TableStyle:
    start_pat: str = ''
    header_end_pat: str = ''
    row_end_pat: str = ''
    end_pat: str = ''


class Table(ABC):
    @abstractproperty
    def re(self) -> regex.Pattern:
        ...

    def get_itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Extract(self.re, tag=self.itor_tag)


class StyledTable(Table):
    @classmethod
    def _build_re(cls, style: TableStyle) -> regex.Pattern:
        return regex.compile('(?<=\n)(?<table>' + style.start_pat + '\n(?:.+?\n' + style.end_pat + ')+)', regex.DOTALL)

    def __init__(self, style: TableStyle, tag: str | None):
        self.style = style
        self._re = self._build_re(style)
        self.tag = tag

    @property
    def re(self) -> regex.Pattern:
        return self._re

    def get_itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Extract(self._re, tag=self.tag)


class Tables:
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

    Style 2a: rst  Simple

    =====  =====  ======
       Inputs     Output
    ------------  ------
      A      B    A or B
    =====  =====  ======
    False  False  False
    True   False  True
    False  True   True
    True   True   True
    =====  =====  ======

    Style 2b: rst Grid

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
    

    Style 5a: [Unamed]

    -----+-----+-----
      A  |  B  |  C
    -----+-----+-----      
     aaa | bbb | ccc
    -----+-----+-----      

    Style 5b: [Unamed]

    -------------------
    |  A  |  B  |  C  |
    -------------------     
    | aaa | bbb | ccc |
    -------------------     

    """

    p = r'-{2,}[\-\+]*-{2,}'
    style = TableStyle(p, p, p, p)
    Style_A = StyledTable(style, 'table type A extractor')
    del style
    del p

    '''
        -------------
        | A | B | C |
        -------------
        | a | b | c |
        | a |   | c
        -------------       
    '''
    p = r'-{2,}'
    style = TableStyle(p, p, p, p)
    Style_B = StyledTable(style, 'table type A extractor')
    del style
    del p
