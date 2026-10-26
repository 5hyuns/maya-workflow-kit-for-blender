# SPDX-License-Identifier: GPL-3.0-or-later
"""maya.cmds look-alike 3 (step 216, Issue #122): freeze, constraints, joints, connections.

Maya behaviour:  (Maya, cases  c216_*)."""


def makeIdentity(*args, **kwargs):
    raise NotImplementedError("makeIdentity")


def parentConstraint(*args, **kwargs):
    raise NotImplementedError("parentConstraint")


def pointConstraint(*args, **kwargs):
    raise NotImplementedError("pointConstraint")


def orientConstraint(*args, **kwargs):
    raise NotImplementedError("orientConstraint")


def scaleConstraint(*args, **kwargs):
    raise NotImplementedError("scaleConstraint")


def aimConstraint(*args, **kwargs):
    raise NotImplementedError("aimConstraint")


def joint(*args, **kwargs):
    raise NotImplementedError("joint")


def connectAttr(*args, **kwargs):
    raise NotImplementedError("connectAttr")


def disconnectAttr(*args, **kwargs):
    raise NotImplementedError("disconnectAttr")


def isConnected(*args, **kwargs):
    raise NotImplementedError("isConnected")


def listConnections(*args, **kwargs):
    raise NotImplementedError("listConnections")


def connectionInfo(*args, **kwargs):
    raise NotImplementedError("connectionInfo")

