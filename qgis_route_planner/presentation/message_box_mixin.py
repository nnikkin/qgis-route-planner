from qgis.PyQt.QtWidgets import QMessageBox, QWidget


class MessageBoxMixin(QWidget):
    def _show_warning(self, message: str, title: str = "Предупреждение", parent = None):
        QMessageBox.warning(parent, title, message, QMessageBox.Ok)

    def _show_info(self, message: str, title: str = "Внимание", parent = None):
        QMessageBox.information(parent, title, message, QMessageBox.Ok)

    def _show_error(self, message: str, title: str = "Ошибка", parent = None):
        QMessageBox.critical(parent, title, message, QMessageBox.Ok)

    def _show_critical(self, message: str, title: str = "Критический сбой", parent = None):
        QMessageBox.critical(parent, title, message, QMessageBox.Ok)

    def _show_question(self, message: str, title: str = "", parent = None) -> bool:
        q = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return True if q == QMessageBox.Yes else False