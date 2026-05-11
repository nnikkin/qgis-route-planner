from qgis.PyQt.QtWidgets import QMessageBox

class MessageBoxMixin:
    def _show_warning(self, message: str, title: str = "Предупреждение"):
        QMessageBox.warning(self.parent(), title, message, QMessageBox.Ok)

    def _show_info(self, message: str, title: str = "Внимание"):
        QMessageBox.information(self.parent(), title, message, QMessageBox.Ok)

    def _show_error(self, message: str, title: str = "Ошибка"):
        QMessageBox.critical(self.parent(), title, message, QMessageBox.Ok)

    def _show_critical(self, message: str, title: str = "Критический сбой"):
        QMessageBox.critical(self.parent(), title, message, QMessageBox.Ok)

    def _show_question(self, message: str, title: str = "") -> bool:
        q = QMessageBox.question(
            self.parent(),
            title,
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return True if q == QMessageBox.Yes else False

    def _show_non_modal(self, message: str, title: str = "") -> QMessageBox:
        msg_box = QMessageBox(self.parent())
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setModal(False)
        msg_box.addButton(QMessageBox.Ok)
        msg_box.addButton(QMessageBox.Cancel)
        msg_box.show()

        return msg_box