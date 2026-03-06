from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QDialog
)

from ..data.restrictions import RestrictionRecord


class PointRestrictionDialog(QDialog):
    """Диалог создания ограничения для выбранной точки карты."""

    def __init__(self, node_id: int, restriction_types: list[dict], parent=None):
        super().__init__(parent)
        self.__restriction_types = restriction_types
        self.__setup_ui(node_id)
        self.__load_types()

    def setupUi(self):
        self.setWindowTitle("Ограничение точки")
        self.resize(420, 260)

        self.__main_layout = QVBoxLayout(self)
        self.__form_layout = QFormLayout()

        self.__type_combo = QComboBox(self)
        self.__name_edit = QLineEdit(self)
        self.__node_id_spin = QSpinBox(self)
        self.__value_num_spin = QDoubleSpinBox(self)
        self.__value_text_edit = QLineEdit(self)
        self.__comment_edit = QLineEdit(self)

        self.__node_id_spin.setMaximum(2147483647)
        self.__node_id_spin.setValue(self.__node_id)
        self.__node_id_spin.setEnabled(False)

        self.__value_num_spin.setMaximum(999999999.0)

        self.__form_layout.addRow(QLabel("Тип"), self.__type_combo)
        self.__form_layout.addRow(QLabel("Название"), self.__name_edit)
        self.__form_layout.addRow(QLabel("Node ID"), self.__node_id_spin)
        self.__form_layout.addRow(QLabel("Число"), self.__value_num_spin)
        self.__form_layout.addRow(QLabel("Текст"), self.__value_text_edit)
        self.__form_layout.addRow(QLabel("Комментарий"), self.__comment_edit)

        self.__main_layout.addLayout(self.__form_layout)

        self.__button_layout = QHBoxLayout()
        self.__button_layout.addStretch(1)

        self.__ok_button = QPushButton("ОК", self)
        self.__cancel_button = QPushButton("Отмена", self)
        self.__ok_button.clicked.connect(self.__accept_dialog)
        self.__cancel_button.clicked.connect(self.reject)

        self.__button_layout.addWidget(self.__ok_button)
        self.__button_layout.addWidget(self.__cancel_button)
        self.__main_layout.addLayout(self.__button_layout)
        self.__name_edit.setFocus()

    def __load_types(self):
        self.__type_combo.clear()
        for row in self.__restriction_types:
            self.__type_combo.addItem(
                row.get("name", ""),
                row.get("restriction_type_id"),
            )

        if self.__type_combo.count() == 0:
            self.__type_combo.addItem("Без типа", 1)

    def __accept_dialog(self):
        if not self.__name_edit.text().strip():
            QMessageBox.warning(
                self,
                "Внимание",
                "Введите название ограничения!",
                QMessageBox.Ok,
            )
            return

        self.accept()

    def get_restriction(self) -> RestrictionRecord:
        return RestrictionRecord(
            restriction_type_id=self.__type_combo.currentData() or 1,
            name=self.__name_edit.text().strip(),
            node_id=self.__node_id_spin.value(),
            value_num=self.__value_num_spin.value(),
            value_text=self.__value_text_edit.text().strip(),
            comment=self.__comment_edit.text().strip(),
        )
