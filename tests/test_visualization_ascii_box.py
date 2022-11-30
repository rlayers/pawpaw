import pawpaw
import pawpaw.visualization.ascii_box as box

from tests.util import _TestIto


class TestAsciiBoxDrawing(_TestIto):
    def test_side_chars_all_present(self):
        chars = set()
        for orientation in box.Side.Orientation:
            print(f'Orientation: {orientation}')
            for count in box.Style.Count:
                for weight in box.Style.Weight:
                    style = box.Style(weight, count)
                    try:
                        side = box.Side(style)
                        c = side[orientation]
                        chars.add(c)
                    except:
                        pass

        expected = len(box.Side._characters)
        actual = len(chars)
        self.assertEqual(expected, actual)

    def test_corner_chars_all_present(self):
        chars = set()
        for orientation in box.Corner.Orientation:
            print(f'Orientation: {orientation}')
            for hcount in box.Style.Count:
                for hweight in box.Style.Weight:
                    hz_style = box.Style(hweight, hcount)
                    for vcount in box.Style.Count:
                        for vweight in box.Style.Weight:
                            vt_style = box.Style(vweight, vcount)
                            try:
                                corner = box.Corner(hz_style, vt_style)
                                c = corner[orientation]
                                chars.add(c)
                            except:
                                pass

        expected = len(box.Corner._characters)
        actual = len(chars)
        self.assertEqual(expected, actual)
