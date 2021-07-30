# Arcana Pretty Printer

Collection of debug pretty printer for arcana libraries

## QtCreator

In `QtCreator > Tools > Options > Debugger > Locals & Expressions > Extra Debugging Helpers`

Enter path to `qtcreator/printers.py`

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
