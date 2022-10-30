import enum
import locale
import typing

import regex
import segments
from segments import nuco



class Number:
    _sign_pat = r'(?<sign>[-+])'
    _integer_pat = r'(?<integer>\d{1,3}(?:[,\.]\d{3})*)'
    _decimal_pat = r'(?<decimal>[,\.]\d+)'
    _sci_exp_e_notation_pat = r'[Ee]' + _sign_pat + r'?\d+'
    _sci_exp_x10_notation_pat = r' ?[Xx\u2715] ?10\^ ?' + _sign_pat + r'?\d+'
    _sci_exp_pat = r'(?<exponent>' + '|'.join([_sci_exp_e_notation_pat, _sci_exp_x10_notation_pat]) + r')'

    @property
    def integer_pat(self) -> str:
        seps = list(filter(lambda ts: ts != '', regex.escape(self.thousands_seps)))
        if len(seps) > 0:
            ts = f'[{"|".join(seps)}]'
            if '' in self.thousands_seps:
                ts += '?'
        else:
            ts = ''
        return r'(?<integer>\d{1,3}(?:' + ts + r'\d{3})*)'

    @property
    def decimal_pat(self) -> str:
        return r'(?<decimal>' + regex.escape(self.decimal_point) + r'\d+)'

    def __init__(self, decimal_point: str | None = None, thousands_seps: typing.Set[str] = {''}):
        lc_dict = locale.localeconv()
        self.decimal_point = decimal_point |nuco| lc_dict['decimal_point']
        self.thousands_seps = thousands_seps

        self._num_pat = f'{self._sign_pat}?' \
            f'(?:{self.integer_pat}{self.decimal_pat}?' \
            f'|{self.decimal_pat})' \
            f'{self._sci_exp_pat}?'

        self._re = regex.compile(self._num_pat, regex.DOTALL)

    @property
    def num_pat(self) -> str:
        return self._num_pat

    @property
    def re(self) -> regex.Pattern:
        return self._re


class SimpleNlp:
    _paragraph_re = regex.compile(r'(?:\r?\n){2,}', regex.DOTALL)
    _sentence_re = regex.compile(r'(?<=\s*(?:[\.\?\!][\'"]?|\.{3}))(?:\s+)', regex.DOTALL)

    _apostrophe_pat = r'[' + '|'.join(("'", '‛', '‵', '′', '’', '\u2018', '\u2018\u2019')) + r']'
    _word_pat = r'\w(?:(?:' + _apostrophe_pat + r'|-\s*)?\w)*'

    def __init__(self, number: Number | None = None, chars: bool = False):
        super().__init__()

        trimmer = segments.itorator.Wrap(lambda ito: [ito.str_strip()])

        paragraph = segments.itorator.Split(self._paragraph_re, desc='Paragraph')
        trimmer.itor_children = paragraph

        sentence = segments.itorator.Split(self._sentence_re, desc='Sentence')
        paragraph.itor_children = sentence

        self._number = number |nuco| Number()
        word_num_re = regex.compile(r'(?P<Number>' + self._number.num_pat + r')|(?P<Word>' + self._word_pat + r')', regex.DOTALL)

        word_number = segments.itorator.Extract(word_num_re)
        sentence.itor_children = word_number

        if chars:
            char = segments.itorator.Extract(regex.compile(r'(?P<Character>\w)', regex.DOTALL))
            word_number.itor_children = lambda ito: char if ito.desc == 'Word' else None

        self.itor = trimmer

    @property
    def number(self) -> Number:
        return self._number

    def from_text(self, text: str) -> segments.Ito:
        doc = segments.Ito(text, desc='Document')
        doc.children.add(*self.itor.traverse(doc))
        return doc
