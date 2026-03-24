import http from "k6/http";
import { check } from "k6";
import { Counter } from "k6/metrics";
import { USER_BATCH_URL } from "./config.js";

const totalSent = new Counter("total_sent");
const totalSaved = new Counter("total_saved");
const lostMessages = new Counter("lost_messages");

export const options = {
  scenarios: {
    // Спайк: резкий всплеск — что будет если 50 VU одновременно запросят batch/1
    spike: {
      executor: "shared-iterations",
      vus: 50,
      iterations: 50,
      maxDuration: "2m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.3"],
  },
};

export default function () {
  const res = http.post(USER_BATCH_URL);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "all saved": (r) =>
      r.status === 200 && r.json("sent") === r.json("saved_to_clickhouse"),
  });

  if (res.status === 200) {
    const body = res.json();
    totalSent.add(body.sent);
    totalSaved.add(body.saved_to_clickhouse);

    const lost = body.sent - body.saved_to_clickhouse;
    if (lost > 0) {
      lostMessages.add(lost);
    }
  }
}
