# Sleep Tracker — вариант 19

Приложение для учёта сна: Qt-клиент, веб-интерфейс и FastAPI в Docker с существующим PostgreSQL-контейнером `sleep-tracker-postgres` (Compose его не создаёт и не удаляет).

## Архитектура
- `desktop/` — PySide6-клиент, работает с `http://localhost:8000`.
- `api/` — FastAPI REST API в Docker.
- `tests/` — pytest-тесты API на временной SQLite.

## Запуск API

```bash
cp .env.example .env
# если пароль postgres не 1234, поправь DB_PASSWORD в .env
docker compose up --build -d
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Проверка БД: http://localhost:8000/health

Подключение: `host.docker.internal:5438`, база `postgres`, пользователь `postgres` (меняется через `DB_NAME`, `DB_USER`, `DB_PASSWORD` в `.env`). Таблица `sleep_records` создаётся автоматически.

Остановить API: `docker compose down`.

## Запуск Qt-клиента

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r desktop/requirements.txt
python desktop/main.py
```

Логи доступны в меню «Логи».

## Запуск тестов

```bash
python3 -m venv .venv-test
source .venv-test/bin/activate
pip install -r tests/requirements.txt
python -m pytest -v
```

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

Пример `POST /sleep`:

```json
{
  "sleep_start": "2026-11-02T23:00:00",
  "sleep_end": "2026-11-03T07:00:00",
  "quality": 4,
  "notes": "Хорошо выспался"
}
```

## Веб-интерфейс

Открой `http://localhost:8000/`: добавление, изменение и удаление записей, график и статистика.
