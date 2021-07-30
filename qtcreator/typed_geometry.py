
# API Notes:
# - templateArgument(idx) is either int or type

from dumper import *

# ttype:
# "comp" for complike
# "mat" for matrices
# "obj" for objects


def prettify_tg_name(d, value, tname, ttype):
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
def tg_print_complike(d, value, tname, comps):
    dim = value.type.templateArgument(0)

    prettify_tg_name(d, value, tname, "comp")

    name = "("
    for i in range(dim):
        if i > 0:
            name += ", "
        name += value[comps[i]].display()
    name += ")"

    d.putValue(name.replace('"', '\\"'))
    d.putNumChild(dim)
    if d.isExpanded():
        with Children(d, dim):
            for i in range(dim):
                d.putSubItem(comps[i], value[comps[i]])


def qdump__tg__aabb(d, value):
    dim = value.type.templateArgument(0)

    prettify_tg_name(d, value, "aabb", "obj")

    comps = ["x", "y", "z", "w"]
    name = "("
    for i in range(dim):
        if i > 0:
            name += ", "
        name += value["min"][comps[i]].display()
        name += ".."
        name += value["max"][comps[i]].display()
    name += ")"

    d.putValue(name.replace('"', '\\"'))
    d.putNumChild(2)
    if d.isExpanded():
        with Children(d, 2):
            d.putSubItem("min", value["min"])
            d.putSubItem("max", value["max"])
            # TODO: size?


def qdump__tg__pos(d, value):
    tg_print_complike(d, value, "pos", ["x", "y", "z", "w"])


def qdump__tg__vec(d, value):
    tg_print_complike(d, value, "vec", ["x", "y", "z", "w"])


def qdump__tg__dir(d, value):
    tg_print_complike(d, value, "dir", ["x", "y", "z", "w"])


def qdump__tg__color(d, value):
    tg_print_complike(d, value, "color", ["r", "g", "b", "a"])
