import clickhouse_connect

from config import CLICKHOUSE_HOST

_client = None


def get_clickhouse_client():
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(host=CLICKHOUSE_HOST)
    return _client
