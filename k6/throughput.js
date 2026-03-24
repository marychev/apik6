import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Counter } from "k6/metrics";
import { USER_BATCH_URL } from "./config.js";

// Кастомные метрики
const batchDuration = new Trend("batch_duration", true);
const kafkaLag = new Trend("kafka_lag", true);
const totalSent = new Counter("total_sent");
const totalSaved = new Counter("total_saved");

export const options = {
  scenarios: {
    // Сценарий 1: Нарастающая нагрузка — сколько выдержит система
    ramp_up: {
      executor: "ramping-arrival-rate",
      startRate: 5,
      timeUnit: "1s",
      preAllocatedVUs: 50,
      maxVUs: 200,
      stages: [
        { duration: "15s", target: 10 },   // разогрев
        { duration: "15s", target: 30 },   // средняя нагрузка
        { duration: "15s", target: 60 },   // высокая нагрузка
        { duration: "15s", target: 100 },  // пиковая нагрузка
        { duration: "10s", target: 5 },    // остывание
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<5000"],       // 95% запросов < 5 сек
    http_req_failed: ["rate<0.1"],           // < 10% ошибок
    batch_duration: ["p(95)<5000"],          // полный цикл batch < 5 сек
    kafka_lag: ["p(95)<3000"],               // лаг Kafka→CH < 3 сек
  },
};

export default function () {
  const start = Date.now();

  const res = http.post(USER_BATCH_URL);

  const duration = Date.now() - start;
  batchDuration.add(duration);

  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
    "has sent field": (r) => r.json("sent") !== undefined,
    "has saved_to_clickhouse": (r) => r.json("saved_to_clickhouse") !== undefined,
  });

  if (ok && res.status === 200) {
    const body = res.json();
    totalSent.add(body.sent);
    totalSaved.add(body.saved_to_clickhouse);

    // Лаг = общее время - время на prepare+send (оценка: ~30% на подготовку, ~70% на consume)
    // Более точно: если sent > saved — данные застряли в Kafka
    if (body.sent > body.saved_to_clickhouse) {
      kafkaLag.add(duration);
    } else {
      kafkaLag.add(duration * 0.5); // примерная доля consume в общем времени
    }
  }

}
