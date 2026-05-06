# 1. Определяем путь к папке, где лежит сам скрипт
$scriptDir = $PSScriptRoot

# 2. Указываем путь к папке, которую нужно запаковать
$sourcePath = Join-Path -Path $scriptDir -ChildPath "qgis_route_planner"

# 3. Указываем имя и путь для архива
$destinationPath = Join-Path -Path $scriptDir "qgis_route_planner.zip"

# 4. Проверяем, существует ли папка перед архивацией
if (Test-Path $sourcePath) {
    # Если архив уже существует, удаляем его (чтобы не было ошибки или дозаписи)
    if (Test-Path $destinationPath) { Remove-Item $destinationPath -Force }

    # 5. Создаем архив
    Compress-Archive -Path $sourcePath -DestinationPath $destinationPath
    Write-Host "ARCHIVE CREATED: $destinationPath" -ForegroundColor Green
}
else {
    Write-Error "qgis_route_planner FOLDER NOT FOUND IN $scriptDir"
}