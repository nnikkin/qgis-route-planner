from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services import RestrictionService

from qgis.PyQt.QtCore import pyqtSignal, Qt, pyqtSlot
from qgis.PyQt.QtWidgets import QListWidgetItem, QMessageBox
from qgis.core import QgsPointXY

from ..controllers import BaseController
from ..data.restrictions import RestrictionRecord, RestrictionType


class RestrictionDialogController(BaseController):
    """Контроллер диалога ограничений"""

    select_point_on_map_requested = pyqtSignal()
    point_selected = pyqtSignal(object, int)

    def __init__(
            self,
            service: RestrictionService,
    ):
        super().__init__()
        self.__service = service
        self.__view = None
        self.__current_id: int | None = None
        self.__awaiting_point = False

        self.__initialize()

    def __initialize(self):
        self.__load_restrictions()
        self.__view.clear_form()
        self.__view.set_form_enabled(False)
        self.__view.set_list_buttons_enabled(False)

    def __load_restrictions(self):
        try:
            restrictions = self.__service.get_all_restrictions()
            self.__view.restrictionListWidget.clear()
            for r in restrictions:
                label = (
                    f"{r.get('name', '—')} "
                    f"[{r.get('restriction_type_name', '')}]"
                )
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, r.get("id"))
                self.__view.restrictionListWidget.addItem(item)
        except Exception as e:
            print(f"Ошибка загрузки ограничений: {e}")

    @pyqtSlot()
    def on_restriction_selected(self):
        items = self.__view.restrictionListWidget.selectedItems()
        if not items:
            self.__view.set_list_buttons_enabled(False)
            self.__view.set_form_enabled(False)
            self.__view.clear_form()
            self.__current_id = None
            return

        self.__current_id = items[0].data(Qt.ItemDataRole.UserRole)
        self.__load_restriction_to_form(self.__current_id)
        self.__view.set_list_buttons_enabled(True)
        self.__view.set_form_enabled(False)

    @pyqtSlot()
    def on_create_restriction(self):
        self.__current_id = None
        self.__view.restrictionListWidget.clearSelection()
        self.__view.clear_form()
        self.__view.set_form_enabled(True)
        self.__view.set_list_buttons_enabled(False)

    @pyqtSlot()
    def on_edit_restriction(self):
        if self.__current_id is None:
            return
        self.__view.set_form_enabled(True)

    @pyqtSlot()
    def on_cancel_edit(self):
        if self.__current_id is not None:
            self.__load_restriction_to_form(self.__current_id)
        else:
            self.__view.clear_form()
        self.__view.set_form_enabled(False)

    @pyqtSlot()
    def on_save_restriction(self):
        name = self.__view.get_name()
        if not name:
            QMessageBox.warning(self.__view, "", "Введите название ограничения!", QMessageBox.Ok)
            return

        rt = self.__view.get_current_type()
        node_ids = self.__view.get_node_ids()

        if not node_ids:
            QMessageBox.warning(self.__view, "", "Добавьте хотя бы одну точку для ограничения!", QMessageBox.Ok)
            return

        # Собираем данные в зависимости от типа
        value_num = None
        value_text = ""

        if rt == RestrictionType.DIMENSION:
            h, w, l, weight = self.__view.get_dimension_values()
            value_text = f"height={h};width={w};length={l};weight={weight}"
        elif rt == RestrictionType.TEMPORARY:
            date_from, date_to = self.__view.get_temporary_dates()
            value_text = f"from={date_from.toString('yyyy-MM-dd HH:mm')};to={date_to.toString('yyyy-MM-dd HH:mm')}"
        elif rt == RestrictionType.SIMPLE:
            value_text = "simple"

        try:
            # Сохраняем каждую точку отдельно
            for node_id in node_ids:
                record = RestrictionRecord(
                    restriction_type_id=self.__type_to_id(rt),
                    name=name,
                    node_id=node_id,
                    value_num=value_num,
                    value_text=value_text,
                    comment=self.__view.get_comment(),
                )
                if self.__current_id is not None:
                    self.__service.update_restriction(self.__current_id, record)
                else:
                    self.__service.create_restriction(record)

            self.__load_restrictions()
            self.__view.set_form_enabled(False)
            self.__view.set_list_buttons_enabled(False)
            self.__view.clear_form()
            self.__current_id = None

            QMessageBox.information(
                self.__view, "",
                "Ограничение сохранено!",
                QMessageBox.Ok
            )
        except Exception as e:
            QMessageBox.critical(self.__view, "Ошибка", str(e), QMessageBox.Ok)

    @pyqtSlot()
    def on_delete_restriction(self):
        if self.__current_id is None:
            return
        reply = QMessageBox.question(
            self.__view, "",
            "Удалить это ограничение?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.__service.delete_restriction(self.__current_id)
            self.__current_id = None
            self.__view.clear_form()
            self.__view.set_form_enabled(False)
            self.__view.set_list_buttons_enabled(False)
            self.__load_restrictions()
        except Exception as e:
            QMessageBox.critical(self.__view, "Ошибка", str(e), QMessageBox.Ok)

    @pyqtSlot()
    def on_select_point_on_map(self):
        """Запрашиваем у главного окна активировать инструмент выбора"""
        self.__awaiting_point = True
        self.select_point_on_map_requested.emit()

    def on_point_selected(self, point: QgsPointXY, node_id: int):
        """Вызывается из MainWindowController когда пользователь кликнул на карте"""
        if not self.__awaiting_point:
            return
        self.__awaiting_point = False
        self.__view.add_node_to_list(node_id, point.x(), point.y())
        self.__view.show()

    # --- Вспомогательное ---
    def __load_restriction_to_form(self, restriction_id: int):
        try:
            r = self.__service.get_restriction_by_id(restriction_id)
            if not r:
                return
            self.__view.load_restriction_to_form(r)
        except Exception as e:
            print(f"Ошибка загрузки ограничения: {e}")

    def __type_to_id(self, rt: RestrictionType) -> int:
        return {
            RestrictionType.SIMPLE: 1,
            RestrictionType.DIMENSION: 2,
            RestrictionType.TEMPORARY: 3,
        }.get(rt, 1)

    def __id_to_type(self, type_id: int) -> RestrictionType:
        return {
            1: RestrictionType.SIMPLE,
            2: RestrictionType.DIMENSION,
            3: RestrictionType.TEMPORARY,
        }.get(type_id, RestrictionType.SIMPLE)