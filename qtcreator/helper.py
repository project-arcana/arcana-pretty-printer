
from dumper import DumperBase, Children, SubItem
from utils import TypeCode


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
# NOTE: currently unable to provide previews of structs due to qt's arch
# NOTE: ensures that all " are escaped
def to_str_preview(value):
    # TODO: might not recognize typedefs
    if isinstance(value, DumperBase.Value):
        if value.type is None:
            return "??"

        if value.type.code == TypeCode.Float:
            return "{:.3g}".format(float(value.floatingPoint()))

        if value.type.code == TypeCode.Struct:
            return "??"

        return value.display().replace('"', '\\"')

    # primitive types
    if isinstance(value, float):
        return "{:.3g}".format(value)

    return str(value).replace('"', '\\"')


def add_computed_child(d, name, val, type="", encoding=None, children=[], childrenNames=[]):
    with SubItem(d, name):
        d.putNumChild(len(children))
        d.putName(name)
        d.putValue(str(val), encoding=encoding)
        d.putType(type)
        if d.isExpanded() and len(children) > 0:
            with Children(d, len(children)):
                if len(childrenNames) > 0:
                    for n, v in zip(childrenNames, children):
                        d.putSubItem(n, v)
                else:
                    for i in range(len(children)):
                        d.putSubItem(i, children[i])


def make_array_preview_str(count, type, value_gen):
    if not isinstance(type, str):
        type = type.name

    txt = "{} x {}: [".format(count, type)
    try:
        i = 0
        for v in value_gen:
            s = to_str_preview(v)
            if len(txt) + len(s) > 30:
                txt += "..."
                break
            if i > 0:
                txt += ", "
            txt += s
            i += 1
    except:
        txt += "<error>"
    txt += "]"
    return txt


def show_arraylike_data(d, size, data_ptr, innertype):
    innerSize = innertype.size()
    addrBase = data_ptr

    d.putNumChild(size)
    d.putValue(make_array_preview_str(size, innertype, [d.createValue(
        addrBase + i * innerSize, innertype) for i in range(size)]))
    if d.isExpanded():
        with Children(d, size, innertype, None, 2000, addrBase=addrBase, addrStep=innerSize):
            for i in d.childRange():
                d.putSubItem(i, d.createValue(
                    addrBase + i * innerSize, innertype))
