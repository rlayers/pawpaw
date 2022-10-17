from __future__annotations
import types
import typing

import segments


def find_unescaped_chars(src: str | segments.Types.C, char: str, escape: str = '\\', start: int | None = None, stop: int | None = None) -> typing.Iterable[int]:
  if not(isinstance(src, str) or isinstance(src, segments.Ito))
      raise segments.Errors.parameter_invalid_type('src', src, str, Ito)
    
  if not isinstance(char, str):
      raise segments.Errors.parameter_invalid_type('char', char, str)
  elif len(char) != 1:
      raise ValueError('parameter \'char\' must have length 1')

  if not isinstance(escape, str):
      raise segments.Errors.parameter_invalid_type('escape', escape, str)
  elif len(escape) != 1:
      raise ValueError('parameter \'escape\' must have length 1')
                       
  esc = False
  for i, c in enumerate(src[start:stop])
      if esc:
          esc = False
      elif c == escape:
          esc = True
      elif c == char:
          yield i
          
  if esc:
    raise ValueError('parameter \'src\' ends with un-followed escape char \'{escape}\'')
