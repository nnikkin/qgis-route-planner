from qgis.PyQt.QtWidgets import QMessageBox

class MessageBoxMixin:
    def _show_warning(self, parent, message: str, title: str = "Предупреждение"):
        QMessageBox.warning(parent, title, message, QMessageBox.Ok)

    def _show_info(self, parent, message: str, title: str = "Внимание"):
        QMessageBox.information(parent, title, message, QMessageBox.Ok)

    def _show_error(self, parent, message: str, title: str = "Ошибка"):
        QMessageBox.critical(parent, title, message, QMessageBox.Ok)

    def _show_critical(self, parent, message: str, title: str = "Критический сбой"):
        QMessageBox.critical(parent, title, message, QMessageBox.Ok)

    def _show_question(self, parent, message: str, title: str = "") -> bool:
        q = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return True if q == QMessageBox.Yes else False