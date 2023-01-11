import pawpaw
import pawpaw.visualization.ascii_box as box

from tests.util import _TestIto


class TestAsciiBoxDrawing(_TestIto):
    def test_chars_unique(self):
        chars = set(c.char for c in box.BoxDrawingChar._instances)
        self.assertEqual(len(box.BoxDrawingChar._instances), len(chars))

    def test_direction_styles_unique(self):
        dss = set((ds.direction, ds.style.weight, ds.style.count, ds.style.dash, ds.style.path) for c in box.BoxDrawingChar._instances for ds in c.direction_styles)
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

    def test_from_corners_single_valid(self):
        for bdc in box.BoxDrawingChar.from_char('╭',),:  # box.BoxDrawingChar._instances:
            with self.subTest(box_drawing_char=bdc):
                if self.is_corner(bdc):
                    boxer = box.from_corners(bdc.char)
                    boxer = box.from_corners(bdc)
                else:
                    with self.assertRaises(ValueError):
                        boxer = box.from_corners(bdc.char)
                    with self.assertRaises(ValueError):
                        boxer = box.from_corners(bdc)

    def test_corner_combos(self):
        in_outs = (
            (('╔', '╯'), ('╔', '╕', '╙', '╯')),
            (('╚', '╮'), ('╓', '╮', '╚', '╛'))
        )

        for ins, output_corners in in_outs:
            for input_corners in ins, ins[::-1]:
                with self.subTest(input_corners=input_corners):
                    input_corners = [box.BoxDrawingChar.from_char(c) for c in input_corners]
                    boxer = box.from_corners(*input_corners)
                    lines = list(boxer.from_srcs(' '))
                    self.assertEqual(3, len(lines))
                    self.assertEqual(output_corners[0], lines[0][0])
                    self.assertEqual(output_corners[1], lines[0][-1])
                    self.assertEqual(output_corners[2], lines[-1][0])
                    self.assertEqual(output_corners[3], lines[-1][-1])
