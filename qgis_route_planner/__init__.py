# -*- coding: utf-8 -*-
def classFactory(iface):  # pylint: disable=invalid-name
    from .qgis_route_planner import QgisRoutePlanner
    return QgisRoutePlanner(iface)
