from abc import ABC, abstractmethod, abstractproperty
import locale
import typing

import regex
import pawpaw

# See https://www.unicode.org/Public/UNIDATA/NamesList.txt

byte_order_controls = {
    'Big-endian byte order mark': '\uFEFF',  # "UTF-16BE"
    'Little-endian byte order mark': '\uFFFE',  # "UTF-16LE"
}

unicode_white_space_eol = {
    'LINE FEED': '\u000A',
    'NEXT LINE': '\u0085',
    'LINE SEPARATOR': '\u2028',
    'PARAGRAPH SEPARATOR': '\u2029',
}

unicode_white_space_other = {
    'CHARACTER TABULATION': '\u0009',
    'FORM FEED': '\u000C',
    'CARRIAGE RETURN': '\u000D',
    'SPACE': '\u0020',
    'NO-BREAK SPACE': '\u00A0',

    'EN QUAD': '\u2000',
    'EM QUAD': '\u2001',
    'EN SPACE': '\u2002',
    'EM SPACE': '\u2003',
    'THREE-PER-EM SPACE': '\u2004',
    'FOUR-PER-EM SPACE': '\u2005',
    'SIX-PER-EM SPACE': '\u2006',
    'FIGURE SPACE': '\u2007',
    'PUNCTUATION SPACE': '\u2008',
    'THIN SPACE': '\u2009',
    'HAIR SPACE': '\u200A',
    'ZERO WIDTH SPACE': '\u200B',

    'NARROW NO-BREAK SPACE': '\u202F',

    'MEDIUM MATHEMATICAL SPACE': '\u205F',

    'IDEOGRAPHIC SPACE': '\u3000',
}

unicode_single_quote_marks = {
    'APOSTROPHE': '\u0027',
    'GRAVE ACCENT': '\u0060',
    'ACUTE ACCENT': '\u00B4',

    'LEFT SINGLE QUOTATION MARK': '\u2018',
    'RIGHT SINGLE QUOTATION MARK': '\u2019',

    'SINGLE LOW-9 QUOTATION MARK': '\u201A',
    'SINGLE HIGH-REVERSED-9 QUOTATION MARK': '\u201B',

    'HEAVY SINGLE TURNED COMMA QUOTATION MARK ORNAMENT': '\u275B',
    'HEAVY SINGLE COMMA QUOTATION MARK ORNAMENT': '\u275C',

    'HEAVY LOW SINGLE COMMA QUOTATION MARK ORNAMENT': '\u275F',
}

unicode_double_quote_marks = {
    'QUOTATION MARK': '\u0022',

    'LEFT DOUBLE QUOTATION MARK': '\u201C',
    'RIGHT DOUBLE QUOTATION MARK': '\u201D',

    'DOUBLE LOW-9 QUOTATION MARK': '\u201E',
    'DOUBLE HIGH-REVERSED-9 QUOTATION MARK': '\u201F',

    'HEAVY DOUBLE TURNED COMMA QUOTATION MARK ORNAMENT': '\u275D',
    'HEAVY DOUBLE COMMA QUOTATION MARK ORNAMENT': '\u275E',

    'HEAVY LOW DOUBLE COMMA QUOTATION MARK ORNAMENT': '\u2760',
}

unicode_bullets = {
    'BULLET': '\u2022',  # •
    'TRIANGULAR BULLET': '\u2023',  # ‣
    'HYPHEN BULLET': '\u2043',  # ⁃
    'BLACK LEFTWARDS BULLET': '\u204C',  # ⁌
    'BLACK RIGHTWARDS BULLET': '\u204D',  # ⁍
    'BULLET OPERATOR': '\u2219',  # ∙
    'BLACK VERY SMALL SQUARE': '\u2B1D',  # ⬝
    'BLACK SMALL SQUARE aka SQUARE BULLET': '\u25AA',  # ▪
    'FISHEYE aka tainome': '\u25C9',  # ◉
    'INVERSE BULLET': '\u25D8',  # ◘
    'WHITE BULLET': '\u25E6',  # ◦
    'REVERSED ROTATED FLORAL HEART BULLET': '\u2619',  # ☙
}


