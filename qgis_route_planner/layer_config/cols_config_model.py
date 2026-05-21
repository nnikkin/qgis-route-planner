from qgis.PyQt.QtCore import pyqtSignal, QObject

from .column_role import ColumnRole
from .layer_role import LayerRole
from .layer_config_model import Layer

from dataclasses import dataclass

@dataclass
class ColumnInfo:
    name: str
    data_type: str | None = None

class ColumnsConfigModel(QObject):
    """ Модель, используемая LayerColumnsDialog """

    __ROLE_COLUMN_RULES = {
        LayerRole.ROADS: {
            "required": {
                ColumnRole.PRIMARY_KEY,
                ColumnRole.GEOMETRY,
                ColumnRole.HIGHWAY,
                ColumnRole.ONEWAY,
                ColumnRole.LANES_FORWARD,
                ColumnRole.LANES_BACKWARD
            },
            "optional": {
                ColumnRole.NAME,
                ColumnRole.OTHER,
                ColumnRole.MAX_SPEED,
                ColumnRole.BRIDGE,
                ColumnRole.MAX_WEIGHT,
                ColumnRole.MAX_WIDTH
            },
        },
        LayerRole.POINTS: {
            "required": {ColumnRole.GEOMETRY},
            "optional": {
                ColumnRole.PRIMARY_KEY,
                ColumnRole.NAME,
                ColumnRole.ADDRESS,
                ColumnRole.OTHER,
                ColumnRole.MAX_SPEED,
            },
        },
        LayerRole.PARKING: {
            "required": {ColumnRole.GEOMETRY},
            "optional": {
                ColumnRole.PRIMARY_KEY,
                ColumnRole.NAME,
                ColumnRole.ADDRESS,
                ColumnRole.OTHER,
            },
        },
        LayerRole.PIPING: {
            "required": {ColumnRole.GEOMETRY, ColumnRole.LOCATION, ColumnRole.MAX_HEIGHT},
            "optional": {
                ColumnRole.PRIMARY_KEY,
                ColumnRole.NAME,
                ColumnRole.OTHER,
            },
        },
        LayerRole.FOR_CONTEXT: {
            "required": {ColumnRole.GEOMETRY},
        },
    }

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
                role: (
                    self.__mappings.get(layer.name, {}).get(role)
                    if self.is_role_applicable(layer.role, role)
                    else None
                )
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
            layer = self.__layer_by_name(layer_name)
            for role in ColumnRole:
                if layer and not self.is_role_applicable(layer.role, role):
                    self.__mappings[layer_name][role] = None
                    continue

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

        layer = self.__layer_by_name(layer_name)
        if layer and not self.is_role_applicable(layer.role, role):
            column_name = None

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

            for role in self.required_roles_for_layer(layer.role):
                if not mapping.get(role):
                    missing_roles.append(role.value)

            if missing_roles:
                errors.append(f"{layer.name}: {', '.join(missing_roles)}")

        return errors

    @classmethod
    def required_roles_for_layer(cls, layer_role: LayerRole) -> set[ColumnRole]:
        return set(cls.__ROLE_COLUMN_RULES.get(layer_role, {}).get("required", set()))

    @classmethod
    def optional_roles_for_layer(cls, layer_role: LayerRole) -> set[ColumnRole]:
        return set(cls.__ROLE_COLUMN_RULES.get(layer_role, {}).get("optional", set()))

    @classmethod
    def applicable_roles_for_layer(cls, layer_role: LayerRole) -> set[ColumnRole]:
        return cls.required_roles_for_layer(layer_role) | cls.optional_roles_for_layer(layer_role)

    @classmethod
    def is_role_required(cls, layer_role: LayerRole, column_role: ColumnRole) -> bool:
        return column_role in cls.required_roles_for_layer(layer_role)

    @classmethod
    def is_role_applicable(cls, layer_role: LayerRole, column_role: ColumnRole) -> bool:
        return column_role in cls.applicable_roles_for_layer(layer_role)

    def __layer_by_name(self, layer_name: str) -> Layer | None:
        return next((layer for layer in self.__layers if layer.name == layer_name), None)

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
            ColumnRole.PRIMARY_KEY: ("osm_id", "id", "gid", "fid", "objectid",),
            ColumnRole.GEOMETRY: ("geom", "geometry", "wkb_geometry",),
            ColumnRole.ONEWAY: ("oneway",),
            ColumnRole.HIGHWAY: ("highway",),
            ColumnRole.LANES_FORWARD: ("lanes:forward", "lanes_forward",),
            ColumnRole.LANES_BACKWARD: ("lanes:backward","lanes_backward",),
            ColumnRole.BRIDGE: ("bridge",),
            ColumnRole.MAX_HEIGHT: ("max_height", "maxheight",),
            ColumnRole.MAX_WIDTH: ("max_width", "maxwidth",),
            ColumnRole.MAX_SPEED: ("max_speed", "maxspeed",),
            ColumnRole.NAME: ("name", "name_ru",),
            ColumnRole.ADDRESS: ("addr", "addr:full", "address", "addr_street", "addr:street",),
            ColumnRole.LOCATION: ("location",),
            ColumnRole.OTHER: ("other_tags", "tags", "all_tags",),
        }

        available_by_lower = {column.name.lower(): column.name for column in columns}
        for candidate in candidates_by_role.get(role, ()):
            matched_column = available_by_lower.get(candidate.lower())
            if matched_column:
                return matched_column

        return None
