import sys
# Force Python XML parser, not faster C accelerators, because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import abc
import json
import io
import os
import typing
from xml.sax.saxutils import escape as xml_escape

import pawpaw
from pawpaw.visualization import ascii_box_drawing


Repr = typing.Callable[[str], str]


class Pepo:
    def __init__(self, indent: str = '    ', children: bool = True):
        self.linesep: str = os.linesep
        self.indent: str = indent
        self.children = children


    @abc.abstractmethod
    def dump(self, fs: typing.IO, *itos: pawpaw.Types.C_ITO) -> None:
        ...

    def dumps(self, *itos: pawpaw.Types.C_ITO) -> str:
        with io.StringIO() as fs:
            self.dump(fs, *itos)
            fs.seek(0)
            return fs.read()


class _PepoFstr(Pepo):
    def __init__(self, indent: str = '    ', children: bool = True, fstr: str = '%desc'):
        super().__init__(indent, children)
        self.fstr = fstr


class Compact(_PepoFstr):
    def __init__(self, indent: str = '    ', children: bool = True):
        super().__init__(indent, children, '%span \'%desc\' : \'%substr:40…\'')
        self.children = children

    def _dump(self, fs: typing.IO, ei: pawpaw.Types.C_EITO, level: int = 0) -> None:
        fs.write(f'{self.indent * level}{ei.index:,}: {ei.ito:{self.fstr}}{self.linesep}')

        if self.children:
            level += 1
            for eic in (pawpaw.Types.C_EITO(i, ito) for i, ito in enumerate(ei.ito.children, start=1)):
                self._dump(fs, eic, level)

    def dump(self, fs: typing.IO, *itos: pawpaw.Types.C_ITO) -> None:
        for ei in (pawpaw.Types.C_EITO(i, ito) for i, ito in enumerate(itos, start=1)):
            self._dump(fs, ei)


class Tree(_PepoFstr):
    HORZ = ascii_box_drawing.Lines.Horizontal.SINGLE_LIGHT
    VERT = ascii_box_drawing.Lines.Vertical.SINGLE_LIGHT
    TEE = '├'
    ELBOW = ascii_box_drawing.Corners.SW.HZ_LIGHT_VT_LIGHT

    def __init__(self, indent: str = '  ', children: bool = True):
        super().__init__(indent, children, '%span \'%desc\' : \'%substr:40…\'')
        self.children = False

    def _dump_children(self, fs: typing.IO, ito: pawpaw.Types.C_ITO, prefix: str = '') -> None:
        for child in ito.children[:-1]:
            fs.write(f'{prefix}'
                     f'{self.TEE}'
                     f'{self.HORZ * len(self.indent)}'
                     f'{child:{self.fstr}}'
                     f'{self.linesep}')
            self._dump_children(fs, child, prefix + f'{self.VERT}{self.indent}')

        if len(ito.children) > 0:
            fs.write(f'{prefix}'
                     f'{self.ELBOW}'
                     f'{self.HORZ * len(self.indent)}'
                     f'{ito.children[-1]:{self.fstr}}'
                     f'{self.linesep}')
            self._dump_children(fs, child, prefix + f' {self.indent}')

    def dump(self, fs: typing.IO, *itos: pawpaw.Types.C_ITO) -> None:
        for ito in itos:
            fs.write(f'{ito:{self.fstr}}{self.linesep}')
            self._dump_children(fs, ito)


class Xml(Pepo):
    def __init__(self, indent: str = '    ', children: bool = True):
        super().__init__(indent, children)

    def _dump(self, fs: typing.IO, ei: pawpaw.Types.C_EITO, level: int = 0) -> None:
        fs.write(f'{level * self.indent}<ito')
        fs.write(f' start="{ei.ito.start}"')
        fs.write(f' stop="{ei.ito.stop}"')
        fs.write(f' desc="{xml_escape(ei.ito.desc or "")}">')
        fs.write(self.linesep)

        fs.write(f'{level * self.indent}<substring>')
        fs.write(xml_escape(str(ei.ito)))
        fs.write(f'</substring>{self.linesep}')
        if self.children and len(ei.ito.children) > 0:
            fs.write(f'{level * self.indent}<children>{self.linesep}')

            level += 1
            for i, ito in enumerate(ei.ito.children):
                child = pawpaw.Types.C_EITO(i, ito)
                self._dump(fs, child, level)

            level -= 1
            fs.write(f'{level * self.indent}</children>{self.linesep}')

        level -= 1
        fs.write(f'{level * self.indent}</ito>{self.linesep}')

    def dump(self, fs: typing.IO, *itos: pawpaw.Types.C_ITO) -> None:
        fs.write(f'<?xml version="1.0" encoding="UTF-8" ?>{self.linesep}')
        fs.write(f'<itos>{self.linesep}')
        for ito in itos:
            self._dump(fs, pawpaw.Types.C_EITO(0, ito), 1)
        fs.write(f'<itos>{self.linesep}')


class Json(Pepo):
    def __init__(self, indent: str = '    ', children: bool = True):
        super().__init__(indent, children)

    def _dump(self, fs: typing.IO, ei: pawpaw.Types.C_EITO, level: int = 0) -> None:
        fs.write(level * self.indent + '{' + self.linesep)

        level += 1
        fs.write(f'{level * self.indent}"start": {ei.ito.start},{self.linesep}')
        fs.write(f'{level * self.indent}"stop": {ei.ito.stop},{self.linesep}')
        if ei.ito.desc == None:
            desc = "null"
        else:
            desc = json.encoder.encode_basestring(ei.ito.desc)
        fs.write(f'{level * self.indent}"desc": {desc},{self.linesep}')
        substr = json.encoder.encode_basestring(str(ei.ito))
        fs.write(f'{level * self.indent}"substr": {substr},{self.linesep}')
        if self.children:
            fs.write(f'{level * self.indent}"children": [')
            if len(ei.ito.children) == 0:
                fs.write(f']{self.linesep}')
            else:
                fs.write(self.linesep)

                level += 1
                for i, ito in enumerate(ei.ito.children):
                    child = pawpaw.Types.C_EITO(i, ito)
                    self._dump(fs, child, level)
                    if i < len(ei.ito.children) - 1:
                        fs.write(',')
                    fs.write(self.linesep)

                level -= 1
                fs.write(f'{level * self.indent}]{self.linesep}')

        level -= 1
        fs.write(level * self.indent + '}')

    def dump(self, fs: typing.IO, *itos: pawpaw.Types.C_ITO) -> None:
        fs.write('{' + self.linesep)

        fs.write(f'{self.indent}"itos": [')

        comma_needed = False
        for ito in itos:
            if comma_needed:
                fs.write(',')
            fs.write(self.linesep)
            self._dump(fs, pawpaw.Types.C_EITO(0, ito), 2)
            comma_needed = True
        fs.write(self.linesep)

        fs.write(self.indent + ']' + self.linesep)

        fs.write('}' + self.linesep)
