import sys
# Force Python XML parser, not faster C accelerators, because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import abc
import json
import io
import os
import typing
from xml.sax.saxutils import escape

import segments


class Dump(abc.ABC):
    def __init__(self, indent: str = '    ', substring: bool = True, value: bool = False):
        self.indent = indent
        self.substring = substring
        self.value = value
        self.linesep = os.linesep

    @abc.abstractmethod
    def _dump(self, fs: typing.IO, ei: segments.Types.C_EITO, level: int = 0) -> None:
        ...

    @abc.abstractmethod
    def dump(self, fs: typing.IO, *itos: segments.Types.C_ITO) -> None:
        ...
        
    def dumps(self, *itos: segments.Types.C_ITO) -> str:
        with io.StringIO() as fs:
            self.dump(fs, *itos)
            fs.seek(0)
            return fs.read()
        

class Compact(Dump):
    def __init__(self, indent: str = '    ', substring: bool = True, value: bool = False):
        super().__init__(indent, substring, value)
        
    def _dump(self, fs: typing.IO, ei: segments.Types.C_EITO, level: int = 0) -> None:
        fs.write(f'{self.indent * level}{ei.index:,}: .span={ei.ito.span} .desc="{ei.ito.desc}"')
        if self.substring:
            fs.write(f' .__str__(): "{ei.ito}"')
        fs.write(self.linesep)
        
        level += 1
        for eic in (segments.Types.C_EITO(i, ito) for i, ito in enumerate(ei.ito.children, start=1)):
            self._dump(fs, eic, level)

    def dump(self, fs: typing.IO, *itos: segments.Types.C_ITO) -> None:
        for ei in (segments.Types.C_EITO(i, ito) for i, ito in enumerate(itos, start=1)):
            self._dump(fs, ei)

                
class Xml(Dump):
    def __init__(self, indent: str = '    ', substring: bool = True, value: bool = False):
        super().__init__(indent, substring, value)
                
    def _dump(self, fs: typing.IO, ei: segments.Types.C_EITO, level: int = 0) -> None:
        fs.write(f'{level * self.indent}<ito')
        fs.write(f' start="{ei.ito.start}"')
        fs.write(f' stop="{ei.ito.stop}"')
        fs.write(f' desc="{escape(ei.ito.desc or "")}')
        fs.write(self.linesep)
        
        level += 1
        if self.substring:
            fs.write(f'{level * self.indent}<substring>{escape(str(ei.ito))}</substring>{self.linesep}')
        if self.value:
            fs.write(f'{level * self.indent}<value>{escape(str(ei.ito.value()))}</value>{self.linesep}')
        if len(ei.ito.children) > 0:
            fs.write(f'{level * self.indent}<children>{self.linesep}')
            
            level += 1
            for i, ito in enumerate(ei.ito.children):
                child = segments.Types.C_EITO(i, ito)
                self._dump(fs, child, level)
            
            level -= 1
            fs.write(f'{level * self.indent}</children>{self.linesep}')

        level -= 1
        fs.write(f'{level * self.indent}</ito>{self.linesep}')

    def dump(self, fs: typing.IO, *itos: segments.Types.C_ITO) -> None:
        fs.write(f'<?xml version="1.0" encoding="UTF-8" ?>{self.linesep}')
        fs.write(f'<itos>{self.linesep}')
        for ito in itos:
            self._dump(fs, segments.Types.C_EITO(0, ito), 1)
        fs.write(f'<itos>{self.linesep}')

                        
class Json(Dump):
    def __init__(self, indent: str = '    ', substring: bool = True, value: bool = False):
        super().__init__(indent, substring, value)
                
    def _dump(self, fs: typing.IO, ei: segments.Types.C_EITO, level: int = 0) -> None:
        fs.write(level * self.indent + '{' + self.linesep)
        
        level += 1
        fs.write(f'{level * self.indent}"start": {ei.ito.start},{self.linesep}')
        fs.write(f'{level * self.indent}"stop": {ei.ito.stop},{self.linesep}')
        fs.write(f'{level * self.indent}"desc": {"null" if ei.ito.desc is None else json.encoder.encode_basestring(ei.ito.desc)},{self.linesep}')
        if self.substring:
            fs.write(f'{level * self.indent}"substring": {json.encoder.encode_basestring(str(ei.ito))},{self.linesep}')
        if self.value:
            fs.write(f'{level * self.indent}"value": {json.encoder.encode_basestring(str(ei.ito.value()))}",{self.linesep}')
            
        fs.write(f'{level * self.indent}"children": [')
        if len(ei.ito.children) == 0:
            fs.write(f']{self.linesep}')
        else:
            fs.write(self.linesep)
            
            level += 1
            for i, ito in enumerate(ei.ito.children):
                child = segments.Types.C_EITO(i, ito)
                self._dump(fs, child, level)
                if i < len(ei.ito.children) - 1:
                    fs.write(',')
                fs.write(self.linesep)
                
            level -= 1
            fs.write(f'{level * self.indent}]{self.linesep}')

        level -= 1
        fs.write(level * self.indent + '}')
        
    def dump(self, fs: typing.IO, *itos: segments.Types.C_ITO) -> None:
        fs.write('{' + self.linesep)
        
        fs.write(f'{self.indent}"itos": [')
        
        comma_needed = False
        for ito in itos:
            if comma_needed:
                fs.write(',')
            fs.write(self.linesep)
            self._dump(fs, segments.Types.C_EITO(0, ito), 2)
            comma_needed = True
        fs.write(self.linesep)
        
        fs.write(self.indent + ']' + self.linesep)
        
        fs.write('}' + self.linesep)
