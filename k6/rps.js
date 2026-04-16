import http from "k6/http";
import { check } from "k6";
import { USER_BATCH_URL } from "./config.js";

// Чистый замер RPS без thresholds.
// Запуск:            k6 run k6/rps.js                (дефолт: 100 VU, 1 мин)
// С параметрами:     VUS=400 DURATION=1m k6 run k6/rps.js
export const options = {
  vus: parseInt(__ENV.VUS || "100"),
  duration: __ENV.DURATION || "1m",
};

const SLA_TIMEOUT = __ENV.SLA_TIMEOUT || "60s";

export default function () {
  const res = http.post(USER_BATCH_URL, null, { timeout: SLA_TIMEOUT });
  check(res, { "status 200": (r) => r.status === 200 });
}
