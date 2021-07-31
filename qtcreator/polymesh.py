
import sys
import math
from dumper import Children, SubItem
from helper import *


type_vertex_handle = None
type_face_handle = None
type_edge_handle = None
type_halfedge_handle = None

local_vertex_attrs = None
local_face_attrs = None
local_edge_attrs = None
local_halfedge_attrs = None


def init_local_attrs(d):
    global local_edge_attrs, local_face_attrs, local_vertex_attrs, local_halfedge_attrs

    if local_vertex_attrs is not None:
        return  # already initialized

    local_vertex_attrs = []
    local_face_attrs = []
    local_edge_attrs = []
    local_halfedge_attrs = []

    if not hasattr(d, 'listLocals'):
        return  # not gdb

    vars = d.listLocals(None)

    for v in vars:
        tname = v.type.name

        if tname.startswith("polymesh::vertex_attribute"):
            v.imesh = int(v["mMesh"].pointer())
            if v.imesh != 0:
                local_vertex_attrs.append(v)

        elif tname.startswith("polymesh::edge_attribute"):
            v.imesh = int(v["mMesh"].pointer())
            if v.imesh != 0:
                local_edge_attrs.append(v)

        elif tname.startswith("polymesh::halfedge_attribute"):
            v.imesh = int(v["mMesh"].pointer())
            if v.imesh != 0:
                local_halfedge_attrs.append(v)

        elif tname.startswith("polymesh::face_attribute"):
            v.imesh = int(v["mMesh"].pointer())
            if v.imesh != 0:
                local_face_attrs.append(v)


def get_local_attr_name(attr, attrs):
    ad = int(attr.address())
    for a in attrs:
        if int(a.address()) == ad:
            return a.name
    return None


# NOTE: must call init_local_attrs before!
def put_all_local_and_mesh_attrs(d, pidx, mesh, mattrs, lattrs):
    mesh = int(mesh.address())

    if int(mattrs) != 0:
        with SubItem(d, "attributes"):
            d.putExpandable()
            if d.isExpanded():
                maxAttrs = 50
                attrs = []
                while int(mattrs) != 0:
                    if len(attrs) >= maxAttrs:
                        break

                    a = mattrs.dereference()
                    attrs.append(a)
                    mattrs = a["mNextAttribute"]

                # because registration is in opposite order
                attrs = list(reversed(attrs))

                with Children(d):
                    for i in range(len(attrs)):
                        aname = get_local_attr_name(attrs[i], lattrs)
                        if aname is None:
                            aname = "[{}]".format(i)
                        d.putSubItem(aname, attrs[i]["mData"]["ptr"][pidx])

    for a in lattrs:
        if a.imesh != mesh:
            continue  # wrong mesh

        d.putSubItem("{}[{}]".format(a.name, pidx), a["mData"]["ptr"][pidx])


