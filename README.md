# ManageTime

Веб-приложение для учёта времени по проектам и задачам. ManageTime помогает фиксировать продолжительность работы, отслеживать активные таймеры и выгружать статистику в Excel.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.2-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)

> Учебный проект, созданный в 2022 году и обновлённый для безопасного локального запуска.

<p align="center">
  <img src="static/img/icon.png" alt="Логотип ManageTime" width="180">
</p>

## Возможности

- регистрация и авторизация пользователей;
- создание и редактирование проектов;
- добавление ссылки на репозиторий GitHub;
- создание и редактирование задач;
- запуск, остановка и сброс таймера;
- подсчёт общего времени по проекту;
- поиск по списку проектов и задач;
- выгрузка статистики проекта или отдельной задачи в `.xlsx`;
- административная панель для локального управления данными.

## Технологии

- Python, Flask и Waitress;
- SQLAlchemy и SQLite;
- Flask-Login, Flask-WTF и Flask-Admin;
- XlsxWriter;
- Bootstrap и JavaScript.

## Запуск

1. Клонируйте репозиторий и перейдите в его каталог.
2. Создайте и активируйте виртуальное окружение:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Установите зависимости:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Задайте секретный ключ и, при необходимости, логин администратора:

   ```powershell
   $env:MANAGETIME_SECRET_KEY = "replace-with-a-random-secret"
   $env:MANAGETIME_ADMIN_LOGIN = "admin"
   ```

5. Запустите приложение:

   ```powershell
   python app.py
   ```

6. Откройте [http://127.0.0.1:5001](http://127.0.0.1:5001).

Чтобы войти в административную панель, зарегистрируйтесь с логином, указанным в `MANAGETIME_ADMIN_LOGIN`, и откройте `/admin`. Дополнительные параметры приведены в [`.env.example`](.env.example).

## База данных

При первом запуске приложение автоматически создаёт локальную базу `db/manage_time.db`. Она добавлена в `.gitignore`, поэтому учётные записи, проекты и история таймеров не попадут в репозиторий.

## Структура проекта

```text
ManageTime/
├── app.py                 # маршруты, API, экспорт и запуск приложения
├── data/                  # модели SQLAlchemy и подключение к SQLite
├── forms/                 # формы Flask-WTF
├── static/                # стили, JavaScript и изображения
├── templates/             # HTML-шаблоны
└── requirements.txt       # зависимости Python
```

## Ограничения

Проект рассчитан на локальный запуск и демонстрацию. Перед полноценным размещением в интернете ему потребуются миграции базы данных, журналирование и автоматические тесты.

## Автор

[Александр Зейферт](https://github.com/Mr-Zoom-13)
