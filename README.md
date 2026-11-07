# Sleep Tracker — вариант 19

Приложение для учёта сна. Qt-клиент запускается локально в Ubuntu/WSL2, FastAPI работает в Docker и подключается к уже существующему PostgreSQL-контейнеру `sleep-tracker-postgres`. Compose **не создаёт и не удаляет PostgreSQL**.

## Архитектура
- `desktop/` — интерфейс PySide6, обращается к `http://localhost:8000`.
- `api/` — FastAPI REST API в Docker.
- PostgreSQL — твой существующий контейнер, опубликованный на порту `5438`; он остаётся без изменений.
- `tests/` — pytest-тесты API с временной SQLite, реальные данные PostgreSQL не затрагиваются.

## Запуск API

Убедись, что существующий контейнер запущен: `docker ps`. В корне проекта выполни:

```bash
cp .env.example .env
# Если пароль postgres отличается от 1234, поправь DB_PASSWORD в .env
docker compose up --build -d
docker compose ps
docker compose logs -f api
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs  
Проверка подключения к БД: http://localhost:8000/health

API подключается к опубликованному порту существующей базы: `host.docker.internal:5438`, база `postgres`, пользователь `postgres`. Если база или пользователь у тебя другие, измени `DB_NAME` и `DB_USER` в `.env`. Пароль должен совпадать с паролем существующего PostgreSQL.

Остановить только API: `docker compose down`. Эта команда не останавливает и не удаляет контейнер `sleep-tracker-postgres`. Не используй `docker compose down -v` для этой конфигурации — PostgreSQL volume здесь не создаётся, но эта команда всё равно не нужна.

При первом запуске API автоматически создаст таблицу приложения `sleep_records`, если её ещё нет, внутри базы `postgres`. Существующие таблицы и данные не удаляются.

## Запуск Qt-клиента в Ubuntu/WSL2

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r desktop/requirements.txt
python desktop/main.py
```

Для окна Qt требуется поддержка GUI в WSL2 (WSLg).

## Запуск тестов

```bash
python3 -m venv .venv-test
source .venv-test/bin/activate
pip install -r tests/requirements.txt
python -m pytest -v
```

Тесты используют временную SQLite в памяти и не меняют данные PostgreSQL.

## Методы API

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/health` | Проверка API и БД |
| GET | `/sleep` | Список записей |
| POST | `/sleep` | Создание записи |
| GET | `/sleep/{id}` | Получение записи |
| PUT | `/sleep/{id}` | Изменение записи |
| DELETE | `/sleep/{id}` | Удаление записи |
| GET | `/stats` | Статистика сна |

Пример JSON для `POST /sleep`:

```json
{
  "sleep_start": "2026-11-02T23:00:00",
  "sleep_end": "2026-11-03T07:00:00",
  "quality": 4,
  "notes": "Хорошо выспался"
}
```

## Работа через браузер

После запуска API открой в браузере Windows или WSL2 адрес `http://localhost:8000/`. На странице можно добавлять записи сна, выбирать строку для изменения, сохранять изменения, удалять записи и смотреть статистику. Документация API остаётся доступна по адресу `http://localhost:8000/docs`.

