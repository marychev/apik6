import { check } from "k6";
import { Counter } from "k6/metrics";
import http from "k6/http";
import { createUser, resetUsers, BASE_URL } from "./config.js";

export function setup() {
  resetUsers();
}

const successCount = new Counter("successful_creates");
const failCount = new Counter("failed_creates");

export const options = {
  scenarios: {
    integrity: {
      executor: "shared-iterations",
      vus: 10,
      iterations: 1000,
      maxDuration: "60s",
    },
  },
  thresholds: {
    "failed_creates": ["count<1"],
  },
};

export default function () {
  const res = createUser();

  const ok = check(res, {
    "status is 201": (r) => r.status === 201,
    "body has id": (r) => {
      try {
        return JSON.parse(r.body).id !== undefined;
      } catch {
        return false;
      }
    },
  });

  if (ok) {
    successCount.add(1);
  } else {
    failCount.add(1);
  }
}

export function handleSummary(data) {
  // Проверяем количество записей на сервере
  const res = http.get(`${BASE_URL}/users/count`);
  let serverCount = "N/A";
  try {
    serverCount = JSON.parse(res.body).count;
  } catch {}

  const sent = data.metrics.successful_creates
    ? data.metrics.successful_creates.values.count
    : 0;
  const failed = data.metrics.failed_creates
    ? data.metrics.failed_creates.values.count
    : 0;

  const summary = {
    "=== DATA INTEGRITY REPORT ===": "",
    "Sent (success)": sent,
    "Sent (failed)": failed,
    "Server count": serverCount,
    "Data loss": sent - (typeof serverCount === "number" ? serverCount : 0),
  };

  console.log("\n" + JSON.stringify(summary, null, 2));

  return {};
}
