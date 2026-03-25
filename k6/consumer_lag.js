import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Counter, Gauge } from "k6/metrics";
import { BASE_URL, USER_COUNT_URL } from "./config.js";

const BATCH_URL = `${BASE_URL}/users/batch/1000`;

// --- Метрики ---
const batchDuration = new Trend("batch_duration", true);
const totalSent = new Counter("total_sent");

// Lag-метрики
const lagDuration = new Trend("lag_duration", true);  // время полной доставки после нагрузки
const lagMessages = new Gauge("lag_messages");         // сообщений дошло после окончания нагрузки

export const options = {
  scenarios: {
    // Фаза 1: Нагрузка на consumer — batch/1000 × ramping VUs
    // Цель: ~10,000 сообщений
    load: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "10s", target: 3 },    // разогрев
        { duration: "15s", target: 5 },    // основная нагрузка
        { duration: "15s", target: 10 },   // пиковая нагрузка
        { duration: "10s", target: 1 },    // остывание
      ],
      exec: "loadTest",
    },

    // Фаза 2: Замер лага — стартует после нагрузки
    measure_lag: {
      executor: "shared-iterations",
      vus: 1,
      iterations: 1,
      startTime: "55s",  // после load (50s) + 5s буфер
      maxDuration: "2m",
      exec: "measureLag",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.2"],
  },
};

export function setup() {
  const res = http.get(USER_COUNT_URL);
  const countBefore = res.status === 200 ? res.json("count") : 0;
  console.log(`[setup] CH count до теста: ${countBefore}`);
  return { countBefore };
}

// --- Фаза 1: Нагрузка batch/1000 ---
export function loadTest(data) {
  const start = Date.now();

  const res = http.post(BATCH_URL);

  const duration = Date.now() - start;
  batchDuration.add(duration);

  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
  });

  if (ok && res.status === 200) {
    totalSent.add(res.json("sent"));
  }
}

// --- Фаза 2: Замер лага Kafka→ClickHouse ---
export function measureLag(data) {
  const countBefore = data.countBefore;

  let res = http.get(USER_COUNT_URL);
  const countAfterLoad = res.status === 200 ? res.json("count") : 0;
  const alreadyDelivered = countAfterLoad - countBefore;

  console.log(`[lag] CH count после нагрузки: ${countAfterLoad} (было: ${countBefore}, уже доставлено: ${alreadyDelivered})`);

  let prevCount = countAfterLoad;
  let stableRounds = 0;
  const lagStart = Date.now();
  const maxWait = 60000; // макс 60 сек ожидания

  while (Date.now() - lagStart < maxWait) {
    sleep(1);
    res = http.get(USER_COUNT_URL);
    if (res.status !== 200) continue;

    const current = res.json("count");
    const delta = current - prevCount;

    console.log(`[lag] CH count: ${current} (+${delta} за секунду, всего доставлено: ${current - countBefore})`);
    lagMessages.add(current - countAfterLoad);

    if (current === prevCount) {
      stableRounds++;
      if (stableRounds >= 3) {
        break;
      }
    } else {
      stableRounds = 0;
    }
    prevCount = current;
  }

  const lagMs = Date.now() - lagStart;
  lagDuration.add(lagMs);

  const totalDelivered = prevCount - countBefore;
  const deliveredAfterLoad = prevCount - countAfterLoad;

  console.log(`[lag] ─────────────────────────────────`);
  console.log(`[lag] Всего доставлено в CH: ${totalDelivered}`);
  console.log(`[lag] Из них после окончания нагрузки: ${deliveredAfterLoad}`);
  console.log(`[lag] Время дочитки consumer: ${lagMs}ms`);

  check(null, {
    "consumer delivered all": () => stableRounds >= 3,
    "lag under 30s": () => lagMs < 30000,
  });
}
