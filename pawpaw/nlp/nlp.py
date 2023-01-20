import itertools
import locale
import typing

import regex
import pawpaw
from pawpaw import nuco

# See https://www.unicode.org/Public/UNIDATA/NamesList.txt

byte_order_controls = {
    'Big-endian byte order mark':       '\uFEFF',   # "UTF-16BE"
    'Little-endian byte order mark':    '\uFFFE',   # "UTF-16LE"
}

unicode_white_space_LF_FF = {
    'LINE FEED':                    '\u000A',
    'FORM FEED':                    '\u000C',
}

unicode_white_space_other = {
    'CHARACTER TABULATION':         '\u0009',

    'CARRIAGE RETURN':              '\u000D',

    'SPACE':                        '\u0020',

    'NO-BREAK SPACE':               '\u00A0',

    'EN QUAD':                      '\u2000',
    'EM QUAD':                      '\u2001',
    'EN SPACE':                     '\u2002',
    'EM SPACE':                     '\u2003',
    'THREE-PER-EM SPACE':           '\u2004',
    'FOUR-PER-EM SPACE':            '\u2005',
    'SIX-PER-EM SPACE':             '\u2006',
    'FIGURE SPACE':                 '\u2007',
    'PUNCTUATION SPACE':            '\u2008',
    'THIN SPACE':                   '\u2009',
    'HAIR SPACE':                   '\u200A',
    'ZERO WIDTH SPACE':             '\u200B',

    'NARROW NO-BREAK SPACE':        '\u202F',
    
    'MEDIUM MATHEMATICAL SPACE':    '\u205F',

    'IDEOGRAPHIC SPACE':            '\u3000',
}

unicode_single_quote_marks = {
    'APOSTROPHE':                                           '\u0027',
    'GRAVE ACCENT':                                         '\u0060',
    'ACUTE ACCENT':                                         '\u00B4',

    'LEFT SINGLE QUOTATION MARK':                           '\u2018',
    'RIGHT SINGLE QUOTATION MARK':                          '\u2019',

    'SINGLE LOW-9 QUOTATION MARK':                          '\u201A',
    'SINGLE HIGH-REVERSED-9 QUOTATION MARK':                '\u201B',

    'HEAVY SINGLE TURNED COMMA QUOTATION MARK ORNAMENT':    '\u275B',
    'HEAVY SINGLE COMMA QUOTATION MARK ORNAMENT':           '\u275C',

    'HEAVY LOW SINGLE COMMA QUOTATION MARK ORNAMENT':       '\u275F',
}

unicode_double_quote_marks = {
    'QUOTATION MARK':                                       '\u0022',

    'LEFT DOUBLE QUOTATION MARK':                           '\u201C',
    'RIGHT DOUBLE QUOTATION MARK':                          '\u201D',

    'DOUBLE LOW-9 QUOTATION MARK':                          '\u201E',
    'DOUBLE HIGH-REVERSED-9 QUOTATION MARK':                '\u201F',

    'HEAVY DOUBLE TURNED COMMA QUOTATION MARK ORNAMENT':    '\u275D',
    'HEAVY DOUBLE COMMA QUOTATION MARK ORNAMENT':           '\u275E',

    'HEAVY LOW DOUBLE COMMA QUOTATION MARK ORNAMENT':       '\u2760',
}


