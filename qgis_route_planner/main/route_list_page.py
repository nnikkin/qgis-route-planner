from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QLabel,
    QTextBrowser,
    QSizePolicy
)

from qgis.PyQt.QtGui import QIcon, QPixmap

from qgis.PyQt.QtCore import pyqtSignal

from qgis_route_planner import resources

class RouteListPage(QWidget):
    route_save_requested = pyqtSignal(int)

    def __init__(self, route_id: int, route: list, info: dict, parent = None):
        super().__init__(parent)

        self.__route_id = route_id
        self.__route = route
        self.__info = info

        self.__setupUi()

    def __setupUi(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(5, 5, 5, 5)
        page_layout.setSpacing(8)

        # --- Кнопки ---
        buttons_layout = QHBoxLayout(self)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        buttons_layout.setSpacing(8)

        save_btn = QPushButton()
        __icon = QIcon()
        __icon.addPixmap(QPixmap(":/route_list_icons/save_icon"))
        save_btn.setIcon(__icon)
        save_btn.setObjectName(f"save_btn_{self.__route_id}")
        save_btn.clicked.connect(lambda checked=False, rid=self.__route_id: self.route_save_requested.emit(rid))
        buttons_layout.addWidget(save_btn)
        page_layout.addLayout(buttons_layout)

        # --- Группа информации ---
        info_group = QGroupBox("Информация", self)
        info_group.setFlat(True)
        info_form = QFormLayout(info_group)
        info_form.setContentsMargins(5, 5, 5, 5)

        time_label = QLabel("Время в пути:")
        time_value = QLabel(f"{self.__info['time_minutes']:.0f} мин")
        dist_label = QLabel("Длина маршрута:")
        dist_value = QLabel(f"{self.__info['distance_km']:.2f} км")

        info_form.addRow(time_label, time_value)
        info_form.addRow(dist_label, dist_value)

        page_layout.addWidget(info_group)

        # --- Группа инструкций ---
        instr_group = QGroupBox("Инструкции", self)
        instr_group.setFlat(True)
        instr_layout = QVBoxLayout(instr_group)
        instr_layout.setContentsMargins(5, 5, 5, 5)

        text_browser = QTextBrowser(instr_group)
        text_browser.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        text_browser.setText(self.__generate_instructions())
        instr_layout.addWidget(text_browser)

        page_layout.addWidget(instr_group)

        page_layout.setStretch(0, 0)
        page_layout.setStretch(1, 1)

        self.addItem(self, f"Маршрут №{self.__route_id + 1}")

    def __generate_instructions(self) -> str:
        """ Генерирует текстовые инструкции по маршруту """
        if not self.__route:
            return "<div>Нет инструкций</div>"
        instructions = []
        total_distance = 0
        for i, edge in enumerate(self.__route):
            total_distance += edge.get('length_m', 0)
            distance_km = total_distance / 1000
            if i == 0:
                action = "Старт"
            elif i == len(self.__route) - 1:
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