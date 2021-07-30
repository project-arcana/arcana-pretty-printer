
import math
from dumper import Children, SubItem, UnnamedSubItem
from utils import DisplayFormat
from helper import *

# TODO:
# - box?
# - strided_span
# - experimental/ringbuffer
# - add allocator to alloc_xyz?


#
# container
#

def qdump__cc__span(d, value):
    show_arraylike_data(d, int(
        value["_size"]), value["_data"].pointer(), value.type.templateArgument(0))


def qdump__cc__vector(d, value):
    show_arraylike_data(d, int(
        value["_size"]), value["_data"].pointer(), value.type.templateArgument(0))


def qdump__cc__alloc_array(d, value):
    show_arraylike_data(d, int(
        value["_size"]), value["_data"].pointer(), value.type.templateArgument(0))


def qdump__cc__alloc_vector(d, value):
    show_arraylike_data(d, int(
        value["_size"]), value["_data"].pointer(), value.type.templateArgument(0))


def qdump__cc__array(d, value):
    if value.type.templateArgument(1) == 2 ** 64 - 1:
        show_arraylike_data(d, int(
            value["_size"]), value["_data"].pointer(), value.type.templateArgument(0))
    else:
        show_arraylike_data(d, value.type.templateArgument(
            1), value["_values"].address(), value.type.templateArgument(0))


def qdump__cc__capped_vector(d, value):
    if int(value.type.templateArgument(1)) == 0:
        d.putValue("0 x " + value.type.templateArgument(0).name)
        return

    show_arraylike_data(d, int(
        value["_size"]), value["_u"]["value"].address(), value.type.templateArgument(0))


def qdump__cc__pair(d, value):
    v0 = to_str_preview(value["first"])
    v1 = to_str_preview(value["second"])
    d.putValue("({}, {})".format(v0, v1))
    d.putPlainChildren(value)


def qdump__cc__tuple(d, value):
    targs = value.type.templateArguments()
    if len(targs) == 0:
        d.putValue("<empty tuple>")
        return

    c = value
    vals = []
    for i in range(len(targs)):
        c = c.members(True)[0]
        vals.append(c["value"])

    s = "("
    for v in vals:
        if len(s) > 1:
            s += ", "
        s += to_str_preview(v)
    s += ")"
    d.putValue(s)
    d.putNumChild(len(targs))
    if d.isExpanded():
        with Children(d, len(targs)):
            for i in range(len(targs)):
                d.putSubItem(i, vals[i])


def qdump__cc__optional(d, value):
    if not int(value["_has_value"]):
        d.putValue("<nullopt>")
        return
    d.putItem(value["_data"]["value"])


def qdump__cc__forward_list(d, value):
    innerType = value.type.templateArgument(0)

    pn = value["_first"]
    if int(pn) == 0:
        d.putValue("<empty>")
        return

    maxCountOuter = 99
    maxCountInner = 500

    vals = []
    more = False
    while int(pn) != 0:
        if len(vals) >= maxCountOuter:
            more = True
            break

        n = pn.dereference()
        vals.append(n["value"])
        pn = n["next"]

    d.putValue("{}{} x {}".format(
        len(vals), "+" if more else "", innerType.name))

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            pn = value["_first"]
            idx = 0
            while int(pn) != 0:
                if idx >= maxCountInner:
                    add_computed_child(d, "...", "...")
                    break

                n = pn.dereference()
                d.putSubItem(idx, n["value"])
                pn = n["next"]
                idx += 1


def qdump__cc__set(d, value):
    size = int(value["_size"])
    innerType = value.type.templateArgument(0)

    maxCnt = 500

    d.putValue("{" + "{} x {}".format(size, innerType.name) + "}")
    d.putNumChild(size)
    if d.isExpanded():
        with Children(d, size):
            isize = int(value["_entries"]["_size"])
            idata = value["_entries"]["_data"]
            idx = 0
            for i in range(isize):
                pn = idata[i]["_first"]
                while int(pn) != 0:
                    n = pn.dereference()
                    d.putSubItem(idx, n["value"])
                    idx += 1
                    if idx >= maxCnt:
                        add_computed_child(
                            d, "...", "+ {} more".format(size - idx))
                        break
                    pn = n["next"]

                if idx >= maxCnt:
                    break


def qdump__cc__map(d, value):
    size = int(value["_size"])
    keyType = value.type.templateArgument(0)
    valueType = value.type.templateArgument(1)

    maxCnt = 500

    d.putValue("{" + "{} x {} -> {}".format(size, keyType.name, valueType.name) + "}")
    d.putNumChild(size)
    if d.isExpanded():
        with Children(d, size):
            isize = int(value["_entries"]["_size"])
            idata = value["_entries"]["_data"]
            idx = 0
            for i in range(isize):
                pn = idata[i]["_first"]
                while int(pn) != 0:
                    n = pn.dereference()
                    iv = n["value"]
                    # d.putSubItem(to_str_preview(iv["key"]), n["value"])

                    e_key = iv["key"]
                    e_value = iv["value"]
                    s_key = to_str_preview_or_none(e_key)

                    # key has proper preview? only expand value
                    if s_key is not None:
                        with UnnamedSubItem(d, idx):
                            d.putName(s_key)
                            d.putField('iname', d.currentIName)
                            d.putItem(e_value)
                    # key is complex type? need to expand into key/value
                    else:
                        add_computed_child(d, "[{}]".format(idx), to_str_preview(
                            iv["value"]), children=[iv["key"], iv["value"]], childrenNames=["key", "value"], iname=idx)

                    idx += 1
                    if idx >= maxCnt:
                        add_computed_child(
                            d, "...", "+ {} more".format(size - idx))
                        break
                    pn = n["next"]

                if idx >= maxCnt:
                    break


#
# strings
#


def qdump__cc__sbo_string(d, value):
    sbo_size = value.type.templateArgument(0)
    if sbo_size == 15:
        d.putType("cc::string")
    d.putCharArrayValue(value["_data"].pointer(), int(
        value["_size"]), 1, displayFormat=DisplayFormat.Utf8String)


def qdump__cc__string_view(d, value):
    size = int(value["_size"])
    d.putCharArrayValue(value["_data"].pointer(), size,
                        1, displayFormat=DisplayFormat.Utf8String)


#
# smart pointer
#


def qdump__cc__unique_ptr(d, value):
    ptr = value["_ptr"]
    if int(ptr) == 0:
        d.putValue("<nullptr>")
        return

    d.putItem(ptr.dereference())


def qdump__cc__poly_unique_ptr(d, value):
    ptr = value["_ptr"]
    if int(ptr) == 0:
        d.putValue("<nullptr>")
        return

    d.putItem(ptr.dereference())


#
# flags
#


def qdump__cc__flags(d, value):
    v = int(value["_value"])
    enumDD = value.type.templateArgument(0).typeData().enumDisplay

    if v == 0:
        d.putValue("<no flags>")
        return

    flags = []
    idx = 0
    s = ""
    while v > 0:
        if v % 2 == 1:
            vs = str(idx) if enumDD is None else enumDD(
                idx, value.laddress, '%d')
            flags.append(vs)

            # compactify a bit
            if "::" in vs:
                vs = vs[vs.index("::")+2:]
            if " " in vs:
                vs = vs[:vs.index(" ")]

            if len(s) > 0:
                s += " | "
            s += vs
            v -= 1
        v /= 2
        idx += 1

    d.putValue(s)
    d.putNumChild(len(flags))
    if d.isExpanded():
        with Children(d, len(flags)):
            for i in range(len(flags)):
                add_computed_child(d, i, flags[i])
