# Поиск маршрутов для QGIS
---
## RU
Данный плагин рассчитан на построение марщрутов на основе данных OSM, хранящихся в базе данных PostgreSQL.
Для нахождения маршрутов используется реализация алгоритма k-кратчайших путей из  pgRouting. Плагин ищет до 3 различных вариантов маршрута из точки А в точку Б (учитывая промежуточные точки в заданном порядке, если также были указаны). Для связи с БД используется библиотека psycopg.
Пользователь может создавать профили транспортных средств и задавать различные ограничения, которые должны быть учтены при построении маршрутов. Также доступен учёт погодных условий с помошью сервиса OpenWeatherMap (требуется ключ к API).

### Зависимости
---
- QGIS версии 3.44 и выше (QGIS 4.x не поддерживается)
- Python 3.12 и выше
- psycopg 3.3 и выше
- PostgreSQl 18.1 и выше
- pgRouting 4.0 и выше

### Установка
---

1. Найдите и выполните в меню Модули команду Управление модулями...
2. Перейдите на вкладку Установить из ZIP файла... и введите путь до файла архива с плагином
3. Нажмите кнопку Установить модуль

---
## EN
QgisRoutePlanner can calculate routes based on OSM data from PostgreSQL using KSP algorithm.
This plugin uses pgRouting for calculations and psycopg for accessing the database.
User can create vehicle profiles and add restrictions to the road graph that must be taken into account when searching for routes. Plugin also supports including weather data into route calculating if they have an API key for OpenWeatherMap service.

### Requirements
---
- QGIS version 3.44 and up (incompatible with QGIS 4.x)
- Python 3.12 and up
- psycopg 3.3 and up
- PostgreSQl 18.1 and up
- pgRouting 4.0 and up

### Installation
---

1. Go to Plugins > Manage and Install Plugins...
2. Go to Install from ZIP... > enter the path to the plugin ZIP file
3. Click Install Plugin
