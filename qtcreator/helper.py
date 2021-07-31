
from dumper import DumperBase, Children, SubItem, UnnamedSubItem
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
    s = to_str_preview_or_none(value)
    if s is None:
        return "{..}"
    return s


# looks for ways to interpret value as a string
# returns None if not possible
def try_get_string(value):
    s_data = value.findMemberByName("_data")
    if s_data is None:
        return None
    if s_data.type.code != TypeCode.Pointer:
        return None
    if s_data.type.target().name != "char":
        return None

    s_size = value.findMemberByName("_size")
    if s_size is None:
        return None
    if s_size.type.code != TypeCode.Integral:
        return None

    more = ""
    size = int(s_size)
    if size > 1000:
        size = 1000
        more = "..."
    mem = bytes(value.dumper.readRawMemory(s_data.pointer(), size)
                ).decode('utf-8').replace('"', '\\\\\\"')
    return '\\"' + mem + '\\"' + more


def to_str_preview_or_none(value):
    # TODO: might not recognize typedefs
    if isinstance(value, DumperBase.Value):
        if value.type is None:
            return None

        if value.type.code == TypeCode.Float:
            return "{:.3g}".format(float(value.floatingPoint()))

        if value.type.code == TypeCode.Struct:

            # "string protocol"
            s = try_get_string(value)
            if s is not None:
                return s

            return None

        if value.type.name == "char":
            c = int(value)
            if chr(c).isprintable():
                return "'{}'".format(chr(c)).replace('"', '\\"')
            return "char({})".format(c)

        return value.display().replace('"', '\\"')

    # primitive types
    if isinstance(value, float):
        return "{:.3g}".format(value)

    return str(value).replace('"', '\\"')


def add_computed_child(d, name, val, type="", encoding=None, children=[], childrenNames=[], iname=None):
    if isinstance(val, bool):
        val = "true" if val else "false"

    with UnnamedSubItem(d, iname if iname is not None else name):
        d.putField('iname', d.currentIName)
        d.putName(name)
        d.putNumChild(len(children))
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
    d.putValue(make_array_preview_str(size, innertype, (d.createValue(
        addrBase + i * innerSize, innertype) for i in range(size))))
    if d.isExpanded():
        with Children(d, size, innertype, None, 2000, addrBase=addrBase, addrStep=innerSize):
            for i in d.childRange():
                d.putSubItem(i, d.createValue(
                    addrBase + i * innerSize, innertype))