def to_re_char_set(chars: typing.Iterable[str] | dict[str, str], inclusive: bool = True) -> str:
    if isinstance(chars, dict):
        chars = list(chars.values())
    elif not pawpaw._type_magic.isinstance_ex(chars, typing.Iterable[str]):
        raise pawpaw.Errors.parameter_invalid_type('chars', chars, typing.Iterable)
    return f'[{"" if inclusive else "^"}{regex.escape("".join(chars))}]'


trimmable_ws = list(byte_order_controls.values())
trimmable_ws.extend(unicode_white_space_eol.values())
trimmable_ws.extend(unicode_white_space_other.values())


class NlpComponent(ABC):
    @abstractproperty
    @property
    def re(self) -> regex.Pattern:
        ...

    @abstractmethod
    def get_itor(self) -> pawpaw.arborform.Itorator:
        ...


class Number(NlpComponent):
    _sign_pat = r'(?P<sign>[-+])'
    _sci_exp_e_notation_pat = r'[Ee]' + _sign_pat + r'?\d+'
    _sci_exp_x10_notation_pat = r' ?[Xx\u2715] ?10\^ ?' + _sign_pat + r'?\d+'
    _sci_exp_pat = r'(?P<exponent>' + '|'.join([_sci_exp_e_notation_pat, _sci_exp_x10_notation_pat]) + r')'

    def build_integer_pat(self) -> str:
        rv = r'(?P<integer>\d{1,3}(?:' + regex.escape(self.thousands_sep) + r'\d{3})+'
        if self.thousands_sep_optional:
            rv += r'|\d+'
        rv += r')'
        return rv

    def build_decimal_pat(self) -> str:
        return r'(?P<decimal>' + regex.escape(self.decimal_point) + r'\d+)'

    def build_num_pat_re(self) -> tuple[str, regex.Pattern]:
        num_pat = f'(?P<number>{self._sign_pat}?' \
                  f'(?:{self._int_pat}{self._decimal_pat}?' \
                  f'|{self._decimal_pat})' \
                  f'{self._sci_exp_pat}?)'
        re = regex.compile(num_pat, regex.DOTALL)
        return num_pat, re

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
        self._int_pat: str = self.build_integer_pat()
        self._decimal_pat: str = self.build_decimal_pat()
        self._num_pat: str
        self._re: regex.Pattern
        self._num_pat, self._re = self.build_num_pat_re()

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
    
    # endregion

    def get_itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Split(
            pawpaw.arborform.Extract(self._re),
            boundary_retention=pawpaw.arborform.Split.BoundaryRetention.ALL,
            tag='number splitter'
        )


class KeyedPrefix:
    """
    Lists, legal documents, etc.

    Some ideas:

        \d.\d...\d.?    :
        \d-\d-...\d     :
        §{1,2}          :  Section (Silcrow) : "16 U.S.C. § 580(p)",  "§§ 13–21"
        [A-Z]{1,2}      :
        [MDCLXVI]+      : Latin numerals (could be case insensitive - but should all be same case)

    """

    # \d+[sepchar]    : 1) 2. 3] 4:
    __int_pat = r'(?<key>\d+)[\)\]\.\-:]'

    # \d.\d...\d.?
    # \d-\d-...\d
    __compound_int_pat = r'(?<key>\d+(?:[\.\-]\d+)+)\.?'

    _key_prefix_pat = r'(?:' + '|'.join((__compound_int_pat, __int_pat)) + r')[ \t]+'


