import clickhouse_connect
from clickhouse_connect.driver import Client

from config import CLICKHOUSE_HOST

_client: Client | None = None


def get_clickhouse_client() -> Client:
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(host=CLICKHOUSE_HOST)
    return _client