class MeshApi:
    def __init__(self, mesh):
        self.mesh = mesh
        self.p_face_to_halfedge = mesh["mFaceToHalfedge"]["ptr"]
        self.p_vertex_to_outgoing_halfedge = mesh["mVertexToOutgoingHalfedge"]["ptr"]
        self.p_halfedge_to_vertex = mesh["mHalfedgeToVertex"]["ptr"]
        self.p_halfedge_to_face = mesh["mHalfedgeToFace"]["ptr"]
        self.p_halfedge_to_next = mesh["mHalfedgeToNextHalfedge"]["ptr"]
        self.p_halfedge_to_prev = mesh["mHalfedgeToPrevHalfedge"]["ptr"]

    def face_to_halfedge(self, i):
        return int(self.p_face_to_halfedge[i]["value"])

    def vertex_to_outgoing_halfedge(self, i):
        return int(self.p_vertex_to_outgoing_halfedge[i]["value"])

    def halfedge_to_vertex(self, i):
        return int(self.p_halfedge_to_vertex[i]["value"])

    def halfedge_to_face(self, i):
        return int(self.p_halfedge_to_face[i]["value"])

    def halfedge_to_next(self, i):
        return int(self.p_halfedge_to_next[i]["value"])

    def halfedge_to_prev(self, i):
        return int(self.p_halfedge_to_prev[i]["value"])

    def is_halfedge_boundary(self, i):
        return self.halfedge_to_face(i) < 0

    def is_face_boundary(self, i):
        return self.is_halfedge_boundary(self.face_to_halfedge(i) ^ 1)

    def is_edge_boundary(self, i):
        return self.is_halfedge_boundary(i * 2) or self.is_halfedge_boundary(i * 2 + 1)

    def is_edge_isolated(self, i):
        return self.is_halfedge_boundary(i * 2) and self.is_halfedge_boundary(i * 2 + 1)

    def is_vertex_boundary(self, i):
        oh = self.vertex_to_outgoing_halfedge(i)
        if oh < 0:
            return True
        return self.is_halfedge_boundary(oh)

    def vertex_to_vertices(self, vi, *, limit=99):
        more = False
        res = []
        oh = self.vertex_to_outgoing_halfedge(vi)
        h = oh
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(self.halfedge_to_vertex(h))
            h = self.halfedge_to_next(h ^ 1)
            if h == oh:
                break
        return res, more

    def vertex_to_outgoing_halfedges(self, vi, *, limit=99):
        more = False
        res = []
        oh = self.vertex_to_outgoing_halfedge(vi)
        h = oh
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(h)
            h = self.halfedge_to_next(h ^ 1)
            if h == oh:
                break
        return res, more

    def vertex_to_edges(self, vi, *, limit=99):
        more = False
        res = []
        oh = self.vertex_to_outgoing_halfedge(vi)
        h = oh
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(h // 2)
            h = self.halfedge_to_next(h ^ 1)
            if h == oh:
                break
        return res, more

    def vertex_to_incoming_halfedges(self, vi, *, limit=99):
        more = False
        res = []
        oh = self.vertex_to_outgoing_halfedge(vi)
        h = oh
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(h ^ 1)
            h = self.halfedge_to_next(h ^ 1)
            if h == oh:
                break
        return res, more

    def vertex_to_faces(self, vi, *, limit=99):
        more = False
        res = []
        oh = self.vertex_to_outgoing_halfedge(vi)
        h = oh
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            f = self.halfedge_to_face(h)
            if f >= 0:
                res.append(f)
            h = self.halfedge_to_next(h ^ 1)
            if h == oh:
                break
        return res, more

    def halfedge_to_ring(self, hi, *, limit=99):
        more = False
        res = []
        h = hi
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(h)
            h = self.halfedge_to_next(h)
            if h == hi:
                break
        return res, more

    def face_to_vertices(self, fi, *, limit=99):
        more = False
        res = []
        hi = self.face_to_halfedge(fi)
        h = hi
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(self.halfedge_to_vertex(h))
            h = self.halfedge_to_next(h)
            if h == hi:
                break
        return res, more

    def face_to_halfedges(self, fi, *, limit=99):
        more = False
        res = []
        hi = self.face_to_halfedge(fi)
        h = hi
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(h)
            h = self.halfedge_to_next(h)
            if h == hi:
                break
        return res, more

    def face_to_edges(self, fi, *, limit=99):
        more = False
        res = []
        hi = self.face_to_halfedge(fi)
        h = hi
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            res.append(h // 2)
            h = self.halfedge_to_next(h)
            if h == hi:
                break
        return res, more

    def face_to_faces(self, fi, *, limit=99):
        more = False
        res = []
        hi = self.face_to_halfedge(fi)
        h = hi
        while h >= 0:
            if len(res) >= limit:
                more = True
                break
            f = self.halfedge_to_face(h ^ 1)
            if f >= 0:
                res.append(f)
            h = self.halfedge_to_next(h)
            if h == hi:
                break
        return res, more


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

            with SubItem(d, "properties"):
                d.putExpandable()
                if d.isExpanded():
                    with Children(d):
                        add_computed_child(d, "...", "TODO")
                        # TODO: computed values like "has boundary", "genus", "byte size", etc. that require mesh iteration

            init_local_attrs(d)
            global local_edge_attrs, local_face_attrs, local_vertex_attrs, local_halfedge_attrs

            def show_attributes(attr, aname, lattrs):
                if int(attr) == 0:
                    return

                maxAttrs = 50
                attrs = []
                while int(attr) != 0:
                    if len(attrs) >= maxAttrs:
                        break

                    a = attr.dereference()
                    attrs.append(a)
                    attr = a["mNextAttribute"]

                # because registration is in opposite order
                attrs = list(reversed(attrs))

                with SubItem(d, aname):
                    d.putValue("{} attribute{}".format(
                        len(attrs), "s" if len(attrs) != 1 else ""))

                    d.putNumChild(len(attrs))
                    if d.isExpanded():
                        with Children(d, len(attrs)):
                            for i in range(len(attrs)):
                                aname = get_local_attr_name(attrs[i], lattrs)
                                if aname is None:
                                    aname = "[{}]".format(i)
                                d.putSubItem(aname, attrs[i])

            show_collection("vertex", "vertices", vcnt,
                            vrcnt, make_vertex_handle)
            show_attributes(value["mVertexAttrs"],
                            "vertex attrs", local_vertex_attrs)

            show_collection("edge", "edges", ecnt,
                            ercnt, make_edge_handle)
            show_attributes(value["mEdgeAttrs"],
                            "edge attrs", local_edge_attrs)

            show_collection("halfedge", "halfedges", hcnt,
                            hrcnt, make_halfedge_handle)
            show_attributes(value["mHalfedgeAttrs"],
                            "halfedge attrs", local_halfedge_attrs)

            show_collection("face", "faces", fcnt,
                            frcnt, make_face_handle)
            show_attributes(value["mFaceAttrs"],
                            "face attrs", local_face_attrs)


def qdump__polymesh__vertex_index(d, value):
    d.putType("pm::vertex_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid vertex ({})>".format(v))
        return

    d.putValue("vertex {}".format(v))


def qdump__polymesh__edge_index(d, value):
    d.putType("pm::edge_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid edge ({})>".format(v))
        return

    d.putValue("edge {}".format(v))


def qdump__polymesh__halfedge_index(d, value):
    d.putType("pm::halfedge_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid halfedge ({})>".format(v))
        return

    d.putValue("halfedge {}".format(v))


def qdump__polymesh__face_index(d, value):
    d.putType("pm::face_index")
    v = int(value["value"])
    if v < 0:
        d.putValue("<invalid face ({})>".format(v))
        return

    d.putValue("face {}".format(v))


def show_primitive_topo(d, mesh, cname, sname, pname, prims_more, handle_fun):
    prims, more = prims_more
    with SubItem(d, cname):
        d.putValue("{}{} {}".format(len(prims), "+" if more else "",
                   sname if len(prims) == 1 else pname))
        d.putNumChild(len(prims))
        if d.isExpanded():
            with Children(d, len(prims)):
                pmesh = mesh.address()
                for i in range(len(prims)):
                    if prims[i] < 0:
                        add_computed_child(
                            d, "[{}]".format(prims[i]), "<none>")
                    else:
                        d.putSubItem("[{}]".format(prims[i]),
                                     handle_fun(d, prims[i], pmesh))


def qdump__polymesh__vertex_handle(d, value):
    d.putType("pm::vertex_handle")
    idx = int(value["idx"]["value"])
    valid = False
    ll = None
    if idx < 0:
        d.putValue("<invalid vertex ({})>".format(idx))
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            d.putValue("<null mesh (vertex {})>".format(idx))
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mVerticesSize"])
            if idx >= pcnt:
                d.putValue("<out of bounds (vertex {})>".format(idx))
            else:
                oh = int(mesh["mVertexToOutgoingHalfedge"]
                         ["ptr"][idx]["value"])
                if oh == -2:
                    d.putValue("<removed vertex ({})>".format(idx))
                else:
                    valid = True
                    ll = MeshApi(mesh)
                    vs, vs_more = ll.vertex_to_vertices(idx)
                    if len(vs) == 0:
                        mod = ", isolated"
                    else:
                        mod += ", valence {}{}".format(len(vs),
                                                       "+" if vs_more else "")
                        if ll.is_vertex_boundary(idx):
                            mod += ", boundary"
                    d.putValue("vertex {}".format(idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            if not valid:
                d.putSubItem("idx", value["idx"])
                d.putSubItem("mesh", value["mesh"])

            if valid:
                with SubItem(d, "topology"):
                    d.putExpandable()
                    if d.isExpanded():
                        with Children(d):
                            d.putSubItem("idx", value["idx"])
                            d.putSubItem("mesh", value["mesh"])
                            add_computed_child(d, "valence", "{}{}".format(
                                len(vs), "+" if vs_more else ""))
                            add_computed_child(d, "isolated", len(vs) == 0)
                            add_computed_child(
                                d, "boundary", ll.is_vertex_boundary(idx))
                            show_primitive_topo(d, mesh, "adj. vertices", "vertex",
                                                "vertices", (vs, vs_more), make_vertex_handle)
                            show_primitive_topo(d, mesh, "faces", "face",
                                                "faces", ll.vertex_to_faces(idx), make_face_handle)
                            show_primitive_topo(d, mesh, "edges", "edge",
                                                "edges", ll.vertex_to_edges(idx), make_edge_handle)
                            show_primitive_topo(d, mesh, "outgoing halfedges", "halfedge",
                                                "halfedges", ll.vertex_to_outgoing_halfedges(idx), make_halfedge_handle)
                            show_primitive_topo(d, mesh, "incoming halfedges", "halfedge",
                                                "halfedges", ll.vertex_to_incoming_halfedges(idx), make_halfedge_handle)

                init_local_attrs(d)
                global local_vertex_attrs
                put_all_local_and_mesh_attrs(
                    d, idx, mesh, mesh["mVertexAttrs"], local_vertex_attrs)


def qdump__polymesh__edge_handle(d, value):
    d.putType("pm::edge_handle")
    idx = int(value["idx"]["value"])
    valid = False
    is_boundary = False
    is_isolated = False
    ll = None
    if idx < 0:
        d.putValue("<invalid edge ({})>".format(idx))
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            d.putValue("<null mesh (edge {})>".format(idx))
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mHalfedgesSize"]) // 2
            if idx >= pcnt:
                d.putValue("<out of bounds (edge {})>".format(idx))
            else:
                v = int(mesh["mHalfedgeToVertex"]["ptr"][2 * idx]["value"])
                if v == -1:
                    d.putValue("<removed edge ({})>".format(idx))
                else:
                    valid = True
                    ll = MeshApi(mesh)
                    if ll.is_edge_isolated(idx):
                        mod = ", isolated"
                        is_isolated = True
                        is_boundary = True
                    elif ll.is_edge_boundary(idx):
                        mod = ", boundary"
                        is_boundary = True
                    d.putValue("edge {}".format(idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            if not valid:
                d.putSubItem("idx", value["idx"])
                d.putSubItem("mesh", value["mesh"])

            if valid:
                with SubItem(d, "topology"):
                    d.putExpandable()
                    if d.isExpanded():
                        with Children(d):
                            d.putSubItem("idx", value["idx"])
                            d.putSubItem("mesh", value["mesh"])
                            add_computed_child(d, "isolated", is_isolated)
                            add_computed_child(d, "boundary", is_boundary)
                            d.putSubItem("halfedgeA", make_halfedge_handle(
                                d, 2 * idx + 0, mesh.address()))
                            d.putSubItem("halfedgeB", make_halfedge_handle(
                                d, 2 * idx + 1, mesh.address()))
                            d.putSubItem("vertexA", make_vertex_handle(
                                d, ll.halfedge_to_vertex(2 * idx + 0), mesh.address()))
                            d.putSubItem("vertexB", make_vertex_handle(
                                d, ll.halfedge_to_vertex(2 * idx + 1), mesh.address()))
                            d.putSubItem("faceA", make_face_handle(
                                d, ll.halfedge_to_face(2 * idx + 0), mesh.address()))
                            d.putSubItem("faceB", make_face_handle(
                                d, ll.halfedge_to_face(2 * idx + 1), mesh.address()))

                init_local_attrs(d)
                global local_edge_attrs
                put_all_local_and_mesh_attrs(
                    d, idx, mesh, mesh["mEdgeAttrs"], local_edge_attrs)


def qdump__polymesh__halfedge_handle(d, value):
    d.putType("pm::halfedge_handle")
    idx = int(value["idx"]["value"])
    valid = False
    is_boundary = False
    ll = None
    if idx < 0:
        d.putValue("<invalid halfedge ({})>".format(idx))
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            d.putValue("<null mesh (halfedge {})>".format(idx))
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mHalfedgesSize"])
            if idx >= pcnt:
                d.putValue("<out of bounds (halfedge {})>".format(idx))
            else:
                v = int(mesh["mHalfedgeToVertex"]["ptr"][idx]["value"])
                if v == -1:
                    d.putValue("<removed halfedge ({})>".format(idx))
                else:
                    valid = True
                    ll = MeshApi(mesh)
                    if ll.is_halfedge_boundary(idx):
                        mod = ", boundary"
                        is_boundary = True
                    d.putValue("halfedge {}".format(idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            if not valid:
                d.putSubItem("idx", value["idx"])
                d.putSubItem("mesh", value["mesh"])

            if valid:
                with SubItem(d, "topology"):
                    d.putExpandable()
                    if d.isExpanded():
                        with Children(d):
                            d.putSubItem("idx", value["idx"])
                            d.putSubItem("mesh", value["mesh"])
                            add_computed_child(d, "boundary", is_boundary)
                            d.putSubItem("opposite", make_halfedge_handle(
                                d, idx ^ 1, mesh.address()))
                            d.putSubItem("next", make_halfedge_handle(
                                d, ll.halfedge_to_next(idx), mesh.address()))
                            d.putSubItem("prev", make_halfedge_handle(
                                d, ll.halfedge_to_prev(idx), mesh.address()))
                            d.putSubItem("vertex_to", make_vertex_handle(
                                d, ll.halfedge_to_vertex(idx), mesh.address()))
                            d.putSubItem("vertex_from", make_vertex_handle(
                                d, ll.halfedge_to_vertex(idx ^ 1), mesh.address()))
                            d.putSubItem("edge", make_edge_handle(
                                d, idx // 2, mesh.address()))
                            d.putSubItem("face", make_face_handle(
                                d, ll.halfedge_to_face(idx), mesh.address()))
                            d.putSubItem("opposite_face", make_face_handle(
                                d, ll.halfedge_to_face(idx ^ 1), mesh.address()))
                            show_primitive_topo(d, mesh, "ring", "halfedge",
                                                "halfedges", ll.halfedge_to_ring(idx), make_halfedge_handle)

                init_local_attrs(d)
                global local_halfedge_attrs
                put_all_local_and_mesh_attrs(
                    d, idx, mesh, mesh["mHalfedgeAttrs"], local_halfedge_attrs)


def qdump__polymesh__face_handle(d, value):
    d.putType("pm::face_handle")
    idx = int(value["idx"]["value"])
    valid = False
    is_boundary = False
    ll = None
    if idx < 0:
        d.putValue("<invalid face ({})>".format(idx))
    else:
        mod = ""
        mesh = value["mesh"]
        if int(mesh) == 0:
            d.putValue("<null mesh (face {})>".format(idx))
        else:
            mesh = mesh.dereference()
            pcnt = int(mesh["mFacesSize"])
            if idx >= pcnt:
                d.putValue("<out of bounds (face {})>".format(idx))
            else:
                hh = int(mesh["mFaceToHalfedge"]["ptr"][idx]["value"])
                if hh == -1:
                    d.putValue("<removed face ({})>".format(idx))
                else:
                    valid = True
                    tname = "polygon"
                    ll = MeshApi(mesh)
                    vs, vs_more = ll.face_to_vertices(idx)
                    if len(vs) == 3:
                        tname = "triangle"
                    elif len(vs) == 4:
                        tname = "quad"
                    else:
                        mod = ", {}-gon".format(len(vs))
                    if ll.is_face_boundary(idx):
                        mod += ", boundary"
                        is_boundary = True
                    d.putValue("{} {}".format(tname, idx) + mod)

    d.putExpandable()
    if d.isExpanded():
        with Children(d):
            if not valid:
                d.putSubItem("idx", value["idx"])
                d.putSubItem("mesh", value["mesh"])

            if valid:
                with SubItem(d, "topology"):
                    d.putExpandable()
                    if d.isExpanded():
                        with Children(d):
                            d.putSubItem("idx", value["idx"])
                            d.putSubItem("mesh", value["mesh"])
                            add_computed_child(d, "boundary", is_boundary)
                            show_primitive_topo(d, mesh, "vertices", "vertex",
                                                "vertices", (vs, vs_more), make_vertex_handle)
                            show_primitive_topo(d, mesh, "adj. faces", "face",
                                                "faces", ll.face_to_faces(idx), make_face_handle)
                            show_primitive_topo(d, mesh, "edges", "edge",
                                                "edges", ll.face_to_edges(idx), make_edge_handle)
                            show_primitive_topo(d, mesh, "halfedges", "halfedge",
                                                "halfedges", ll.face_to_halfedges(idx), make_halfedge_handle)

                init_local_attrs(d)
                global local_face_attrs
                put_all_local_and_mesh_attrs(
                    d, idx, mesh, mesh["mFaceAttrs"], local_face_attrs)


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
                    add_computed_child(
                        d, "...", "+ {} more".format(vcnt - maxCount))
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
                    add_computed_child(
                        d, "...", "+ {} more".format(fcnt - maxCount))
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
                    add_computed_child(
                        d, "...", "+ {} more".format(ecnt - maxCount))
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
                    add_computed_child(
                        d, "...", "+ {} more".format(hcnt - maxCount))
                    break
                if int(vhptr[i]["value"]) == -1:
                    add_computed_child(d, "[{}]".format(i), "<removed>")
                else:
                    d.putSubItem("[{}]".format(i), aptr[i])
