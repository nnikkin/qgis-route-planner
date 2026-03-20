from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services import RestrictionService
    from ..data.route import RestrictionModel

from qgis.PyQt.QtCore import pyqtSignal, QObject
from qgis.core import QgsPointXY

from ..data.models import RestrictionType
from ..data.route import RestrictionRecord
from ..utils import FormMode


class RestrictionDialogController(QObject):
    """Контроллер диалога ограничений"""

    # Сигналы для view
    open_requested = pyqtSignal()
    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    # Сигналы для обновления view
    load_restrictions_list = pyqtSignal(list)  # список ограничений для отображения
    load_restriction_to_form = pyqtSignal(dict)  # данные ограничения для загрузки в форму
    set_form_state = pyqtSignal(object)  # FormMode (VIEW/EDIT/CREATE)
    clear_form = pyqtSignal()  # очистить форму
    set_list_buttons_enabled = pyqtSignal(bool)  # включить/выключить кнопки списка

    # Сигналы для взаимодействия с main window
    select_point_on_map_requested = pyqtSignal()
    point_selected = pyqtSignal(object, int)  # point, node_id

    def __init__(self, model: RestrictionModel, service: RestrictionService):
        super().__init__()
        self.__model = model
        self.__service = service
        self.__awaiting_point = False

        # Подключаемся к сигналам модели
        self.__model.restrictions_changed.connect(self.__on_restrictions_changed)
        self.__model.current_restriction_id_changed.connect(self.__on_current_id_changed)
        self.__model.editing_mode_changed.connect(self.__on_editing_mode_changed)

    def open_dialog(self):
        """Открыть диалог"""
        self.__load_restrictions()
        self.open_requested.emit()

    def __load_restrictions(self):
        """Загрузить список ограничений из БД в модель"""
        try:
            restrictions = self.__service.get_all_restrictions()
            restriction_records = [self.__dict_to_record(r) for r in restrictions]
            self.__model.set_restrictions(restriction_records)
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки ограничений: {e}")

    def __dict_to_record(self, data: dict) -> RestrictionRecord:
        """Преобразовать словарь в объект RestrictionRecord"""
        return RestrictionRecord(
            id=data.get("id"),
            restriction_type_id=data.get("restriction_type_id", 1),
            name=data.get("name", ""),
            node_id=data.get("node_id"),
            value_num=data.get("value_num"),
            value_text=data.get("value_text", ""),
            comment=data.get("comment", "")
        )

    def __record_to_dict(self, record: RestrictionRecord) -> dict:
        """Преобразовать объект RestrictionRecord в словарь"""
        return {
            "id": record.id,
            "restriction_type_id": record.restriction_type_id,
            "name": record.name,
            "node_id": record.node_id,
            "value_num": record.value_num,
            "value_text": record.value_text,
            "comment": record.comment
        }

    def on_restriction_selected(self, restriction_id: int | None):
        """Обработчик выбора ограничения в списке"""
        if restriction_id is None:
            self.__model.set_current_restriction_id(None)
            self.__model.set_editing_mode(FormMode.VIEW)
            return

        self.__model.set_current_restriction_id(restriction_id)
        self.__load_restriction_to_form(restriction_id)
        self.__model.set_editing_mode(FormMode.VIEW)

    def on_create_restriction(self):
        """Обработчик создания нового ограничения"""
        self.__model.set_current_restriction_id(None)
        self.__model.set_current_restriction_data(None)
        self.__model.set_editing_mode(FormMode.CREATE)

    def on_edit_restriction(self):
        """Обработчик редактирования ограничения"""
        if self.__model.get_current_restriction_id() is not None:
            self.__model.set_editing_mode(FormMode.EDIT)

    def on_cancel_edit(self):
        """Обработчик отмены редактирования"""
        current_id = self.__model.get_current_restriction_id()
        if current_id is not None:
            self.__load_restriction_to_form(current_id)
        else:
            self.__model.set_current_restriction_data(None)
        self.__model.set_editing_mode(FormMode.VIEW)

    def on_save_restriction(self, form_data: dict):
        """Обработчик сохранения ограничения"""
        name = form_data.get("name", "")
        if not name:
            self.show_warning.emit("Введите название ограничения!")
            return

        # Получаем точки из формы
        start_node = form_data.get("start_node")
        mid_nodes = form_data.get("mid_nodes", [])
        end_node = form_data.get("end_node")

        # Собираем все node_id
        node_ids = []
        if start_node is not None:
            node_ids.append(start_node)
        node_ids.extend(mid_nodes)
        if end_node is not None:
            node_ids.append(end_node)

        if not node_ids:
            self.show_warning.emit("Добавьте хотя бы одну точку для ограничения!")
            return

        rt = form_data.get("restriction_type")

        # Собираем данные в зависимости от типа
        value_num = None
        value_text = ""

        if rt == RestrictionType.DIMENSION:
            dim_values = form_data.get("dimension_values", {})
            value_text = f"height={dim_values.get('height', 0)};width={dim_values.get('width', 0)};length={dim_values.get('length', 0)};weight={dim_values.get('weight', 0)}"
        elif rt == RestrictionType.TEMPORARY:
            dates = form_data.get("temporary_dates", {})
            value_text = f"from={dates.get('from', '')};to={dates.get('to', '')}"
        elif rt == RestrictionType.SIMPLE:
            value_text = "simple"

        try:
            current_id = self.__model.get_current_restriction_id()
            editing_mode = self.__model.get_editing_mode()

            # Сохраняем каждую точку отдельно
            for node_id in node_ids:
                record = RestrictionRecord(
                    restriction_type_id=self.__type_to_id(rt),
                    name=name,
                    node_id=node_id,
                    value_num=value_num,
                    value_text=value_text,
                    comment=form_data.get("comment", ""),
                )

                if editing_mode == FormMode.EDIT and current_id is not None:
                    record.id = current_id
                    self.__service.update_restriction(current_id, self.__record_to_dict(record))
                else:
                    self.__service.create_restriction(self.__record_to_dict(record))

            self.__load_restrictions()
            self.__model.set_editing_mode(FormMode.VIEW)
            self.__model.set_current_restriction_id(None)
            self.__model.set_current_restriction_data(None)
            self.show_info.emit("Ограничение сохранено!")
        except Exception as e:
            self.show_error.emit(str(e))

    def on_delete_restriction(self):
        """Обработчик удаления ограничения"""
        current_id = self.__model.get_current_restriction_id()
        if current_id is None:
            return

        try:
            self.__service.delete_restriction(current_id)
            self.__model.set_current_restriction_id(None)
            self.__model.set_current_restriction_data(None)
            self.__model.set_editing_mode(FormMode.VIEW)
            self.__load_restrictions()
            self.show_info.emit("Ограничение удалено!")
        except Exception as e:
            self.show_error.emit(str(e))

    def on_select_point_on_map(self):
        """Запрашиваем у главного окна активировать инструмент выбора"""
        self.__awaiting_point = True
        self.select_point_on_map_requested.emit()

    def on_point_selected(self, point: QgsPointXY, node_id: int):
        """Вызывается из MainWindowController, когда пользователь кликнул на карте"""
        if not self.__awaiting_point:
            return
        self.__awaiting_point = False
        self.point_selected.emit(point, node_id)

    def __load_restriction_to_form(self, restriction_id: int):
        """Загрузить данные ограничения в модель"""
        try:
            r_dict = self.__service.get_restriction_by_id(restriction_id)
            if r_dict:
                record = self.__dict_to_record(r_dict)
                self.__model.set_current_restriction_data(record)
                # Отправляем данные в view
                self.load_restriction_to_form.emit(r_dict)
        except Exception as e:
            print(f"Ошибка загрузки ограничения: {e}")

    def __type_to_id(self, rt: RestrictionType) -> int:
        """Преобразовать тип ограничения в ID"""
        return {
            RestrictionType.SIMPLE: 1,
            RestrictionType.DIMENSION: 2,
            RestrictionType.TEMPORARY: 3,
        }.get(rt, 1)

    def __id_to_type_name(self, type_id: int) -> str:
        """Преобразовать ID типа в название"""
        return {
            1: "Простое",
            2: "По габаритам ТС",
            3: "По времени"
        }.get(type_id, "Простое")

    def get_form_state(self) -> dict:
        """Получить текущее состояние формы для view"""
        current_id = self.__model.get_current_restriction_id()
        editing_mode = self.__model.get_editing_mode()
        current_data = self.__model.get_current_restriction_data()

        restrictions = self.__model.get_restrictions()

        restrictions_for_view = []
        for r in restrictions:
            restrictions_for_view.append({
                "id": r.id,
                "name": r.name,
                "restriction_type_id": r.restriction_type_id,
                "restriction_type_name": self.__id_to_type_name(r.restriction_type_id)
            })

        return {
            "restrictions": restrictions_for_view,
            "current_id": current_id,
            "editing_mode": editing_mode,
            "current_data": current_data
        }

    # ==================== ОБРАБОТЧИКИ СИГНАЛОВ МОДЕЛИ ====================

    def __on_restrictions_changed(self, restrictions: list):
        """Обработчик изменения списка ограничений"""
        restrictions_for_view = []
        for r in restrictions:
            restrictions_for_view.append({
                "id": r.id,
                "name": r.name,
                "restriction_type_id": r.restriction_type_id,
                "restriction_type_name": self.__id_to_type_name(r.restriction_type_id)
            })
        self.load_restrictions_list.emit(restrictions_for_view)

    def __on_current_id_changed(self, restriction_id: int | None):
        """Обработчик изменения текущего ID ограничения"""
        # Отправляем состояние формы
        state = self.get_form_state()
        self.set_list_buttons_enabled.emit(state["current_id"] is not None)

        if restriction_id is None:
            self.clear_form.emit()
            self.set_form_state.emit(FormMode.VIEW)
        else:
            self.set_form_state.emit(FormMode.VIEW)

    def __on_editing_mode_changed(self, mode: FormMode):
        """Обработчик изменения режима редактирования"""
        self.set_form_state.emit(mode)