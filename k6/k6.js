import http from "k6/http";
import { check } from "k6";
import { USER_BATCH_URL } from "./config.js";

const DURATION = __ENV.DURATION || "1m";

export const options = {
  vus: 1,
  duration: DURATION,
  thresholds: {
    "http_req_duration{expected_response:true}": ["p(95)<300", "p(99)<800"],
    "http_req_failed": ["rate<0.05"],
  },
};

export default function () {
  const res = http.post(USER_BATCH_URL);
  check(res, { "status is 200": (r) => r.status === 200 });
}
