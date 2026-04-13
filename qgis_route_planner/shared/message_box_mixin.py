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