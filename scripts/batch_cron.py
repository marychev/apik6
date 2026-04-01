"""
Периодическая отправка POST /users/batch/{n}.
Запускается из консоли, работает пока не нажмёшь Ctrl+C.

Примеры:
    python scripts/batch_cron.py
    python scripts/batch_cron.py --batch-size 1000000 --interval 20
    python scripts/batch_cron.py -n 50 -i 3 --url http://localhost:8000
"""

import argparse
import json
import os
import time
import urllib.request
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


def log(msg, log_file=None):
    print(msg)
    if log_file:
        log_file.write(msg + "\n")
        log_file.flush()


def main():
    parser = argparse.ArgumentParser(description="Периодический POST /users/batch/{n}")
    parser.add_argument("-n", "--batch-size", type=int, default=1, help="Кол-во пользователей в батче (default: 1)")
    parser.add_argument("-i", "--interval", type=int, default=10, help="Интервал между запросами в секундах (default: 10)")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base URL API (default: http://localhost:8000)")
    args = parser.parse_args()

    os.makedirs(LOGS_DIR, exist_ok=True)
    log_filename = datetime.now().strftime("batch_cron_%Y%m%d_%H%M%S.log")
    log_path = os.path.join(LOGS_DIR, log_filename)
    log_file = open(log_path, "w")

    endpoint = f"{args.url}/users/batch/{args.batch_size}"

    log(f"[batch_cron] POST {endpoint} каждые {args.interval}с", log_file)
    log(f"[batch_cron] Лог: {log_path}", log_file)
    log(f"[batch_cron] Ctrl+C для остановки\n", log_file)

    total_sent = 0
    total_requests = 0

    try:
        while True:
            start = time.time()
            try:
                req = urllib.request.Request(endpoint, method="POST")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    status = resp.status
                    body = json.loads(resp.read())
                    sent = body.get("sent", 0)
                    total_sent += sent
                    total_requests += 1
            except Exception as e:
                status = "ERR"
                sent = 0
                total_requests += 1
                body = str(e)

            duration_ms = int((time.time() - start) * 1000)
            ts = datetime.now().strftime("%H:%M:%S")

            if status == 200:
                log(f"[{ts}] POST batch/{args.batch_size} → {status} | sent: {sent} | {duration_ms}ms | total: {total_sent}", log_file)
            else:
                log(f"[{ts}] POST batch/{args.batch_size} → {status} | {body} | {duration_ms}ms", log_file)

            time.sleep(args.interval)

    except KeyboardInterrupt:
        log(f"\n[batch_cron] Остановлен. Запросов: {total_requests}, отправлено: {total_sent}", log_file)
    finally:
        log_file.close()


if __name__ == "__main__":
    main()
