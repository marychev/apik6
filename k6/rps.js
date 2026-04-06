import http from "k6/http";
import { check } from "k6";
import { USER_BATCH_URL } from "./config.js";

// Чистый замер RPS: 100 VU, 1 минута, без thresholds
// Запуск: k6 run k6/rps.js
export const options = {
  vus: 100,
  duration: "1m",
};

export default function () {
  const res = http.post(USER_BATCH_URL);
  check(res, { "status 200": (r) => r.status === 200 });
}