class KeyedList(NlpComponent):
    def __init__(self, min_keys: int = 2):
        self._separators: list[str] = list(unicode_white_space_eol.values())
        self._min_keys: int = min_keys
        self._re: regex.Pattern = self._build_re()

    def _build_re(self) -> regex.Pattern:
        return regex.compile(
            rf'(?:\L<line_seps>{to_re_char_set(unicode_white_space_other)}*)+',
            regex.DOTALL,
            line_seps=self._separators)

    @property
    def separators(self) -> list[str]:
        return list(self._separators)

    @separators.setter
    def separators(self, val: typing.Iterable[str]):
        if pawpaw._type_magic.isinstance_ex(val, typing.Iterable[str]):
            self._separators = list[val]
            self._re = self._build_re()
        else:
            raise pawpaw.Errors.parameter_invalid_type('val', val, typing.Iterable[str])

    @property
    def min_keys(self) -> int:
        return self._min_keys

    @min_keys.setter
    def min_keys(self, val: int):
        if isinstance(val, int):
            self._min_keys = val
            self._re = self._build_re()
        else:
            raise pawpaw.Errors.parameter_invalid_type('val', val, int)

    @property
    def re(self) -> regex.Pattern:
        return self._re

    def _as_list(self, ito: pawpaw.Ito) -> pawpaw.Types.C_IT_ITOS:
        line_splitter = pawpaw.arborform.Split(self._re, return_zero_split=False, desc='line')
        lines = [*line_splitter(ito)]

        key_prefixes = [
            r'(?<key>(?:\d{1,2}|[A-Z]{1,2}))[\)\]\.\-:]\s+(?<value>.+)',
            r'(?<key>\d+(?:[\.\-]\d+)+)[\.:]?\s+(?<value>.+)',
        ]
        for kp in key_prefixes:
            kvs = [kv for line in lines for kv in pawpaw.Ito.from_re(kp, line, limit=1) if kv.start == line.start]
            if len(kvs) >= self._min_keys:
                # Also check ordering
                rv = pawpaw.Ito.join(*kvs, desc='list')
                rv.children.add(*kvs)
                return (rv,)

        return tuple()

    def get_itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Itorator.wrap(self._as_list, tag='list finder')


class Paragraph(NlpComponent):
    def __init__(self, min_separators: int = 2):
        self._separators: list[str] = list(unicode_white_space_eol.values())
        self._min_separators: int = min_separators
        self._re: regex.Pattern = self._build_re()

    def _build_re(self) -> regex.Pattern:
        return regex.compile(rf'(?:{to_re_char_set(unicode_white_space_other)}*\L<para_seps>){{{self._min_separators},}}', regex.DOTALL, para_seps=self._separators)

    @property
    def separators(self) -> list[str]:
        return list(self._separators)

    @separators.setter
    def separators(self, val: typing.Iterable[str]):
        if pawpaw._type_magic.isinstance_ex(val, typing.Iterable[str]):
            self._separators = list[val]
            self._re = self._build_re()
        else:
            raise pawpaw.Errors.parameter_invalid_type('val', val, typing.Iterable[str])

    @property
    def min_separators(self) -> int:
        return self._min_separators

    @min_separators.setter
    def min_separators(self, val: int):
        if isinstance(val, int):
            self._min_separators = val
            self._re = self._build_re()
        else:
            raise pawpaw.Errors.parameter_invalid_type('val', val, int)

    @property
    def re(self) -> regex.Pattern:
        return self._re

    def get_itor(self) -> pawpaw.arborform.Itorator:
        ws_trimmer = pawpaw.arborform.Itorator.wrap(
            lambda ito: [ito.str_strip(''.join(trimmable_ws))],
            tag='para trimmer'
        )

        para_splitter = pawpaw.arborform.Split(self._re, desc='paragraph', tag='para splitter')
        con = pawpaw.arborform.Connectors.Recurse(para_splitter)
        ws_trimmer.connections.append(con)

        return ws_trimmer


