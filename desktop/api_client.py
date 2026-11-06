import os
import requests
from exceptions import ApiConnectionError

API_URL = os.getenv("SLEEP_API_URL", "http://localhost:8000")

class ApiClient:
    def __init__(self, base_url=API_URL):
        self.base_url = base_url.rstrip("/")

    def _request(self, method, path, **kwargs):
        try:
            response = requests.request(method, self.base_url + path, timeout=5, **kwargs)
            response.raise_for_status()
            return None if response.status_code == 204 else response.json()
        except requests.RequestException as exc:
            raise ApiConnectionError(
                "Не удалось связаться с API. Проверь, что Docker-контейнеры запущены.\n"
                f"Подробности: {exc}"
            ) from exc

    def list_records(self):
        return self._request("GET", "/sleep")

    def create_record(self, data):
        return self._request("POST", "/sleep", json=data)

    def update_record(self, record_id, data):
        return self._request("PUT", f"/sleep/{record_id}", json=data)

    def delete_record(self, record_id):
        return self._request("DELETE", f"/sleep/{record_id}")

    def stats(self):
        return self._request("GET", "/stats")
