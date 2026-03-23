import { createUser, resetUsers } from "./config.js";
import { check, sleep } from "k6";

export function setup() {
  resetUsers();
}
import { Trend, Counter } from "k6/metrics";

const latencyTrend = new Trend("post_user_duration");
const totalCreated = new Counter("total_users_created");

export const options = {
  stages: [
    { duration: "30s", target: 50 },
    { duration: "5m", target: 50 },
    { duration: "10s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const res = createUser();

  check(res, {
    "status is 201": (r) => r.status === 201,
  });

  if (res.status === 201) {
    latencyTrend.add(res.timings.duration);
    totalCreated.add(1);
  }

  sleep(0.1);
}
