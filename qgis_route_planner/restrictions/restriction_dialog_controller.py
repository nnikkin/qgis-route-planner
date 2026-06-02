from __future__ import annotations
from typing import TYPE_CHECKING

from qgis_route_planner.exceptions import RoutingPluginError
from qgis_route_planner.logger import Logger

if TYPE_CHECKING:
    from qgis_route_planner.restrictions.restriction_service import RestrictionService
    from qgis_route_planner.restrictions.restriction_model import RestrictionModel

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject, QDateTime
from qgis.core import QgsPointXY

from qgis_route_planner.restrictions.restriction_type import RestrictionType
from qgis_route_planner.restrictions.restriction_record import RestrictionRecord
from qgis_route_planner.shared.form_mode import FormMode


class RestrictionDialogController(QObject):
    """ Контроллер диалога ограничений """

    # Сигналы для view
    open_requested = pyqtSignal()
    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    # Сигналы для взаимодействия с main window
    select_point_on_map_requested = pyqtSignal(bool)
    point_selected = pyqtSignal(object, int)  # point, node_id

    def __init__(self, model: RestrictionModel, service: RestrictionService):
        super().__init__()
        self.__model = model
        self.__service = service
        self.__awaiting_point = False

    def open_dialog(self):
        """ Открыть диалог """
        self.refresh_restrictions()
        self.open_requested.emit()

    def refresh_restrictions(self):
        """ Обновить список ограничений в модели  """
        self.__load_restrictions()

    @pyqtSlot(object)
    def change_restriction_type_value(self, value: RestrictionType):
        self.__model.restriction_type = value

    @pyqtSlot(str)
    def change_name_value(self, value: str):
        self.__model.name = value

    @pyqtSlot(str)
    def change_comment_value(self, value: str):
        self.__model.comment = value

    @pyqtSlot(object, int)
    def change_point_value(self, point: QgsPointXY | None, node_id: int | None):
        self.__model.point = (point, node_id) if node_id is not None else None

    @pyqtSlot(QDateTime)
    def change_valid_from_value(self, dt_value):
        self.__model.valid_from = dt_value

    @pyqtSlot(QDateTime)
    def change_valid_to_value(self, dt_value):
        self.__model.valid_to = dt_value

    @pyqtSlot(float)
    def change_max_height_value(self, value: float):
        self.__model.max_height = value

    @pyqtSlot(float)
    def change_max_width_value(self, value: float):
        self.__model.max_width = value

    @pyqtSlot(float)
    def change_max_weight_value(self, value: float):
        self.__model.max_weight = value

    def __load_restrictions(self):
        """ Загрузить список ограничений из БД в модель """
        try:
            restrictions = self.__service.get_all_restrictions()
            restriction_records = [RestrictionRecord.dict_to_record(r) for r in restrictions]
            self.__model.restrictions = restriction_records
        except RoutingPluginError as e:
            self.show_error.emit(str(e))
        except Exception as e:
            Logger.error(e)
            self.show_error.emit("Не удалось загрузить ограничения")

    def on_restriction_selected(self, restriction_id: int | None):
        """ Обработчик выбора ограничения в списке """
        if restriction_id is None:
            self.__model.current_restriction_id = None
            self.__model.current_restriction_data = None
            self.__model.clear_form()
            self.__model.editing_mode = FormMode.VIEW
            return

        self.__model.current_restriction_id = restriction_id
        self.__load_restriction_to_form(restriction_id)
        self.__model.editing_mode = FormMode.VIEW

    def on_create_restriction(self):
        """ Обработчик создания нового ограничения """
        self.__model.current_restriction_id = None
        self.__model.current_restriction_data = None
        self.__model.clear_form()
        self.__model.editing_mode = FormMode.CREATE

    def on_edit_restriction(self):
        """ Обработчик редактирования ограничения """
        if self.__model.current_restriction_id is not None:
            self.__model.editing_mode = FormMode.EDIT

    def on_cancel_edit(self):
        """ Обработчик отмены редактирования """
        current_id = self.__model.current_restriction_id
        if current_id is not None:
            self.__load_restriction_to_form(current_id)
        else:
            self.__model.current_restriction_data = None
            self.__model.clear_form()
        self.__model.editing_mode = FormMode.VIEW

    def on_save_restriction(self):
        """ Обработчик сохранения ограничения """
        name = self.__model.name.strip()
        if not name:
            self.show_warning.emit("Введите название ограничения!")
            return

        node_ids = self.__model.get_node_ids()

        if not node_ids:
            self.show_warning.emit("Добавьте хотя бы одну точку для ограничения!")
            return

        rt = self.__model.restriction_type
        type_name = getattr(rt, "name", str(rt))
        max_height_m = self.__model.max_height if type_name == "DIMENSION" else None
        max_width_m = self.__model.max_width if type_name == "DIMENSION" else None
        max_weight_t = self.__model.max_weight if type_name == "DIMENSION" else None
        valid_from = self.__date_to_storage_text(self.__model.valid_from) if type_name == "TEMPORARY" else None
        valid_to = self.__date_to_storage_text(self.__model.valid_to) if type_name == "TEMPORARY" else None
        value_num = next(
            (value for value in (max_height_m, max_width_m, max_weight_t) if value and value > 0),
            None,
        )

        try:
            current_id = self.__model.current_restriction_id
            editing_mode = self.__model.editing_mode

            for node_id in node_ids:
                record = RestrictionRecord(
                    restriction_type_id=RestrictionRecord.type_to_id(rt),
                    name=name,
                    node_id=node_id,
                    value_num=value_num,
                    value_text="",
                    comment=self.__model.comment.strip(),
                    max_height_m=max_height_m,
                    max_width_m=max_width_m,
                    max_weight_t=max_weight_t,
                    valid_from=valid_from,
                    valid_to=valid_to,
                )

                if editing_mode == FormMode.EDIT and current_id is not None:
                    record.id = current_id
                    self.__service.update_restriction(current_id, RestrictionRecord.record_to_dict(record))
                else:
                    self.__service.create_restriction(RestrictionRecord.record_to_dict(record))

            self.__load_restrictions()
            self.__model.editing_mode = FormMode.VIEW
            self.__model.current_restriction_id = None
            self.__model.current_restriction_data = None
            self.__model.clear_form()
            self.show_info.emit("Ограничение сохранено!")
        except Exception as e:
            self.show_error.emit(str(e))

    def on_delete_restriction(self):
        """ Обработчик удаления ограничения """
        current_id = self.__model.current_restriction_id
        if current_id is None:
            return

        try:
            self.__service.delete_restriction(current_id)
            self.__model.current_restriction_id = None
            self.__model.current_restriction_data = None
            self.__model.clear_form()
            self.__model.editing_mode = FormMode.VIEW
            self.__load_restrictions()
            self.show_info.emit("Ограничение удалено!")
        except Exception as e:
            self.show_error.emit(str(e))

    def on_select_point_on_map(self):
        """ Запрашиваем у главного окна активировать инструмент выбора """
        self.__awaiting_point = True
        self.select_point_on_map_requested.emit(True)

    def on_point_selected(self, point: QgsPointXY, node_id: int):
        """ Вызывается из MainWindowController, когда пользователь кликнул на карте """
        if not self.__awaiting_point:
            return
        self.__awaiting_point = False
        self.point_selected.emit(point, node_id)

    def __load_restriction_to_form(self, restriction_id: int):
        """ Загрузить данные ограничения в модель """
        try:
            r_dict = self.__service.get_restriction_by_id(restriction_id)
            if r_dict:
                record = RestrictionRecord.dict_to_record(r_dict)
                self.__model.load_record(record)
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки ограничения: {e}")

    @staticmethod
    def __date_to_storage_text(value) -> str:
        if value is None:
            return ""
        if hasattr(value, "toString"):
            return value.toString("yyyy-MM-dd HH:mm")
        return str(value)