class Number:
    _sign_pat = r'(?P<sign>[-+])'
    _sci_exp_e_notation_pat = r'[Ee]' + _sign_pat + r'?\d+'
    _sci_exp_x10_notation_pat = r' ?[Xx\u2715] ?10\^ ?' + _sign_pat + r'?\d+'
    _sci_exp_pat = r'(?P<exponent>' + '|'.join([_sci_exp_e_notation_pat, _sci_exp_x10_notation_pat]) + r')'

    def build_integer_pat(self) -> None:
        self._int_pat = r'(?P<integer>\d{1,3}(?:' + regex.escape(self.thousands_sep) + r'\d{3})*'
        if self.thousands_sep_optional:
            self._int_pat += r'|\d+'
        self._int_pat += r')'

    def build_decimal_pat(self) -> None:
        self._decimal_pat = r'(?P<decimal>' + regex.escape(self.decimal_point) + r'\d+)'

    def build_num_pat_re(self) -> None:
        self.build_integer_pat()
        self.build_decimal_pat()
        self._num_pat = f'(?P<number>{self._sign_pat}?' \
            f'(?:{self._int_pat}{self._decimal_pat}?' \
            f'|{self._decimal_pat})' \
            f'{self._sci_exp_pat}?)'

        self._re = regex.compile(self._num_pat, regex.DOTALL)

    def __init__(self, **kwargs):
        # defaults
        loc = locale.localeconv()
        self._decimal_point = loc['decimal_point']
        self._thousands_sep = loc['thousands_sep'] if loc['thousands_sep'] != '' else ','
        self._thousands_sep_optional = True

        # kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

        # build patterns & re
        self._int_pat: str
        self._decimal_pat: str
        self._num_pat: str
        self._re: regex.Pattern

        self.build_num_pat_re()

    # region properties

    @property
    def decimal_point(self) -> str:
        return self._decimal_point

    @decimal_point.setter
    def decimal_point(self, decimal_point: str) -> None:
        self._decimal_point = decimal_point
        self.build_num_pat_re()

    @property
    def thousands_sep(self) -> str:
        return self._thousands_sep

    @thousands_sep.setter
    def thousands_sep(self, thousands_sep: str) -> None:
        if not isinstance(thousands_sep, str):
            raise pawpaw.Errors.parameter_invalid_type('thousands_sep', thousands_sep, str)
        if thousands_sep == '' or thousands_sep.isspace():
            raise ValueError('parameter \'thousands_sep\' must contain a non-whitespace character')
        self._thousands_sep = thousands_sep
        self.build_decimal_pat()

    @property
    def thousands_sep_optional(self) -> bool:
        return self._thousands_sep_optional

    @thousands_sep_optional.setter
    def thousands_sep_optional(self, thousands_sep_optional: bool) -> None:
        self._thousands_sep_optional = thousands_sep_optional
        self.build_num_pat_re()        

    @property
    def integer_pat(self) -> str:
        return self._int_pat

    @property
    def decimal_pat(self) -> str:
        return self._decimal_pat

    @property
    def sci_exp_pat(self) -> str:
        return self._sci_exp_pat

    @property
    def num_pat(self) -> str:
        return self._num_pat

    @property
    def re(self) -> regex.Pattern:
        return self._re


class Table:
    """
    Style 1: md style

    | A | B | C |
    |---|:-:|--:|
    | a | b | c |
    | d | e | f |

    Style 2: Misc ASCII

    +───+───+───+
    | A | B | C |
    +───+───+───+
    | a | b | c |
    | d | e | f |
    +───+───+───+

    +---+---+---+
    | A | B | C |
    +---+---+---+
    | a | b | c |
    +---+---+---+
    | d | e | f |
    +---+---+---+

    ╔═══╦═══╦═══╗
    ║ A ║ B ║ C ║
    ╠═══╬═══╬═══╣
    ║ a ║ b ║ c ║
    ╠═══╬═══╬═══╣
    ║ d ║ e ║ f ║
    ╚═══╩═══╩═══╝    

    Style 3a: rst  Simple

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

    Style 3b: rst Grid

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

    Style 4: Ascii doc

    [cols="e,m,^,>s",width="25%"]
    |============================
    |1 >s|2 |3 |4
    ^|5 2.2+^.^|6 .3+<.>m|7
    ^|8
    |9 2+>|10
    |============================

    Style 5: [Unamed]

    -----+-----+-----
      A  |  B  |  C
    -----+-----+-----      
     aaa | bbb | ccc
    -----+-----+-----      

    Style 6: Tabbed

    A\tB\tC
    a\tb\tc




    """

    pass


