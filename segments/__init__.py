from segments._version import __version__
del _version

from segments.errors import Errors
del errors

from segments.span import Span
del span

from segments.ito import Ito, ChildItos
del ito

import segments.itorator
import segments.xml

del segments
