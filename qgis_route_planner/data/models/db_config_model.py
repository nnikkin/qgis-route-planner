from qgis.PyQt.QtCore import pyqtSignal, QObject

class DbConfigModel(QObject):
    host_changed = pyqtSignal(str)
    port_changed = pyqtSignal(str)
    username_changed = pyqtSignal(str)
    password_changed = pyqtSignal(str)
    database_changed = pyqtSignal(str)
    schema_changed = pyqtSignal(str)
    any_field_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.__host = ""
        self.__port = ""
        self.__username = ""
        self.__password = ""
        self.__database = ""
        self.__schema = ""

        for s in (
                self.host_changed,
                self.port_changed,
                self.username_changed,
                self.password_changed,
                self.database_changed,
        ):
            s.connect(self.__on_any_changed)

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, value):
        self.__host = value
        self.host_changed.emit(value)

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, value):
        self.__port = value
        self.port_changed.emit(value)

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, value):
        self.__password = value
        self.password_changed.emit(value)

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, value):
        self.__username = value
        self.username_changed.emit(value)

    @property
    def database(self):
        return self.__database

    @database.setter
    def database(self, value):
        self.__database = value
        self.database_changed.emit(value)

    @property
    def schema(self):
        return self.__schema

    @schema.setter
    def schema(self, value):
        self.__schema = value
        self.schema_changed.emit(value)

    def validate_values_for_schema(self):
        """Проверка введённых значений, нужных для получения списка схем"""
        return all([self.host, self.port, self.username, self.password, self.database])

    def validate_all_values(self):
        """Проверка всех значений, нужных для подключения"""
        return all([self.host, self.port, self.username, self.password, self.database, self.schema])

    def __on_any_changed(self, _):
        self.any_field_changed.emit()
