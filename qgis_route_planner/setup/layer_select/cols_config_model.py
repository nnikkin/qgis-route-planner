from qgis.PyQt.QtCore import pyqtSignal, QObject

from qgis_route_planner.setup.layer_select.column_role import ColumnRole
from qgis_route_planner.setup.layer_select.layer_role import LayerRole
from qgis_route_planner.setup.layer_select.layer_config_model import Layer

from dataclasses import dataclass

@dataclass
class ColumnInfo:
    name: str
    data_type: str | None = None

class ColumnsConfigModel(QObject):
    """ Модель, используемая LayerColumnsDialog """

    available_columns_changed = pyqtSignal(dict)
    mappings_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.__available_columns: dict[str, list[ColumnInfo]] = {}
        self.__mappings: dict[str, dict[ColumnRole, str | None]] = {}
        self.__layers: list[Layer] = []

    @property
    def available_columns(self):
        return self.__available_columns

    @property
    def mappings(self):
        return self.__mappings

    @mappings.setter
    def mappings(self, value):
        self.__mappings = value
        self.mappings_changed.emit(self.__mappings)

    @property
    def layers(self) -> list[Layer]:
        return self.__layers

    def set_layers(self, layers: list[Layer]):
        self.__layers = list(layers)
        self.__mappings = {
            layer.name: {
                role: self.__mappings.get(layer.name, {}).get(role)
                for role in ColumnRole
            }
            for layer in self.__layers
        }
        self.mappings_changed.emit(self.__mappings)

    def set_available_columns(self, layer_name: str, columns: list[str | tuple | ColumnInfo]):
        self.__available_columns[layer_name] = [
            self.__normalize_column(column)
            for column in columns
        ]

        if layer_name in self.__mappings:
            for role in ColumnRole:
                if self.__mappings[layer_name].get(role):
                    continue

                guessed_column = self.__guess_column_for_role(role, self.__available_columns[layer_name])
                if guessed_column:
                    self.__mappings[layer_name][role] = guessed_column

        self.available_columns_changed.emit(self.__available_columns)
        self.mappings_changed.emit(self.__mappings)

    def set_mapping(self, layer_name: str, role: ColumnRole, column_name: str | None):
        if layer_name not in self.__mappings:
            self.__mappings[layer_name] = {role: None for role in ColumnRole}

        self.__mappings[layer_name][role] = column_name
        self.mappings_changed.emit(self.__mappings)

    def clear(self):
        self.__available_columns = {}
        self.__mappings = {}
        self.__layers = []
        self.available_columns_changed.emit(self.__available_columns)
        self.mappings_changed.emit(self.__mappings)

    def validate_required_mappings(self) -> list[str]:
        errors = []

        for layer in self.__layers:
            mapping = self.__mappings.get(layer.name, {})
            missing_roles = []

            for role in (ColumnRole.PRIMARY_KEY, ColumnRole.GEOMETRY):
                if not mapping.get(role):
                    missing_roles.append(role.value)

            if layer.role == LayerRole.ROADS and not mapping.get(ColumnRole.HIGHWAY):
                missing_roles.append(ColumnRole.HIGHWAY.value)

            if layer.role == LayerRole.PIPING and not mapping.get(ColumnRole.MAX_HEIGHT):
                missing_roles.append(ColumnRole.MAX_HEIGHT.value)

            if missing_roles:
                errors.append(f"{layer.name}: {', '.join(missing_roles)}")

        return errors

    def __normalize_column(self, column: str | tuple | ColumnInfo) -> ColumnInfo:
        if isinstance(column, ColumnInfo):
            return column

        if isinstance(column, str):
            return ColumnInfo(name=column)

        if isinstance(column, (tuple, list)) and column:
            data_type = column[1] if len(column) > 1 else None
            return ColumnInfo(name=column[0], data_type=data_type)

        return ColumnInfo(name=str(column))

    def __guess_column_for_role(self, role: ColumnRole, columns: list[ColumnInfo]) -> str | None:
        candidates_by_role = {
            ColumnRole.PRIMARY_KEY: ("osm_id", "id", "gid", "fid", "objectid"),
            ColumnRole.GEOMETRY: ("geom", "geometry", "wkb_geometry", "the_geom"),
            ColumnRole.HIGHWAY: ("highway",),
            ColumnRole.MAX_HEIGHT: ("max_height","maxheight"),
            ColumnRole.MAX_WIDTH: ("max_width", "maxwidth"),
            ColumnRole.MAX_SPEED: ("max_speed", "maxspeed"),
            ColumnRole.NAME: ("name",),
            ColumnRole.ADDRESS: ("addr:full", "address", "addr_street", "addr:street"),
            ColumnRole.OTHER: ("other_tags", "tags", "all_tags"),
        }

        available_by_lower = {column.name.lower(): column.name for column in columns}
        for candidate in candidates_by_role.get(role, ()):
            matched_column = available_by_lower.get(candidate.lower())
            if matched_column:
                return matched_column

        return None
