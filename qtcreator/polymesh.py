
import sys
import math
from dumper import Children, SubItem
from helper import *


type_vertex_handle = None
type_face_handle = None
type_edge_handle = None
type_halfedge_handle = None


def make_vertex_handle(d, idx, mesh):
    global type_vertex_handle

    mesh = int(mesh)
    idx = int(idx)

    if type_vertex_handle is None:
        type_vertex_handle = d.createType("polymesh::vertex_handle")

    # TODO: 32bit version?
    data = mesh.to_bytes(8, sys.byteorder) + \
        idx.to_bytes(4, sys.byteorder, signed=True)

    return d.createValue(data, type_vertex_handle)


def make_face_handle(d, idx, mesh):
    global type_face_handle

    mesh = int(mesh)
    idx = int(idx)

    if type_face_handle is None:
        type_face_handle = d.createType("polymesh::face_handle")

    # TODO: 32bit version?
    data = mesh.to_bytes(8, sys.byteorder) + \
        idx.to_bytes(4, sys.byteorder, signed=True)

    return d.createValue(data, type_face_handle)


def make_edge_handle(d, idx, mesh):
    global type_edge_handle

    mesh = int(mesh)
    idx = int(idx)

    if type_edge_handle is None:
        type_edge_handle = d.createType("polymesh::edge_handle")

    # TODO: 32bit version?
    data = mesh.to_bytes(8, sys.byteorder) + \
        idx.to_bytes(4, sys.byteorder, signed=True)

    return d.createValue(data, type_edge_handle)


def make_halfedge_handle(d, idx, mesh):
    global type_halfedge_handle

    mesh = int(mesh)
    idx = int(idx)

    if type_halfedge_handle is None:
        type_halfedge_handle = d.createType("polymesh::halfedge_handle")

    # TODO: 32bit version?
    data = mesh.to_bytes(8, sys.byteorder) + \
        idx.to_bytes(4, sys.byteorder, signed=True)

    return d.createValue(data, type_halfedge_handle)


def make_count_str(allcnt, remcnt, singular_name, plural_name):
    if remcnt == 0:
        return "{} {}".format(
            allcnt, singular_name if allcnt == 1 else plural_name)
    else:
        return "{} {} (+ {} removed)".format(
            allcnt - remcnt, singular_name if allcnt - remcnt == 1 else plural_name, remcnt)


def qdump__polymesh__Mesh(d, value):
    d.putType("pm::Mesh")
    vcnt = int(value["mVerticesSize"])
    hcnt = int(value["mHalfedgesSize"])
    fcnt = int(value["mFacesSize"])
    ecnt = hcnt // 2

    vrcnt = int(value["mRemovedVertices"])
    hrcnt = int(value["mRemovedHalfedges"])
    frcnt = int(value["mRemovedFaces"])
    ercnt = hrcnt // 2

    mptr = value.address()

    d.putValue("Mesh: {} V, {} E, {} F{}".format(
        vcnt - vrcnt,
        ecnt - ercnt,
        fcnt - frcnt,
        "" if int(value["mCompact"]) else ", non-compact"
    ))

    maxCount = 1000

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            add_computed_child(d, "compact", "true" if int(
                value["mCompact"]) else "false", "bool")

            def show_collection(sname, pname, pcnt, prcnt, make_handle):
                with SubItem(d, pname):
                    d.putValue(make_count_str(pcnt, prcnt, sname, pname))
                    d.putType("pm::{}_collection".format(sname))

                    d.putNumChild(pcnt - prcnt)
                    if d.isExpanded():
                        with Children(d):
                            for i in range(pcnt):
                                if i >= maxCount:
                                    add_computed_child(
                                        d, "...", "+ {} more".format(pcnt - prcnt - maxCount))
                                    break
                                d.putSubItem(i, make_handle(d, i, mptr))

            show_collection("vertex", "vertices", vcnt,
                            vrcnt, make_vertex_handle)
            show_collection("edge", "edges", ecnt,
                            ercnt, make_edge_handle)
            show_collection("halfedge", "halfedges", hcnt,
                            hrcnt, make_halfedge_handle)
            show_collection("face", "faces", fcnt,
                            frcnt, make_face_handle)

            # TODO: computed values like "has boundary", "genus", "byte size", etc. that require mesh iteration


def qdump__polymesh__vertex_index(d, value):
    d.putType("pm::vertex_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid vertex>")
        return

    d.putValue("vertex {}".format(v))


def qdump__polymesh__edge_index(d, value):
    d.putType("pm::edge_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid edge>")
        return

    d.putValue("edge {}".format(v))


def qdump__polymesh__halfedge_index(d, value):
    d.putType("pm::halfedge_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid halfedge>")
        return

    d.putValue("halfedge {}".format(v))


def qdump__polymesh__face_index(d, value):
    d.putType("pm::face_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid face>")
        return

    d.putValue("face {}".format(v))


