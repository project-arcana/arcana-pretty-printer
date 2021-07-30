
# API Notes:
# - templateArgument(idx) is either int or type

from dumper import *
from utils import TypeCode


def prettify_tg_name(d, value, tname, ttype):
    # ttype:
    # "comp" for complike
    # "mat" for matrices
    # "obj" for objects

    t = value.type
    dim = value.type.templateArgument(0)
    comptype = t.templateArgument(1).name

    # typedeffed name
    shortname = None
    if comptype == "int":
        shortname = "i"
    elif comptype == "float":
        shortname = ""
    elif comptype == "double":
        shortname = "d"
    elif comptype == "uint":
        shortname = "u"

    if shortname != None:
        d.putType("tg::{}{}{}".format(shortname, tname, dim))


def is_arithmetic_type(t):
    if t is None:
        return False

    if t.code == TypeCode.Float:
        return True
    if t.code == TypeCode.Integral:
        return True

    return False


def arithmetic_value(value):
    if value.type.code == TypeCode.Float:
        return float(value.floatingPoint())
    if value.type.code == TypeCode.Integral:
        return int(value)


# mainly calls value.display(), but for floats it will make "shorter" version
def to_str_preview(value):
    # TODO: might not recognize typedefs
    if isinstance(value, DumperBase.Value):
        if value.type is not None and value.type.code == TypeCode.Float:
            return "{:.3g}".format(float(value.floatingPoint()))

        return value.display()

    # primitive types
    if isinstance(value, float):
        return "{:.3g}".format(value)

    return str(value)


# e.g. tname is "pos" and comps is ["x", "y", "z", "w"]
def tg_print_complike(d, value, tname, comps):
    dim = value.type.templateArgument(0)

    prettify_tg_name(d, value, tname, "comp")

    name = "("
    for i in range(dim):
        if i > 0:
            name += ", "
        name += to_str_preview(value[comps[i]])
    name += ")"

    d.putValue(name.replace('"', '\\"'))
    d.putNumChild(dim)
    if d.isExpanded():
        with Children(d, dim):
            for i in range(dim):
                d.putSubItem(comps[i], value[comps[i]])


def qdump__tg__aabb(d, value):
    dim = value.type.templateArgument(0)
    comptype = value.type.templateArgument(1)

    prettify_tg_name(d, value, "aabb", "obj")

    comps = ["x", "y", "z", "w"]
    name = "("
    for i in range(dim):
        if i > 0:
            name += ", "
        name += to_str_preview(value["min"][comps[i]])
        name += ".."
        name += to_str_preview(value["max"][comps[i]])
    name += ")"

    numChilds = 2
    if is_arithmetic_type(comptype):
        numChilds += 1

    d.putValue(name.replace('"', '\\"'))
    d.putNumChild(numChilds)
    if d.isExpanded():
        with Children(d, numChilds):
            d.putSubItem("min", value["min"])
            d.putSubItem("max", value["max"])

            if is_arithmetic_type(comptype):
                sname = "("
                for i in range(dim):
                    if i > 0:
                        sname += ", "
                    vmin = arithmetic_value(value["min"][comps[i]])
                    vmax = arithmetic_value(value["max"][comps[i]])
                    sname += to_str_preview(vmax - vmin)
                sname += ")"
                with SubItem(d, "size"):
                    d.putNumChild(dim)
                    d.putName("size")
                    d.putValue(sname)
                    d.putType("")
                    if d.isExpanded():
                        with Children(d, dim):
                            for i in range(dim):
                                vmin = arithmetic_value(value["min"][comps[i]])
                                vmax = arithmetic_value(value["max"][comps[i]])
                                with SubItem(d, comps[i]):
                                    d.putNumChild(0)
                                    d.putName(comps[i])
                                    d.putValue(str(vmax - vmin))
                                    d.putType(comptype)


def qdump__tg__pos(d, value):
    tg_print_complike(d, value, "pos", ["x", "y", "z", "w"])


def qdump__tg__vec(d, value):
    tg_print_complike(d, value, "vec", ["x", "y", "z", "w"])


def qdump__tg__dir(d, value):
    tg_print_complike(d, value, "dir", ["x", "y", "z", "w"])


def qdump__tg__color(d, value):
    tg_print_complike(d, value, "color", ["r", "g", "b", "a"])
