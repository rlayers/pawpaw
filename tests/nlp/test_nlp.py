import typing
from dataclasses import dataclass

import pawpaw
from tests.util import _TestIto, IntIto


class TestNumber(_TestIto):
    _valid_numbers = {
        'identity': '1',
        'with thousands sep': '1,234,567.89',
        'without thousands sep': '1234567.89',
        'abs zero': '-273.15',
        '\u2715': '3.1415926539',
        'Euler\'s': '2.7182818284',
        '\u221A2': '1.4142135623',
        '\u03C6': '1.6180339887',
        'electron': '1.602176634e-19',
        'Avogadro\'s': '6.02214076x10^23',
        'Plank\'s': '6.62607015E-34',
    }

    def test_num_valid(self):
        re = pawpaw.nlp.Number().re
        for name, s in self._valid_numbers.items():
            with self.subTest(name=name, string=s):
                self.assertTrue(re.fullmatch(s) is not None)

    def test_num_invalid(self):
        re = pawpaw.nlp.Number().re
        for s in '', ' ', 'abc', '1x2', 'two':
            with self.subTest(string=s):
                self.assertTrue(re.fullmatch(s) is None)

    def test_num_thousands_sep_valid(self):
        for sep in 'x', '#', '@':
            num = pawpaw.nlp.Number(thousands_sep=sep)
            vals = ['123', '456']
            val = sep.join(vals) + num.decimal_point + '789'
            with self.subTest(thousands_sep=sep, val=val):
                self.assertTrue(num.re.fullmatch(val) is not None)
                    
    def test_num_thousands_sep_invalid(self):
        for sep in None, '', ' ':
            with self.subTest(thousands_seps=sep):
                with self.assertRaises((ValueError, TypeError)):
                    pawpaw.nlp.Number(thousands_sep=sep)


class TestSentence(_TestIto):
    @dataclass
    class _TestData:
        description: str
        text: str
        expected: typing.List[str]

    def setUp(self) -> None:
        self.test_data: typing.List[TestSentence._TestData] = [
            TestSentence._TestData(
                'EOF',
                'Yes.',
                [
                    'Yes.',
                ]
            ),
            TestSentence._TestData(
                'Two whitespace',
                'The king was John I.  Henry was his son.',
                [
                    'The king was John I.',
                    'Henry was his son.',
                ]
            ),
            TestSentence._TestData(
                'Period (Full stop)',
                'Mary spake. Then John',
                [
                    'Mary spake.',
                    'Then John'
                ]
            ),
            TestSentence._TestData(
                'Question mark',
                'What day is it? Tuesday.',
                [
                    'What day is it?',
                    'Tuesday.',
                ]
            ),
            TestSentence._TestData(
                'Exclamation mark',
                'Wait! I want to come.',
                [
                    'Wait!',
                    'I want to come.',
                ]
            ),
            TestSentence._TestData(
                'Multiple EOS delimiters',
                'Wait... how can that be?!? Tell me!! Why is this so hard!?!',
                [
                    'Wait... how can that be?!?',
                    'Tell me!!',
                    'Why is this so hard!?!',
                ]
            ),
            TestSentence._TestData(
                'Sentence starts with number',
                'He lived a long life. 100 years approximately.',
                [
                    'He lived a long life.',
                    '100 years approximately.',
                ]
            ),
            TestSentence._TestData(
                'Number following numeric abbreviation.',
                'Hippocrates was born c. 460 bce.  See pp. 431 in your history book for details.',
                [
                    'Hippocrates was born c. 460 bce.',
                    'See pp. 431 in your history book for details.',
                ]
            ),
            TestSentence._TestData(
                'Numbers with decimals',
                'The plane landed 1.5 south of the airport; approximately 32.2540° N, 110.9742°.',
                [
                    'The plane landed 1.5 south of the airport; approximately 32.2540° N, 110.9742°.',
                ]
            ),
            TestSentence._TestData(
                'URLs',
                'https://github.com/rlayers/pawpaw is home to interesting software.',
                [
                    'https://github.com/rlayers/pawpaw is home to interesting software.',
                ]
            ),
            TestSentence._TestData(
                'Mid-sentence abbreviations',
                'Jane et. al. worked for Smith & Co. last year.',
                [
                    'Jane et. al. worked for Smith & Co. last year.',
                ]
            ),
            TestSentence._TestData(
                'Possessive abbreviations',
                'Martin Luther King Jr.\'s legacy endures.',
                [
                    'Martin Luther King Jr.\'s legacy endures.',
                ]
            ),         
            TestSentence._TestData(
                'Exclusion abbreviations.',
                'Dr. Francis, brother of Prof.\nMustard, and Brig. Gen. Adams hiked together near Mt. Rainer.',
                [
                    'Dr. Francis, brother of Prof.\nMustard, and Brig. Gen. Adams hiked together near Mt. Rainer.',
                ]
            ),
            TestSentence._TestData(
                'High frequency start words',
                'Ok, Mr. There is no Dr. What shall we do?',
                [
                    'Ok, Mr.',
                    'There is no Dr.',
                    'What shall we do?',
                ]
            ),
            TestSentence._TestData(
                'U.S. Government',
                'The U.S. Government decided against action.',
                [
                    'The U.S. Government decided against action.',
                ]
            ),            
        ]

    def test_all(self):
        sbd = pawpaw.arborform.Split(pawpaw.nlp.Sentence().re, non_boundary_desc='sentence')

        for td in self.test_data:
            with self.subTest(description=td.description, text=td.text):
                text = pawpaw.Ito(td.text)
                expected = [*pawpaw.Ito.from_substrings(text, *td.expected, desc='sentence')]
                actual = [*sbd(text)]
                self.assertListEqual(expected, actual)


