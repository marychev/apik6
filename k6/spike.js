import { createUser, resetUsers } from "./config.js";
import { check, sleep } from "k6";

export function setup() {
  resetUsers();
}

export const options = {
  stages: [
    { duration: "10s", target: 10 },
    { duration: "5s", target: 500 },
    { duration: "30s", target: 500 },
    { duration: "5s", target: 10 },
    { duration: "10s", target: 10 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"],
    http_req_failed: ["rate<0.05"],
  },
};

export default function () {
  const res = createUser();

  check(res, {
    "status is 201": (r) => r.status === 201,
  });

  sleep(0.1);
}
