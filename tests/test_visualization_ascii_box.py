import pawpaw
import pawpaw.visualization.ascii_box as box

from tests.util import _TestIto


class TestAsciiBoxDrawing(_TestIto):
    def test_chars_unique(self):
        chars = set(c.char for c in box.BoxDrawingChar._instances)
        self.assertEqual(len(box.BoxDrawingChar._instances), len(chars))

    def test_direction_styles_unique(self):
        dss = set(c.direction_styles for c in box.BoxDrawingChar._instances)
        self.assertEqual(len(box.BoxDrawingChar._instances), len(dss))

    @classmethod
    def is_corner(cls, bdc: box.BoxDrawingChar) -> bool:
        if len(bdc.direction_styles) != 2:
            return False

        dirs = tuple(ds.direction for ds in bdc.direction_styles)
        if dirs[0] == box.Direction.N:
            return dirs[1] in (box.Direction.W, box.Direction.E)
        elif dirs[1] == box.Direction.S:
            return dirs[0] in (box.Direction.W, box.Direction.E)
        else:
            return False

    def test_from_corners_single(self):
        for bdc in box.BoxDrawingChar.from_char('╭',),:  # box.BoxDrawingChar._instances:
            with self.subTest(box_drawing_char=bdc):
                if self.is_corner(bdc):
                    boxer = box.from_corners(bdc)
                else:
                    with self.assertRaises(ValueError):
                        boxer = box.from_corners(bdc)                   