class TestSimpleNlp(_TestIto):
    def test_from_text(self):
        nlp = pawpaw.nlp.SimpleNlp()
        for name, data in {
            'One sentence with one word': {
                'Yes':
                    {'Document': 1, 'paragraph': 1, 'sentence': 1, 'word': 1, 'number': 0}
            },

            'One BOM sentence with one word': {
                '\ufeffYes':
                    {'Document': 1, 'paragraph': 1, 'sentence': 1, 'word': 1, 'number': 0}
            },

            'One sentence with 5 words': {
                'Dick said, "Look, look up!"':
                    {'Document': 1, 'paragraph': 1, 'sentence': 1, 'word': 5, 'number': 0}
            },

            'One sentence with 6 words and 2 numbers': {
                'Does this sentence have 6 or 8 words?':
                    {'Document': 1, 'paragraph': 1, 'sentence': 1, 'word': 6, 'number': 2}

            },

            'Two sentences': {
                '\ufffeFather said, "I want something."  "Oh, Father," said Sally.':
                    {'Document': 1, 'paragraph': 1, 'sentence': 2, 'word': 9, 'number': 0}
            },

            'Two paragraphs': {
                '\tI am.  I was.\r\n\r\n\tI will be.\r\n\r\n':
                    {'Document': 1, 'paragraph': 2, 'sentence': 3, 'word': 7, 'number': 0}
            },

            'Moby Dick': {
                """Call me Ishmael. Some years ago — never mind how long precisely — having
                little or no money in my purse, and nothing particular to interest me on shore,
                I thought I would sail about a little and see the watery part of the world.""":
                    {'Document': 1, 'paragraph': 1, 'sentence': 2, 'word': 43, 'number': 0}
            },

            'Poe': {
                """Once upon a midnight dreary, while I pondered, weak and weary,
                Over many a quaint and curious volume of forgotten lore—
                While I nodded, nearly napping, suddenly there came a tapping,
                As of some one gently rapping, rapping at my chamber door.
                “’Tis some visitor,” I muttered, “tapping at my chamber door—
                Only this and nothing more.”""":
                    {'Document': 1, 'paragraph': 1, 'sentence': 2, 'word': 57, 'number': 0}
            }
        }.items():
            for text, counts in data.items():
                for desc, count in counts.items():
                    result = nlp.from_text(text)
                    with self.subTest(name=name, desc=desc):
                        if result.desc == desc:
                            actual = 0 if result is None else 1
                        else:
                            actual = sum(1 for i in result.find_all(f'**[d:{desc}]'))
                        self.assertEqual(count, actual)
