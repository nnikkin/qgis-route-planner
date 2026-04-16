# -*- coding: utf-8 -*-
def classFactory(iface):  # pylint: disable=invalid-name
    from .core import QgisRoutePlanner
    return QgisRoutePlanner(iface)