import typing

import pawpaw
import pawpaw.visualization.ascii_box as box
from tests.util import _TestIto

directions: typing.List[box.Direction] = [
    box.Direction.N,
    box.Direction.NE,
    box.Direction.E,
    box.Direction.SE,
    box.Direction.S,
    box.Direction.SW,
    box.Direction.W,
    box.Direction.NW,
]

class TestDirection(_TestIto):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directions = directions

    def test_values(self):
        for i, d in enumerate(self.directions):
            with self.subTest(direction=d):
                self.assertEqual(i * 45, d.value)

    def test_from_degrees(self):
        for direction in self.directions:
            for degrees in -720, -360, 0, 1, 44, 360, 720:
                with self.subTest(direction=direction, degrees=degrees):
                    self.assertEqual(direction, direction.rotate(degrees))

            for degrees in -1, 45:
                with self.subTest(direction=direction, degrees=degrees):
                    self.assertNotEqual(direction, direction.rotate(degrees))

    def test_rotate(self):
        for i, direction in enumerate(self.directions):
            for degrees in range(0, 360 + 45, 45):
                with self.subTest(direction=direction, degrees=degrees):
                    self.assertEqual(
                        box.Direction.from_degrees(direction.value + degrees),
                        direction.rotate(degrees)
                    )

    def test_reflect(self):
        for direction in self.directions:
            for surface in direction, direction.rotate(180):
                with self.subTest(direction=direction, surface=surface):
                    self.assertEqual(direction, direction.reflect(surface))

            for surface in direction.rotate(90), direction.rotate(-90):
                with self.subTest(direction=direction, surface=surface):
                    self.assertEqual(direction.rotate(180), direction.reflect(surface))

            for delta in 45, -45:
                surface = direction.rotate(delta)
                with self.subTest(direction=direction, surface=surface):
                    rot = 90 if delta > 0 else -90
                    self.assertEqual(direction.rotate(rot), direction.reflect(surface))

            for delta in 135, -135:
                surface = direction.rotate(delta)
                with self.subTest(direction=direction, surface=surface):
                    rot = -90 if delta > 0 else 90
                    self.assertEqual(direction.rotate(rot), direction.reflect(surface))


class TestAsciiBoxDrawing(_TestIto):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directions = directions

        rotations = [
            ['┃', '━', '┃', '━'],
            ['┍', '┒', '┙', '┖'],
            ['┡', '┲', '┪', '┹'],
            ['╔', '╗', '╝', '╚'],
        ]
        cls.ninety_degree_rotatations: typing.List[typing.List[box.BoxDrawingChar]] = [
            [box.BoxDrawingChar.from_char(c) for c in rots] for rots in rotations
        ]

    def test_chars_unique(self):
        chars = set(c.char for c in box.BoxDrawingChar._instances)
        self.assertEqual(len(box.BoxDrawingChar._instances), len(chars))

    def test_direction_styles_unique(self):
        dss = set(frozenset((ds.direction, ds.style.weight, ds.style.count, ds.style.dash, ds.style.path) for ds in c.direction_styles) for c in box.BoxDrawingChar._instances)
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

    def test_rotate(self):
        for rots in self.ninety_degree_rotatations:
            for i, bdc in enumerate(rots):
                with self.subTest(box_drawing_char=bdc):
                    j = (i + 1) % 4
                    self.assertEqual(rots[j], bdc.rotate(90))