class Sentence(NlpComponent):
    _prefix_chars = list(unicode_single_quote_marks.values())
    _prefix_chars.extend(unicode_double_quote_marks.values())
    _prefix_chars.extend(c for c in '([{')

    _terminators = [
        r'\.',  # Full stop
        r'\.{3,}',  # Ellipses; three periods
        r'…',  # Ellipses char
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
        'c.',  # circa
        'ca.',  # circa
        'ed.',  # edition
        'illus.',  # circa
        'no.',  # number
        'p.',  # page
        'pp.',  # pages
        'ver.',  # version
        'vol.',  # volume
    ]

    # Common abbrs that are typically not sentence boundaries, even when followed by uppercase
    _ignore_abbrs = [
        'Ald.',  # Alderman
        'Asst.',  # Assistent
        'Dr.',  # Doctor
        'Drs.',  # Doctors
        'ed.',  # editor
        'e.g.',  # exempli gratia
        'Fr.',  # Father
        'Gov.',  # Governor
        'Hon.',  # Honorable (sometimes Rt. Hon. for Right Honorable)
        'ibid.',  # ibidem
        'i.e.',  # ed est
        'illus.',  # illustrated by
        'Insp.',  # Inspector
        'Messrs.',  # plural of Mr.
        'Mlle.',  # Mademoiselle
        'Mmes.',  # Missus
        'Mr.',  # Mister
        'Mrs.',  # plural of Mrs.
        'Ms.',  # Miss
        'Msgr.',  # Monsignor
        'Mt.',  # Mount / Mountain
        'pub.',  # published by / publisher
        'pseud.',  # pseudonym
        'Pres.',  # President
        'Prof.',  # Professor
        'qtd.',  # quoted in
        'Rep.',  # Representative
        'Reps.',  # Representatives
        'Rev.',  # Reverend
        'Sen.',  # Senator
        'Sens.',  # Senators
        'St.',  # Saint
        'vis.',  # videlicet
        'v.',  # versus
        'vs.',  # versus
    ]

    # Military officer abbrs: see https://pavilion.dinfos.edu/Article/Article/2205094/military-rank-abbreviations/
    _mil_officer_abbrs = [
        'Lt.',  # Lieutenant
        'Capt.',  # Captain
        'Cpt.',  # Captain
        'Maj.',  # Major
        'Cmdr.',  # Commander
        'Col.',  # Colonel
        'Brig.',  # Brigadier (as in Brigadier General)
        'Gen.',  # General
        'Adm.',  # Admiral
    ]

    # Military enlisted abbrs: see https://pavilion.dinfos.edu/Article/Article/2205094/military-rank-abbreviations/
    _mil_enlisted_abbrs = [
        'Pvt.',  # Private
        'Pfc.',  # Private First Class
        'Spc.',  # Specialist
        'Cpl.',  # Corporal
        'Sgt.',  # Sergeant
    ]

    _ignores = _ignore_abbrs
    _ignores.extend(_mil_officer_abbrs)
    _ignores.extend(_mil_enlisted_abbrs)

    _sen_ws = ['\r\n', '\n']
    _sen_ws.extend(unicode_white_space_other.values())

    _exceptions = [
        r'(?<!\L<ignores>)',  # Ignores
        r'(?<!\L<num_abbrs>(?=\L<sen_ws>\d))',  # Numeric abbr followed by a digit
        r'(?<![A-Z][a-z]+\L<sen_ws>[A-Z]\.(?=\L<sen_ws>[A-Z][a-z]+))',  # Common human name pattern
        r'(?<!U\.S\.(?=\L<sen_ws>Government))',  # "U.S. Government"
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

    def get_itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Split(Sentence().re, desc='sentence', tag='sentence')


class SimpleNlp:
    _word_pat = r'\w(?:(?:\L<sqs>|-\s*)?\w)*'

    def __init__(self, number: Number | None = Number(), chars: bool = False):
        super().__init__()

        paragraph = Paragraph().get_itor()

        sentence = Sentence().get_itor()
        con = pawpaw.arborform.Connectors.Children.Add(sentence)
        paragraph.connections.append(con)

        itor_num = number.get_itor()
        con = pawpaw.arborform.Connectors.Children.Add(itor_num)
        sentence.connections.append(con)

        word = pawpaw.arborform.Extract(
            regex.compile(r'(?P<word>' + self._word_pat + r')', regex.DOTALL, sqs=list(unicode_single_quote_marks.values()))
        )
        con = pawpaw.arborform.Connectors.Delegate(word, lambda ito: ito.desc is None)
        itor_num.connections.append(con)

        if chars:
            char = pawpaw.arborform.Extract(regex.compile(r'(?P<char>\w)', regex.DOTALL))
            con = pawpaw.arborform.Connectors.Children.Add(char)
            itor_num.connections.append(con)

        self.itor = paragraph

    @property
    def number(self) -> Number:
        return self._number

    def from_text(self, text: str) -> pawpaw.Ito:
        doc = pawpaw.Ito(text, desc='Document')
        doc.children.add(*self.itor(doc))
        return doc
