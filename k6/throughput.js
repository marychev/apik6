import { createUser, resetUsers } from "./config.js";
import { check } from "k6";

export function setup() {
  resetUsers();
}

export const options = {
  scenarios: {
    low: {
      executor: "constant-arrival-rate",
      rate: 50,
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 50,
      maxVUs: 100,
      startTime: "0s",
    },
    medium: {
      executor: "constant-arrival-rate",
      rate: 100,
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 100,
      maxVUs: 200,
      startTime: "30s",
    },
    high: {
      executor: "constant-arrival-rate",
      rate: 200,
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 200,
      maxVUs: 400,
      startTime: "60s",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const res = createUser();

  check(res, {
    "status is 201": (r) => r.status === 201,
    "has user id": (r) => JSON.parse(r.body).id !== undefined,
  });
}