def qdump__polymesh__vertex_handle(d, value):
    d.putType("pm::vertex_handle")
    idx = int(value["idx"]["value"])
    if idx < 0:
        d.putValue("<invalid vertex>")
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            mod = " (null mesh)"
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mVerticesSize"])
            if idx >= pcnt:
                mod = " (out of bounds)"
            else:
                oh = int(mesh["mVertexToOutgoingHalfedge"]
                         ["ptr"][idx]["value"])
                if oh == -2:
                    mod = " (removed)"
        d.putValue("vertex {}".format(idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("idx", value["idx"])
            d.putSubItem("mesh", value["mesh"])


def qdump__polymesh__edge_handle(d, value):
    d.putType("pm::edge_handle")
    idx = int(value["idx"]["value"])
    if idx < 0:
        d.putValue("<invalid edge>")
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            mod = " (null mesh)"
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mHalfedgesSize"]) // 2
            if idx >= pcnt:
                mod = " (out of bounds)"
            else:
                v = int(mesh["mHalfedgeToVertex"]["ptr"][2 * idx]["value"])
                if v == -1:
                    mod = " (removed)"
        d.putValue("edge {}".format(idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("idx", value["idx"])
            d.putSubItem("mesh", value["mesh"])


def qdump__polymesh__halfedge_handle(d, value):
    d.putType("pm::halfedge_handle")
    idx = int(value["idx"]["value"])
    if idx < 0:
        d.putValue("<invalid halfedge>")
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            mod = " (null mesh)"
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mHalfedgesSize"])
            if idx >= pcnt:
                mod = " (out of bounds)"
            else:
                v = int(mesh["mHalfedgeToVertex"]["ptr"][idx]["value"])
                if v == -1:
                    mod = " (removed)"
        d.putValue("halfedge {}".format(idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("idx", value["idx"])
            d.putSubItem("mesh", value["mesh"])


def qdump__polymesh__face_handle(d, value):
    d.putType("pm::face_handle")
    idx = int(value["idx"]["value"])
    if idx < 0:
        d.putValue("<invalid face>")
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            mod = " (null mesh)"
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mFacesSize"])
            if idx >= pcnt:
                mod = " (out of bounds)"
            else:
                hh = int(mesh["mFaceToHalfedge"]["ptr"][idx]["value"])
                if hh == -1:
                    mod = " (removed)"
        d.putValue("face {}".format(idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("idx", value["idx"])
            d.putSubItem("mesh", value["mesh"])


def qdump__polymesh__vertex_attribute(d, value):
    mesh = value["mMesh"]

    if int(mesh) == 0:
        d.putValue("<no mesh attached>")
        return

    mesh = mesh.dereference()

    maxCount = 1000

    vcnt = int(mesh["mVerticesSize"])
    vrcnt = int(mesh["mRemovedVertices"])

    d.putValue(make_count_str(vcnt, vrcnt, "value", "values"))

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("mesh", mesh)
            d.putSubItem("default", value["mDefaultValue"])
            aptr = value["mData"]["ptr"]
            ohptr = mesh["mVertexToOutgoingHalfedge"]["ptr"]
            for i in range(vcnt):
                if i >= maxCount:
                    add_computed_child(d, "...", "+ {} more".format(vcnt - maxCount))
                    break
                if int(ohptr[i]["value"]) == -2:
                    add_computed_child(d, "[{}]".format(i), "<removed>")
                else:
                    d.putSubItem("[{}]".format(i), aptr[i])


def qdump__polymesh__face_attribute(d, value):
    mesh = value["mMesh"]

    if int(mesh) == 0:
        d.putValue("<no mesh attached>")
        return

    mesh = mesh.dereference()

    maxCount = 1000

    fcnt = int(mesh["mFacesSize"])
    frcnt = int(mesh["mRemovedFaces"])

    d.putValue(make_count_str(fcnt, frcnt, "value", "values"))

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("mesh", mesh)
            d.putSubItem("default", value["mDefaultValue"])
            aptr = value["mData"]["ptr"]
            vhptr = mesh["mFaceToHalfedge"]["ptr"]
            for i in range(fcnt):
                if i >= maxCount:
                    add_computed_child(d, "...", "+ {} more".format(fcnt - maxCount))
                    break
                if int(vhptr[i]["value"]) == -1:
                    add_computed_child(d, "[{}]".format(i), "<removed>")
                else:
                    d.putSubItem("[{}]".format(i), aptr[i])


def qdump__polymesh__edge_attribute(d, value):
    mesh = value["mMesh"]

    if int(mesh) == 0:
        d.putValue("<no mesh attached>")
        return

    mesh = mesh.dereference()

    maxCount = 1000

    ecnt = int(mesh["mHalfedgesSize"]) // 2
    ercnt = int(mesh["mRemovedHalfedges"]) // 2

    d.putValue(make_count_str(ecnt, ercnt, "value", "values"))

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("mesh", mesh)
            d.putSubItem("default", value["mDefaultValue"])
            aptr = value["mData"]["ptr"]
            vhptr = mesh["mHalfedgeToVertex"]["ptr"]
            for i in range(ecnt):
                if i >= maxCount:
                    add_computed_child(d, "...", "+ {} more".format(ecnt - maxCount))
                    break
                if int(vhptr[2 * i]["value"]) == -1:
                    add_computed_child(d, "[{}]".format(i), "<removed>")
                else:
                    d.putSubItem("[{}]".format(i), aptr[i])


def qdump__polymesh__halfedge_attribute(d, value):
    mesh = value["mMesh"]

    if int(mesh) == 0:
        d.putValue("<no mesh attached>")
        return

    mesh = mesh.dereference()

    maxCount = 1000

    hcnt = int(mesh["mHalfedgesSize"])
    hrcnt = int(mesh["mRemovedHalfedges"])

    d.putValue(make_count_str(hcnt, hrcnt, "value", "values"))

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            d.putSubItem("mesh", mesh)
            d.putSubItem("default", value["mDefaultValue"])
            aptr = value["mData"]["ptr"]
            vhptr = mesh["mHalfedgeToVertex"]["ptr"]
            for i in range(hcnt):
                if i >= maxCount:
                    add_computed_child(d, "...", "+ {} more".format(hcnt - maxCount))
                    break
                if int(vhptr[i]["value"]) == -1:
                    add_computed_child(d, "[{}]".format(i), "<removed>")
                else:
                    d.putSubItem("[{}]".format(i), aptr[i])