class List:
    """
    quantifier patterns
        \d+  :
        §{1,2}  :  Section (Silcrow) : "16 U.S.C. § 580(p)",  "§§ 13–21"
        [A-Z]{1,2}  :
        [MDCLXVI]+  : Latin numerals (could be case insensitive - but should all be same case)

    prefix patterns:
        •  : Before quantifier

    suffix patterns
        -
        .
        :
        .)
       
    """

    pass

class Sentence:
    _prefix_chars = list(unicode_single_quote_marks.values())
    _prefix_chars.extend(unicode_double_quote_marks.values())
    _prefix_chars.extend(c for c in '([{')

    _terminators = [
        r'\.',      # Full stop
        r'\.{3,}',  # Ellipses; three periods
        r'…',       # Ellipses char
        r'[\!\?]+'  # Exclamation & Question mark(s)
    ]

    _suffix_chars = list(unicode_single_quote_marks.values())
    _suffix_chars.extend(unicode_double_quote_marks.values())
    _suffix_chars.extend(c for c in ')]}')

    # Words that start sentences with high frequency
    _hf_start_words = [
        'A',
        'How',
        'In',
        'It',
        'The',
        'There',
        'This',
        'What',
        'When',
        'Where',
        'Who',
        'Why',
    ]

    # Common abbrs that are typically followed by a digit
    _numeric_abbrs = [
        'c.',      # circa
        'ca.',     # circa
        'ed.',     # edition
        'illus.',  # circa
        'no.',     # number
        'p.',      # page
        'pp.',     # pages
        'ver.',    # version
        'vol.',    # volume
    ]

    # Common abbrs that are typically not sentence boundaries, even when followed by uppercase
    _ignore_abbrs = [
        'Ald.',     # Alderman
        'Asst.',    # Assistent
        'Dr.',      # Doctor
        'Drs.',     # Doctors
        'ed.',      # editor
        'e.g.',     # exempli gratia
        'Fr.',      # Father
        'Gov.',     # Governor
        'Hon.',     # Honorable (sometimes Rt. Hon. for Right Honorable)
        'ibid.',    # ibidem
        'i.e.',     # ed est
        'illus.',   # illustrated by
        'Insp.',    # Inspector
        'Messrs.',  # plural of Mr.
        'Mlle.',    # Mademoiselle
        'Mmes.',    # Missus
        'Mr.',      # Mister
        'Mrs.',     # plural of Mrs.
        'Ms.',      # Miss
        'Msgr.',    # Monsignor  
        'Mt.',      # Mount / Mountain
        'pub.',     # published by / publisher
        'pseud.',   # pseudonym
        'Pres.',    # President
        'Prof.',    # Professor
        'qtd.',     # quoted in
        'Rep.',     # Representative
        'Reps.',    # Representatives
        'Rev.',     # Reverend
        'Sen.',     # Senator
        'Sens.',    # Senators
        'St.',      # Saint
        'vis.',     # videlicet
        'v.',       # versus
        'vs.',      # versus
    ]

    # Military officer abbrs: see https://pavilion.dinfos.edu/Article/Article/2205094/military-rank-abbreviations/
    _mil_officer_abbrs = [
        'Lt.',         # Lieutenant
        'Capt.',       # Captain
        'Cpt.',        # Captain
        'Maj.',        # Major
        'Cmdr.',       # Commander
        'Col.',        # Colonel
        'Brig.',       # Brigadier (as in Brigadier General)
        'Gen.',        # General
        'Adm.',        # Admiral
    ]

    # Military enlisted abbrs: see https://pavilion.dinfos.edu/Article/Article/2205094/military-rank-abbreviations/
    _mil_enlisted_abbrs = [
        'Pvt.',      # Private
        'Pfc.',      # Private First Class
        'Spc.',      # Specialist
        'Cpl.',      # Corporal
        'Sgt.',      # Sergeant
    ]

    _ignores = _ignore_abbrs
    _ignores.extend(_mil_officer_abbrs)
    _ignores.extend(_mil_enlisted_abbrs)

    _sen_ws = ['\r\n', '\n']
    _sen_ws.extend(unicode_white_space_other.values())

    _exceptions = [
        r'(?<!\L<ignores>)',                                            # Ignores 
        r'(?<!\L<num_abbrs>(?=\L<sen_ws>\d))',                          # Numeric abbr followed by a digit
        r'(?<![A-Z][a-z]+\L<sen_ws>[A-Z]\.(?=\L<sen_ws>[A-Z][a-z]+))',  # Common human name pattern
        r'(?<!U\.S\.(?=\L<sen_ws>Government))',                         # "U.S. Government"
    ]

    _rules = [
        # End of document
        r'\L<sen_ws>*$',

        # Suffix
        # r'(?<=\L<sen_suf>+)\L<sen_ws>*',
        
        # Two or more whitespace
        r'\L<sen_ws>{2,}',
        
        # High frequency sentence start word
        r'\L<sen_ws>(?=\L<sen_pre>*\L<hf_starts>\L<sen_ws>)',
        
        # Catch all with exceptions
        r''.join(_exceptions) + r'\L<sen_ws>(?=\L<sen_pre>*[A-Z\d])',
    ]

    combined = '|'.join(f'(?:{r})' for r in _rules)

    _re = regex.compile(
        r'(?<=\w(' + '|'.join(_terminators) + r')\L<sen_suf>*)(?:' + combined + r')',
        regex.DOTALL,
        sen_suf=_suffix_chars,
        sen_ws=_sen_ws,
        sen_pre=_prefix_chars,
        hf_starts=_hf_start_words,
        num_abbrs=_numeric_abbrs,
        ignores=_ignores,
    )

    @property
    def re(self) -> regex.Pattern:
        return self._re


