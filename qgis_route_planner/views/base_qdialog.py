from qgis.PyQt.QtWidgets import QDialog

class BaseQDialog(QDialog):
    def setupUi(self):
        raise NotImplementedError

    def retranslateUi(self):
        raise NotImplementedError

    def closeEvent(self, event):
        raise NotImplementedError