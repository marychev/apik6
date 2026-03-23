import { createUser, resetUsers } from "./config.js";
import { check } from "k6";

export function setup() {
  resetUsers();
}

export const options = {
  scenarios: {
    breakpoint: {
      executor: "ramping-arrival-rate",
      startRate: 10,
      timeUnit: "1s",
      preAllocatedVUs: 100,
      maxVUs: 2000,
      stages: [
        { duration: "30s", target: 100 },
        { duration: "30s", target: 300 },
        { duration: "30s", target: 500 },
        { duration: "30s", target: 800 },
        { duration: "30s", target: 1000 },
      ],
    },
  },
  thresholds: {
    http_req_duration: [{ threshold: "p(95)<2000", abortOnFail: true }],
    http_req_failed: [{ threshold: "rate<0.10", abortOnFail: true }],
  },
};

export default function () {
  const res = createUser();

  check(res, {
    "status is 201": (r) => r.status === 201,
    "response time < 2s": (r) => r.timings.duration < 2000,
  });
}
