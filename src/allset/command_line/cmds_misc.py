# SPDX-License-Identifier: GPL-3.0-or-later
"""maya.cmds look-alike 3 (step 216, Issue #122): node types, attribute queries, units, sets, shading nodes, polygon queries / extrude.

Maya behaviour: research/maya/re/cmds_201.md 「step 216」 (mayapy, cases research/scripts/cmds_201/cases.py c216_*)."""


def nodeType(*args, **kwargs):
    raise NotImplementedError("nodeType")


def objectType(*args, **kwargs):
    raise NotImplementedError("objectType")


def attributeQuery(*args, **kwargs):
    raise NotImplementedError("attributeQuery")


def currentUnit(*args, **kwargs):
    raise NotImplementedError("currentUnit")


def sets(*args, **kwargs):
    raise NotImplementedError("sets")


def shadingNode(*args, **kwargs):
    raise NotImplementedError("shadingNode")


def polyExtrudeFacet(*args, **kwargs):
    raise NotImplementedError("polyExtrudeFacet")


def polyEvaluate(*args, **kwargs):
    raise NotImplementedError("polyEvaluate")


def exactWorldBoundingBox(*args, **kwargs):
    raise NotImplementedError("exactWorldBoundingBox")


def listHistory(*args, **kwargs):
    raise NotImplementedError("listHistory")


def camera(*args, **kwargs):
    raise NotImplementedError("camera")

