# Pretty printers for arcana-related libraries

import gdb


class FixedIntPrinter:
    """ prints tg::fixed_ints and uints """

    def __init__(self, val):
        self.val = val

    def to_string(self):
        return "DEBUG"

    def display_hint(self):
        return 'string'


def register_arcana_printers():
    "Register all supported arcana libs"

    print("[arcana] registering pretty printer")

    pp = gdb.printing.RegexpCollectionPrettyPrinter("project-arcana")

    # TODO: continue
    # pp.add_printer("tg fixed_ints", "^tg::.*", FixedIntPrinter)

    gdb.printing.register_pretty_printer(gdb.current_objfile(), pp, True)
