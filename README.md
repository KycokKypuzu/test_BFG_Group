## Запуск

Требуется Python 3.10+ и Docker.

```powershell
docker compose up -d
pip install -r requirements.txt
python -m alembic upgrade head
```

Запустить API:

```powershell
python inventory_api.py
```

В отдельном терминале запустить Worker:

```powershell
python analytics_worker.py
```

API доступен по адресу `http://127.0.0.1:8000`.

## Тесты

```powershell
python -m pytest tests/test_integration.py -v
```