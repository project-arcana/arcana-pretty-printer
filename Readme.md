# Arcana Pretty Printer

Collection of debug pretty printer for arcana libraries

## QtCreator

In `QtCreator > Tools > Options > Debugger > Locals & Expressions > Extra Debugging Helpers`

Enter path to `qtcreator/printers.py`

### Implementation Notes

Based on [Qt Debugging Helpers](https://doc.qt.io/qtcreator/creator-debugging-helpers.html)

Note: "raw" gdb pretty printer don't work or at least not well with qtcreator, thus a separate implementation

The Qt debugger python api can be a bit obscure, but these resources helper:

* https://doc.qt.io/qtcreator/creator-debugging-helpers.html
* https://github.com/qt-creator/qt-creator/tree/master/share/qtcreator/debugger
* https://github.com/qt-creator/qt-creator/blob/master/share/qtcreator/debugger/dumper.py

## GDB

Example `~/.gdbinit`:

```
python
import sys
sys.path.insert(0, '/path/to/arcana-pretty-printer/')
from arcana.printers import register_arcana_printers
register_arcana_printers()
end
```
