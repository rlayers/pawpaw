import itertools
import locale
import typing

import regex
import pawpaw
from pawpaw import nuco

# See https://www.unicode.org/Public/UNIDATA/NamesList.txt

unicode_controls = {
    'CHARACTER TABULATION': '\u0009',
    'LINE FEED':            '\u000A',
    'FORM FEED':            '\u000C',
    'CARRIAGE RETURN':      '\u000D',
}

unicode_white_spaces = {
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

    'ZERO WIDTH NO-BREAK SPACE':    '\uFEFF',
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


class SimpleNlp:
    _spaces_tab_line_feed = list(unicode_white_spaces.values())
    _spaces_tab_line_feed.append(unicode_controls['CHARACTER TABULATION'])
    _spaces_tab_line_feed.append(unicode_controls['LINE FEED'])

    _paragraph_pat = r'(?:\r?\n\L<s_t_lf>*){2,}'
    _paragraph_re = regex.compile(_paragraph_pat, regex.DOTALL, s_t_lf=_spaces_tab_line_feed)

    # Common abbreviations that are typically followed by a digit and/or uppercase letter as identifier
    _skip_abbrs_1 = [
        'c.',     # circa
        'ca.',    # circa
        'ed.',    # edition
        'illus.', # circa
        'no.',    # number
        'p.',     # page
        'pp.',    # pages
        'ver.',   # version
        'vol.',   # volume
    ]

    # Common abbreviations that are typically not sentence boundaries, even when followed by uppercase words
    _skip_abbrs_1 = [
        'Ald.',     # Alderman
        'Dr.',      # Doctor
        'ed.',      # editor
        'e.g.',     # exempli gratia
        'Fr.',      # Father
        'Gov.',     # Governor
        'Hon.',     # Honorable (sometimes Rt. Hon. for Right Honorable)
        'ibid.',    # ibidem
        'i.e.',     # ed est
        'illus.',   # illustrated by
        'Messrs.',  # plural of Mr.
        'Mr.',      # Mister
        'Mmes.',    # Missus
        'Mrs.',     # plural of Mrs.
        'Ms.',      # Miss
        'Msgr.',    # Monsignor  
        'pub.',     # published by / publisher
        'pseud.',   # pseudonym
        'Pres.',    # President
        'Prof.',    # Professor
        'qtd.',     # quoted in
        'Rep.',     # Representative
        'Rev.',     # Reverend
        'Sen.',     # Senator
        'St.',      # Saint
        'vis.',     # videlicet
        'vs.',      # versus
    ]

    # See: https://www.va.gov/vetsinworkplace/docs/em_rank.html

    _mil_officer_abbr = [
        # O1
        '2lc.',     # Second Lieutenant

        # O2
        '1lc.',     # First Lieutenant
        'Lt.',     # Lieutenant 

        # O3
        'Cpt.',    # Captain

        # O4
        'Maj.',    # Major

        # O5
        'Ltc.',    # Lieutenant Colonel

        # O6
        'Col.',    # Colonel

        # O7
        'Bg.',     # Brigadier General

        # O8
        'Mg.',     # Major General

        # O9
        'Ltg.',    # Lieutenant General

        # O10
        'Gen.',    # General
    ]

    _mil_enlisted_abbr = [
        # E1
        'Pvt.',   # Private

        # E2
        'pv2.',   # Private 2

        # E3
        'Pfc.',   # Private First Class

        # E3
        'Spc.',   # Specialist
        'Cpl.',   # Corporal

        # E5
        'Sgt.',   # Sergeant

        # E6
        'Ssg.',   # Staff Sergeant

        # E7
        'Sfc.',   # Sergeant First Class

        # E8
        'Msg.',   # Master Sergeant
        '1sg.',   # First Sergeant

        # E9
        'Sgm.',   # Sergeant Major
        'Csm.',   # Command Major
        'Sma.',   # Sergeant Major of the Army
    ]

    # sentence must end with a) period, b) elipses ('...' or '…'), or c) one or more '!' or '?', e.g. He said "What?!?"
    _sentence_terminator_pats = r'\.', r'\.{3,}', r'…', r'[\!\?]+'

    _sentence_suffix_chars = list(unicode_single_quote_marks.values())
    _sentence_suffix_chars.extend(unicode_double_quote_marks.values())
    _sentence_suffix_chars.extend(c for c in ')]}')

    _sentence_re = regex.compile(r'(?<=\w(?:' + '|'.join(_sentence_terminator_pats) + r')\L<s_suf_c>*)(?:\s{2,}|\s(?=$|[A-Z]))', regex.DOTALL, s_suf_c=_sentence_suffix_chars)

    _word_pat = r'\w(?:(?:\L<sqs>|-\s*)?\w)*'

    def __init__(self, number: Number | None = None, chars: bool = False):
        super().__init__()

        doc_trimmer = pawpaw.arborform.Wrap(lambda ito: [ito.str_strip(''.join(unicode_white_spaces.values()))])

        paragraph = pawpaw.arborform.Split(self._paragraph_re, desc='paragraph')
        doc_trimmer.itor_next = paragraph

        para_trimmer = pawpaw.arborform.Wrap(lambda ito: [ito.str_strip(''.join(unicode_white_spaces.values()))])
        paragraph.itor_next = para_trimmer

        sentence = pawpaw.arborform.Split(self._sentence_re, desc='sentence')
        paragraph.itor_children = sentence

        self._number = number |nuco| Number()
        word_num_re = regex.compile(self._number.num_pat + r'|(?P<word>' + self._word_pat + r')', regex.DOTALL, sqs=list(unicode_single_quote_marks.values()))

        word_number = pawpaw.arborform.Extract(word_num_re)
        sentence.itor_children = word_number

        if chars:
            char = pawpaw.arborform.Extract(regex.compile(r'(?P<char>\w)', regex.DOTALL))
            word_number.itor_children = lambda ito: char if ito.desc == 'word' else None

        self.itor = doc_trimmer

    @property
    def number(self) -> Number:
        return self._number

    def from_text(self, text: str) -> pawpaw.Ito:
        doc = pawpaw.Ito(text, desc='Document')
        doc.children.add(*self.itor.traverse(doc))
        return doc
