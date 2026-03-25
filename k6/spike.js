import http from "k6/http";
import { check } from "k6";
import { Counter } from "k6/metrics";
import { USER_BATCH_URL } from "./config.js";

const totalSent = new Counter("total_sent");

export const options = {
  scenarios: {
    // Спайк: резкий всплеск — 200 VU одновременно
    spike: {
      executor: "shared-iterations",
      vus: 200,
      iterations: 200,
      maxDuration: "2m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.1"],
  },
};

export default function () {
  const res = http.post(USER_BATCH_URL);

  check(res, {
    "status is 200": (r) => r.status === 200,
  });

  if (res.status === 200) {
    totalSent.add(res.json("sent"));
  }
}
