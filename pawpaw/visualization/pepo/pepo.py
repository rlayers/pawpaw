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


Repr = typing.Callable[[str], str]


class Dumpstr:
    def __init__(self, limit: int = 40, abbr_suffix: str = '...', repr_: Repr = str.__repr__):
        self.limit = limit
        self.abbr_suffix = abbr_suffix
        self.repr_ = repr_

    def dump(self, fs: typing.IO, val: typing.Any) -> None:
        basis = self.repr_(str(val))
        if self.limit >= 0 and len(basis) <= self.limit:
            fs.write(f'{basis}')
        else:
            stop = max(0, self.limit - len(self.abbr_suffix))
            fs.write(f'{basis[:stop] + self.abbr_suffix}')


class Pepo(abc.ABC):
    def __init__(self, indent: str = '    ', substr: Dumpstr | None = Dumpstr(), value: Dumpstr | None = None):
        self.linesep: str = os.linesep
        self.indent: str = indent
        self.substr: Dumpstr | None = substr
        self.value: Dumpstr | None = value
        self.children: bool = True

    @abc.abstractmethod
    def _dump(self, fs: typing.IO, ei: pawpaw.Types.C_EITO, level: int = 0) -> None:
        ...

    @abc.abstractmethod
    def dump(self, fs: typing.IO, *itos: pawpaw.Types.C_ITO) -> None:
        ...

    def dumps(self, *itos: pawpaw.Types.C_ITO) -> str:
        with io.StringIO() as fs:
            self.dump(fs, *itos)
            fs.seek(0)
            return fs.read()


class Compact(Pepo):
    def __init__(self, indent: str = '    ', children: bool = True):
        super().__init__(indent)
        self.children = children

    def _dump(self, fs: typing.IO, ei: pawpaw.Types.C_EITO, level: int = 0) -> None:
        fs.write(f'{self.indent * level}{ei.index:,}:')
        fs.write(f' .span={tuple(ei.ito.span)}')
        fs.write(f' .desc="{ei.ito.desc}"')
        if self.substr is not None:
            fs.write(f' : "')
            self.substr.dump(fs, ei.ito)
            fs.write(f'"')
        if self.value is not None:
            fs.write(f' : .value()="')
            self.value.dump(fs, ei.ito.value())
            fs.write(f'"')
        fs.write(self.linesep)
        
        if self.children:
            level += 1
            for eic in (pawpaw.Types.C_EITO(i, ito) for i, ito in enumerate(ei.ito.children, start=1)):
                self._dump(fs, eic, level)

    def dump(self, fs: typing.IO, *itos: pawpaw.Types.C_ITO) -> None:
        for ei in (pawpaw.Types.C_EITO(i, ito) for i, ito in enumerate(itos, start=1)):
            self._dump(fs, ei)   

                
class Xml(Pepo):
    def __init__(self, indent: str = '    ', substr=Dumpstr(repr_=xml_escape)):
        super().__init__(indent, substr=substr)
                
    def _dump(self, fs: typing.IO, ei: pawpaw.Types.C_EITO, level: int = 0) -> None:
        fs.write(f'{level * self.indent}<ito')
        fs.write(f' start="{ei.ito.start}"')
        fs.write(f' stop="{ei.ito.stop}"')
        fs.write(f' desc="{xml_escape(ei.ito.desc or "")}">')
        fs.write(self.linesep)
        
        level += 1
        if self.substr is not None:
            fs.write(f'{level * self.indent}<substring>')
            self.substr.dump(fs, ei.ito)
            fs.write(f'</substring>{self.linesep}')
        if self.value is not None:
            fs.write(f'{level * self.indent}<value>')
            self.value.dump(fs, ei.ito.value())
            fs.write(f'</value>{self.linesep}')
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
    def __init__(self, indent: str = '    ', substr=Dumpstr(repr_=lambda s: json.encode.encode_basestring(s).strip('"'))):
        super().__init__(indent, substr=substr)
                
    def _dump(self, fs: typing.IO, ei: pawpaw.Types.C_EITO, level: int = 0) -> None:
        fs.write(level * self.indent + '{' + self.linesep)
        
        level += 1
        fs.write(f'{level * self.indent}"start": {ei.ito.start},{self.linesep}')
        fs.write(f'{level * self.indent}"stop": {ei.ito.stop},{self.linesep}')
        fs.write(f'{level * self.indent}"desc": {"null" if ei.ito.desc is None else json.encoder.encode_basestring(ei.ito.desc)},{self.linesep}')
        if self.substr is not None:
            fs.write(f'{level * self.indent}"substring": "')
            self.substr.dump(fs, ei.ito)
            fs.write(f'"{self.linesep}')
        if self.value is not None:
            fs.write(f'{level * self.indent}"value": "')
            self.value.dump(fs, ei.ito.value())
            fs.write(f'"{self.linesep}')
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