class SimpleNlp:
    _paragraph_pat = r'(?:\r?\n\L<other_ws>*){2,}'
    _paragraph_re = regex.compile(_paragraph_pat, regex.DOTALL, other_ws=unicode_white_space_other)

    _trimmable_ws = list(byte_order_controls.values())
    _trimmable_ws.extend(unicode_white_space_LF_FF.values())
    _trimmable_ws.extend(unicode_white_space_other.values())

    _word_pat = r'\w(?:(?:\L<sqs>|-\s*)?\w)*'

    def __init__(self, number: Number | None = None, chars: bool = False):
        super().__init__()

        paragraph = pawpaw.arborform.Split(self._paragraph_re, desc='paragraph')

        para_trimmer = pawpaw.arborform.Itorator.wrap(lambda ito: [ito.str_strip(''.join(self._trimmable_ws))])
        paragraph.itor_next = para_trimmer

        sentence = pawpaw.arborform.Split(Sentence().re, desc='sentence')
        para_trimmer.itor_children = sentence

        self._number = number |nuco| Number()
        word_num_re = regex.compile(self._number.num_pat + r'|(?P<word>' + self._word_pat + r')', regex.DOTALL, sqs=list(unicode_single_quote_marks.values()))

        word_number = pawpaw.arborform.Extract(word_num_re)
        sentence.itor_children = word_number

        if chars:
            char = pawpaw.arborform.Extract(regex.compile(r'(?P<char>\w)', regex.DOTALL))
            word_number.itor_children = lambda ito: char if ito.desc == 'word' else None

        self.itor = paragraph

    @property
    def number(self) -> Number:
        return self._number

    def from_text(self, text: str) -> pawpaw.Ito:
        doc = pawpaw.Ito(text, desc='Document')
        doc.children.add(*self.itor.traverse(doc))
        return doc
