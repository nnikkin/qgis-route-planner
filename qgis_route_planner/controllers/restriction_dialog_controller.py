from qgis.PyQt.QtCore import QObject, pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QListWidgetItem, QMessageBox

from qgis_route_planner.models.restrictions.restriction_record import RestrictionRecord
from qgis_route_planner.repositories.db_connection import DbConnection
from qgis_route_planner.services.restriction_service import RestrictionService
from qgis_route_planner.views.settings_view import SettingsDialog


class RestrictionWindowController(QObject):
    """Контроллер окна ограничений"""

    restriction_saved = pyqtSignal(DbConnection)

    def __init__(self, settings_dialog: SettingsDialog, restriction_service: RestrictionService):
        super().__init__()
        self.__settings_dialog: SettingsDialog = settings_dialog
        self.__restriction_service: RestrictionService = restriction_service
        self.__current_restriction_id: int = None

        self.__connect_signals()
        self.__initialize()

    def __connect_signals(self):
        self.__settings_dialog.createRestrictionButton.clicked.connect(self.__create_new_restriction)
        self.__settings_dialog.editRestrictionButton.clicked.connect(self.__edit_restriction)
        self.__settings_dialog.deleteRestrictionButton.clicked.connect(self.__delete_restriction)
        self.__settings_dialog.saveRestrictionButton.clicked.connect(self.__save_restriction)
        self.__settings_dialog.cancelRestrictionButton.clicked.connect(self.__cancel_edit)
        self.__settings_dialog.restrictionsListWidget.itemSelectionChanged.connect(self.__on_restriction_selected)

    def __set_restriction_mode(self, mode: str):
        is_edit_mode = mode == "edit"
        has_selection = mode == "view"

        self.__enable_restriction_form(is_edit_mode)
        self.__settings_dialog.saveRestrictionButton.setEnabled(is_edit_mode)
        self.__settings_dialog.cancelRestrictionButton.setEnabled(is_edit_mode)
        self.__settings_dialog.editRestrictionButton.setEnabled(has_selection)
        self.__settings_dialog.deleteRestrictionButton.setEnabled(has_selection)

    def __create_new_restriction(self):
        self.__current_restriction_id = None
        self.__clear_restriction_form()
        self.__settings_dialog.restrictionsListWidget.clearSelection()
        self.__set_restriction_mode("edit")
        self.__settings_dialog.restrictionNameEdit.setFocus()

    def __edit_restriction(self):
        if self.__current_restriction_id is None:
            return
        self.__set_restriction_mode("edit")
        self.__settings_dialog.restrictionNameEdit.setFocus()

    def __save_restriction(self):
        name = self.__settings_dialog.restrictionNameEdit.text().strip()
        if not name:
            QMessageBox.warning(
                self.__settings_dialog,
                "",
                "Введите название ограничения!",
                QMessageBox.Ok
            )
            return

        restriction = RestrictionRecord(
            restriction_type_id=self.__settings_dialog.restrictionTypeComboBox.currentData() or 1,
            name=name,
            node_id=self.__settings_dialog.restrictionNodeIdSpinBox.value(),
            value_num=self.__settings_dialog.restrictionValueNumSpinBox.value(),
            value_text=self.__settings_dialog.restrictionValueTextEdit.text().strip(),
            comment=self.__settings_dialog.restrictionCommentEdit.text().strip(),
        )

        try:
            if self.__current_restriction_id is not None:
                self.__restriction_service.update_restriction(self.__current_restriction_id, restriction)
                message = "Ограничение успешно обновлено!"
            else:
                self.__restriction_service.create_restriction(restriction)
                message = "Ограничение успешно создано!"

            self.__load_restrictions()
            self.__cancel_edit()

            QMessageBox.information(
                self.__settings_dialog,
                "",
                message,
                QMessageBox.Ok,
            )
        except Exception as e:
            QMessageBox.critical(
                self.__settings_dialog,
                "Ошибка",
                f"Ошибка сохранения ограничения: {str(e)}",
                QMessageBox.Ok,
            )

    def __delete_restriction(self):
        if self.__current_restriction_id is None:
            return

        reply = QMessageBox.question(
            self.__settings_dialog,
            "",
            f"Вы уверены, что хотите удалить ограничение '{self.__settings_dialog.restrictionNameEdit.text()}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.__restriction_service.delete_restriction(self.__current_restriction_id)
            self.__load_restrictions()
            self.__cancel_edit()
            QMessageBox.information(
                self.__settings_dialog,
                "",
                "Ограничение успешно удалено!",
                QMessageBox.Ok
            )
        except Exception as e:
            QMessageBox.critical(
                self.__settings_dialog,
                "",
                f"Ошибка удаления ограничения: {str(e)}",
                QMessageBox.Ok
            )

    def __on_restriction_selected(self):
        selected_items = self.__settings_dialog.restrictionsListWidget.selectedItems()
        if not selected_items:
            self.__cancel_edit()
            return

        restriction_id = selected_items[0].data(Qt.UserRole)
        self.__current_restriction_id = restriction_id
        self.__load_restriction_to_form(restriction_id)
        self.__set_restriction_mode("view")

    def __load_restriction_to_form(self, restriction_id: int):
        try:
            restriction_data = self.__restriction_service.get_restriction_by_id(restriction_id)
            if not restriction_data:
                self.__cancel_edit()
                return

            types = self.__restriction_service.get_restriction_types()
            self.__settings_dialog.restrictionTypeComboBox.clear()
            for row in types:
                self.__settings_dialog.restrictionTypeComboBox.addItem(
                    row.get("name", ""),
                    row.get("restriction_type_id"),
                )

            type_index = self.__settings_dialog.restrictionTypeComboBox.findData(
                restriction_data.get("restriction_type_id")
            )
            if type_index >= 0:
                self.__settings_dialog.restrictionTypeComboBox.setCurrentIndex(type_index)

            self.__settings_dialog.restrictionNameEdit.setText(restriction_data.get("name", ""))
            self.__settings_dialog.restrictionNodeIdSpinBox.setValue(int(restriction_data.get("node_id") or 0))
            self.__settings_dialog.restrictionValueNumSpinBox.setValue(float(restriction_data.get("value_num") or 0))
            self.__settings_dialog.restrictionValueTextEdit.setText(restriction_data.get("value_text", ""))
            self.__settings_dialog.restrictionCommentEdit.setText(restriction_data.get("comment", ""))
        except Exception as e:
            print(f"Error loading restriction: {e}")

    def __load_restrictions(self):
        try:
            restrictions = self.__restriction_service.get_all_restrictions()
            self.__settings_dialog.restrictionsListWidget.clear()

            for restriction in restrictions:
                item = QListWidgetItem(
                    f"{restriction.get('name', 'Без названия')} "
                    f"({restriction.get('restriction_type_name', '')}) "
                    f"node={restriction.get('node_id', '')}"
                )
                item.setData(Qt.UserRole, restriction.get("id"))
                self.__settings_dialog.restrictionsListWidget.addItem(item)
        except Exception as e:
            print(f"Error loading restrictions: {e}")

    def __clear_restriction_form(self):
        self.__settings_dialog.restrictionNameEdit.clear()
        self.__settings_dialog.restrictionNodeIdSpinBox.setValue(0)
        self.__settings_dialog.restrictionValueNumSpinBox.setValue(0)
        self.__settings_dialog.restrictionValueTextEdit.clear()
        self.__settings_dialog.restrictionCommentEdit.clear()

    def __enable_restriction_form(self, enabled: bool):
        self.__settings_dialog.restrictionTypeComboBox.setEnabled(enabled)
        self.__settings_dialog.restrictionNameEdit.setEnabled(enabled)
        self.__settings_dialog.restrictionNodeIdSpinBox.setEnabled(enabled)
        self.__settings_dialog.restrictionValueNumSpinBox.setEnabled(enabled)
        self.__settings_dialog.restrictionValueTextEdit.setEnabled(enabled)
        self.__settings_dialog.restrictionCommentEdit.setEnabled(enabled)

    def __cancel_edit(self):
        self.__current_restriction_id = None
        self.__clear_restriction_form()
        self.__set_restriction_mode("empty")
        self.__settings_dialog.restrictionsListWidget.clearSelection()

    def __initialize(self):
        self.__restriction_service.ensure_default_types()
        self.__load_types()
        self.__load_restrictions()
        self.__cancel_edit()

    def reload(self):
        """Перечитывает типы и список ограничений после смены подключения."""
        self.__initialize()

    def __load_types(self):
        self.__settings_dialog.restrictionTypeComboBox.clear()
        for row in self.__restriction_service.get_restriction_types():
            self.__settings_dialog.restrictionTypeComboBox.addItem(
                row.get("name", ""),
                row.get("restriction_type_id"),
            )
