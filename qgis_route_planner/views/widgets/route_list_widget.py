# -*- coding: utf-8 -*-
from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QToolBox, QWidget

from qgis_route_planner import resources


class RouteListWidget(QToolBox):
    route_selected = pyqtSignal(int)
    route_save_requested = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.__pages: list[QWidget] = []
        self.setupUi()

    def setupUi(self):
        self.setObjectName("RouteListWidget")
        self.resize(400, 300)

        font = QtGui.QFont()
        font.setBold(True)
        font.setItalic(False)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.setFont(font)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setObjectName("routeListWidget")
        self.currentChanged.connect(self.route_selected.emit)

        self.retranslateUi()
        self.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Form", "Виджет списка маршрутов"))

    def add_page(self, route_id: int, route: list, info: dict):
        route_page = QWidget()
        route_page.setObjectName(f"route_page_{route_id}")

        page_layout = QtWidgets.QVBoxLayout(route_page)
        page_layout.setContentsMargins(5, 5, 5, 5)
        page_layout.setSpacing(8)

        # --- Кнопки ---
        buttons_layout = QtWidgets.QHBoxLayout(route_page)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        buttons_layout.setSpacing(8)

        save_btn = QtWidgets.QPushButton()
        __icon = QtGui.QIcon()
        __icon.addPixmap(QtGui.QPixmap(":/route_list_icons/save_icon"))
        save_btn.setIcon(__icon)
        save_btn.setObjectName(f"save_btn_{route_id}")
        save_btn.clicked.connect(lambda checked=False, rid=route_id: self.route_save_requested.emit(rid))
        buttons_layout.addWidget(save_btn)
        page_layout.addLayout(buttons_layout)

        # --- Группа информации ---
        info_group = QtWidgets.QGroupBox("Информация", route_page)
        info_group.setFlat(True)
        info_form = QtWidgets.QFormLayout(info_group)
        info_form.setContentsMargins(5, 5, 5, 5)

        time_label = QtWidgets.QLabel("Время в пути:")
        time_value = QtWidgets.QLabel(f"{info['time_minutes']:.0f} мин")
        dist_label = QtWidgets.QLabel("Длина маршрута:")
        dist_value = QtWidgets.QLabel(f"{info['distance_km']:.2f} км")

        info_form.addRow(time_label, time_value)
        info_form.addRow(dist_label, dist_value)

        page_layout.addWidget(info_group)

        # --- Группа инструкций ---
        instr_group = QtWidgets.QGroupBox("Инструкции", route_page)
        instr_group.setFlat(True)
        instr_layout = QtWidgets.QVBoxLayout(instr_group)
        instr_layout.setContentsMargins(5, 5, 5, 5)

        text_browser = QtWidgets.QTextBrowser(instr_group)
        text_browser.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        text_browser.setText(self.__generate_instructions(route))
        instr_layout.addWidget(text_browser)

        page_layout.addWidget(instr_group)
        # инструкции должны занимать всё оставшееся место
        page_layout.setStretch(0, 0)
        page_layout.setStretch(1, 1)

        self.addItem(route_page, f"Маршрут №{route_id + 1}")
        self.__pages.append(route_page)

    def __generate_instructions(self, route: list) -> str:
        """Генерирует текстовые инструкции по маршруту"""
        if not route:
            return "<div>Нет инструкций</div>"
        instructions = []
        total_distance = 0
        for i, edge in enumerate(route):
            total_distance += edge['cost']
            distance_km = total_distance / 1000
            if i == 0:
                action = "Старт"
            elif i == len(route) - 1:
                action = "Финиш"
            else:
                action = "Продолжать движение"

            instructions.append(f"""
            <div>
                <b>{i + 1}.</b> {action}<br>
                <span font-size: 11px;">
                    Проехать: {distance_km:.2f} км
                </span>
            </div>
            """)

        return "".join(instructions)

    def clear(self):
        while self.count() > 0:
            widget = self.widget(0)
            self.removeItem(0)
            if widget:
                widget.deleteLater()
