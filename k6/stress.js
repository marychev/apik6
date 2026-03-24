import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Counter } from "k6/metrics";
import { USER_BATCH_URL } from "./config.js";

// Кастомные метрики
const batchDuration = new Trend("batch_duration", true);
const totalSent = new Counter("total_sent");
const totalSaved = new Counter("total_saved");
const lostMessages = new Counter("lost_messages");

export const options = {
  scenarios: {
    // Стресс-тест: много одновременных запросов на batch/1000
    stress: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "10s", target: 5 },    // 5 VU × batch/1000 = 5000 users/итерацию
        { duration: "20s", target: 10 },   // 10 VU одновременно
        { duration: "20s", target: 20 },   // 20 VU — тяжёлая нагрузка
        { duration: "10s", target: 1 },    // остывание
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<15000"],
    http_req_failed: ["rate<0.2"],
  },
};

export default function () {
  const start = Date.now();

  // Каждый VU создаёт 1000 пользователей за один запрос
  const res = http.post(USER_BATCH_URL);

  const duration = Date.now() - start;
  batchDuration.add(duration);

  check(res, {
    "status is 200": (r) => r.status === 200,
  });

  if (res.status === 200) {
    const body = res.json();
    totalSent.add(body.sent);
    totalSaved.add(body.saved_to_clickhouse);

    // Потерянные сообщения
    const lost = body.sent - body.saved_to_clickhouse;
    if (lost > 0) {
      lostMessages.add(lost);
    }
  }

}
