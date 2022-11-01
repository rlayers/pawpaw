import enum
import locale
import typing

import regex
import segments
from segments import nuco



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
    def thousands_sep(self) -> str:
        if not isinstance(thousands_sep, str):
            raise segments.Errors.parameter_invalid_type('thousands_sep', thousands_sep, str)
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

    # endregion


class SimpleNlp:
    _eol_pat = '\r?\n'

    _paragraph_pat = r'(?:' + _eol_pat + r'){2,}\s*'
    _paragraph_re = regex.compile(_paragraph_pat, regex.DOTALL)

    _sentence_terminator_pats = r'\.', r'\.{3}', r'\!+', r'\?'
    _sentence_suffix_chars = '\'"[]()'
    _sentence_suffix_pat = r'[' + ''.join(regex.escape(c) for c in _sentence_suffix_chars) + r']'
    _sentence_re = regex.compile(r'(?<=\s*(?:' + '|'.join(_sentence_terminator_pats) + r')' + _sentence_suffix_pat + r'*)(?:\s+)', regex.DOTALL)

    _apostrophes = r'\'‛‵′’\u2018\u2018\u2019'
    _apostrophe_pat = r'[' + '|'.join(regex.escape(c) for c in _apostrophes) + r']'

    _word_pat = r'\w(?:(?:' + _apostrophe_pat + r'|-\s*)?\w)*'

    def __init__(self, number: Number | None = None, chars: bool = False):
        super().__init__()

        doc_trimmer = segments.itorator.Wrap(lambda ito: [ito.str_strip()])

        paragraph = segments.itorator.Split(self._paragraph_re, desc='Paragraph')
        doc_trimmer.itor_next = paragraph

        para_trimmer = segments.itorator.Wrap(lambda ito: [ito.str_strip()])
        paragraph.itor_next = para_trimmer

        sentence = segments.itorator.Split(self._sentence_re, desc='Sentence')
        paragraph.itor_children = sentence

        self._number = number |nuco| Number()
        word_num_re = regex.compile(r'(?P<Number>' + self._number.num_pat + r')|(?P<Word>' + self._word_pat + r')', regex.DOTALL)

        word_number = segments.itorator.Extract(word_num_re)
        sentence.itor_children = word_number

        if chars:
            char = segments.itorator.Extract(regex.compile(r'(?P<Character>\w)', regex.DOTALL))
            word_number.itor_children = lambda ito: char if ito.desc == 'Word' else None

        self.itor = doc_trimmer

    @property
    def number(self) -> Number:
        return self._number

    def from_text(self, text: str) -> segments.Ito:
        doc = segments.Ito(text, desc='Document')
        doc.children.add(*self.itor.traverse(doc))
        return doc
