import json
import pickle

from pawpaw import Ito, __version__
from tests.util import _TestIto


class TestItoSerialization(_TestIto):
    def setUp(self) -> None:
        super().setUp()

        s = 'See Jack run.'
        self.h_ito = Ito(s, desc='Phrase')
        self.h_ito.children.add(*self.h_ito.str_split())
        for c in self.h_ito.children:
            c.desc = 'Word'
            self.add_chars_as_children(c, 'Char')

    #region pickling

    def test_pickle_serialize(self):
        word = self.h_ito.find('**[d:Word]')
        pickle_data = pickle.dumps(word)
        self.assertLess(0, len(pickle_data))
      
    def test_pickle_deserialize(self):
        w_orig = self.h_ito.find('**[d:Word]')
        pickle_data = pickle.dumps(w_orig)
        w_deser = pickle.loads(pickle_data)
        self.assertEqual(w_orig, w_deser)

    #endregion

    #region JSON

    def test_json_serialize(self):
        word = self.h_ito.find('**[d:Word]')
        indent = ' ' * 4
        js_data = json.dumps(word, cls=Ito.JsonEncoder, stringless=False, full_tree=False, indent=indent)
        expected = {
            '__type__': Ito.JsonEncoder()._js_type_value,
            '__version__': __version__,
            'string': word.string,
            'path': '.',
            'ito': {
                'span': list(word.span),
                'desc': word.desc
            }
        }
        expected = json.dumps(expected, indent=indent)
        self.assertEqual(expected, js_data)

    def test_json_deserialize(self):
        w_orig = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(w_orig, cls=Ito.JsonEncoder, stringless=False, full_tree=False)

        w_deser = json.loads(js_data, object_hook=Ito.JsonDecoderHook())
        self.assertIsNot(w_orig, w_deser)
        self.assertEqual(w_orig, w_deser)
        self.assertEqual(0, len(w_deser.children))

    def test_json_serialize_stringless(self):
        word = self.h_ito.find('**[d:Word]')
        indent = ' ' * 4
        js_data = json.dumps(word, cls=Ito.JsonEncoder, stringless=True, full_tree=False, indent=indent)
        expected = {
            '__type__': Ito.JsonEncoder()._js_type_value,
            '__version__': __version__,
            'path': '.',
            'ito': {
                'span': list(word.span),
                'desc': word.desc
            }
        }
        expected = json.dumps(expected, indent=indent)
        self.assertEqual(expected, js_data)

    def test_json_deserialize_stringless(self):
        w_orig = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(w_orig, cls=Ito.JsonEncoder, stringless=True, full_tree=False)

        with self.subTest(string_parameter_supplied=False):
            with self.assertRaises(ValueError):
                w_deser = json.loads(js_data, object_hook=Ito.JsonDecoderHook())

        with self.subTest(string_parameter_supplied=True):
            w_deser = json.loads(js_data, object_hook=Ito.JsonDecoderHook(string=self.h_ito.string))
            self.assertIsNot(w_orig, w_deser)
            self.assertEqual(w_orig, w_deser)
            self.assertEqual(0, len(w_deser.children))

    def test_json_serialize_full_tree(self):
        word = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(word, cls=Ito.JsonEncoder, stringless=False, full_tree=True)
        prefix = {
            '__type__': Ito.JsonEncoder()._js_type_value,
            '__version__': __version__,
            'string': word.string,
            'path': word.path,
            'ito': {
                'span': list(self.h_ito.span),
                'desc': self.h_ito.desc
            }
        }
        prefix = json.dumps(prefix)
        prefix = prefix[:-2]
        prefix += ', "children": [{'
        self.assertTrue(js_data.startswith(prefix))

    def test_json_deserialize_full_tree(self):
        w_orig = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(w_orig, cls=Ito.JsonEncoder, stringless=False, full_tree=True)

        w_deser = json.loads(js_data, object_hook=Ito.JsonDecoderHook())
        self.assertIsNot(w_orig, w_deser)
        self.assertEqual(w_orig, w_deser)

        w_deser_root = w_deser.find('....')
        self.assertIsNotNone(w_deser_root)
        self.assertIsNot(self.h_ito, w_deser_root)
        self.assertEqual(self.h_ito, w_deser_root)

        self.assertSequenceEqual([*self.h_ito.walk_descendants()], [*w_deser_root.walk_descendants()])

    def test_json_serialize_stringless_full_tree(self):
        word = self.h_ito.find('**[d:Word]')
        indent = ' ' * 4
        js_data = json.dumps(word, cls=Ito.JsonEncoder, stringless=True, full_tree=True)
        prefix = {
            '__type__': Ito.JsonEncoder()._js_type_value,
            '__version__': __version__,
            'path': word.path,
            'ito': {
                'span': list(self.h_ito.span),
                'desc': self.h_ito.desc
            }
        }
        prefix = json.dumps(prefix)
        prefix = prefix[:-2]
        prefix += ', "children": [{'
        self.assertTrue(js_data.startswith(prefix))

    def test_json_deserialize_stringless_full_tree(self):
        w_orig = self.h_ito.find('**[d:Word]')
        js_data = json.dumps(w_orig, cls=Ito.JsonEncoder, stringless=True, full_tree=True)

        with self.subTest(string_parameter_supplied=False):
            with self.assertRaises(ValueError):
                w_deser = json.loads(js_data, object_hook=Ito.JsonDecoderHook())

        with self.subTest(string_parameter_supplied=True):
            w_deser = json.loads(js_data, object_hook=Ito.JsonDecoderHook(string=self.h_ito.string))
            self.assertIsNot(w_orig, w_deser)
            self.assertEqual(w_orig, w_deser)

            w_deser_root = w_deser.find('....')
            self.assertIsNotNone(w_deser_root)
            self.assertIsNot(self.h_ito, w_deser_root)
            self.assertEqual(self.h_ito, w_deser_root)

            self.assertSequenceEqual([*self.h_ito.walk_descendants()], [*w_deser_root.walk_descendants()])

    #endregion
