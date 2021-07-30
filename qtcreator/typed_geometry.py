
# API Notes:
# - templateArgument(idx) is either int or type

import math
from dumper import Children, SubItem
from helper import *


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


# e.g. tname is "pos" and comps is ["x", "y", "z", "w"]
def tg_print_complike(d, value, tname, comps, compute_length=False):
    dim = value.type.templateArgument(0)
    comptype = value.type.templateArgument(1)

    prettify_tg_name(d, value, tname, "comp")

    name = "("
    for i in range(dim):
        if i > 0:
            name += ", "
        name += to_str_preview(value[comps[i]])
    name += ")"

    if not is_arithmetic_type(comptype):
        compute_length = False

    numChilds = dim
    if compute_length:
        numChilds += 1

    d.putValue(name)
    d.putNumChild(numChilds)
    if d.isExpanded():
        with Children(d, numChilds):
            for i in range(dim):
                d.putSubItem(comps[i], value[comps[i]])
            if compute_length:
                s = 0.0
                for i in range(dim):
                    dd = arithmetic_value(value[comps[i]])
                    s += dd * dd
                add_computed_child(d, "length", "{:.4g}".format(s ** 0.5))


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

    d.putValue(name)
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
                                add_computed_child(
                                    d, comps[i], vmax - vmin, comptype)


def qdump__tg__pos(d, value):
    tg_print_complike(d, value, "pos", ["x", "y", "z", "w"])


def qdump__tg__vec(d, value):
    tg_print_complike(d, value, "vec", [
                      "x", "y", "z", "w"], compute_length=True)


def qdump__tg__dir(d, value):
    tg_print_complike(d, value, "dir", ["x", "y", "z", "w"])


def qdump__tg__size(d, value):
    tg_print_complike(d, value, "size", ["width", "height", "depth", "w"])


def qdump__tg__color(d, value):
    tg_print_complike(d, value, "color", ["r", "g", "b", "a"])


def qdump__tg__span(d, value):
    show_arraylike_data(d, int(
        value["_size"]), value["_data"].pointer(), value.type.templateArgument(0))


def qdump__tg__array(d, value):
    show_arraylike_data(d, value.type.templateArgument(
        1), value["_values"].address(), value.type.templateArgument(0))


def qdump__tg__angle_t(d, value):
    t = value.type.templateArgument(0)

    s = str(value["angle_in_radians"].display()) + " rad"
    if is_arithmetic_type(t):
        s = "{:.3g} deg".format(arithmetic_value(
            value["angle_in_radians"]) * 360.0 / math.pi)

    d.putValue(s)
    d.putPlainChildren(value)


def show_fixed_int_uint(d, value, words, signed):
    d.putType("tg::{}{}".format("i" if signed else "u", words * 64))

    val = 0
    for i in range(words):
        val += int(value["d"][i]) * (2 ** (i * 64))
    
    if signed and val >= 2 ** (words * 64 - 1):
        val -= 2 ** (words * 64)

    d.putValue(str(val))

    d.putNumChild(words)
    if d.isExpanded():
        with Children(d, words):
            for i in reversed(range(words)):
                v = int(value["d"][i])
                add_computed_child(d, "w" + str(i), "hex: {:0>16x}".format(v), "u64")


def qdump__tg__fixed_int(d, value):
    show_fixed_int_uint(d, value, value.type.templateArgument(0), True)


def qdump__tg__fixed_uint(d, value):
    show_fixed_int_uint(d, value, value.type.templateArgument(0), False)
