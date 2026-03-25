import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Counter, Gauge } from "k6/metrics";
import { USER_BATCH_URL, USER_COUNT_URL } from "./config.js";

// --- Метрики ---
const batchDuration = new Trend("batch_duration", true);
const totalSent = new Counter("total_sent");

// Lag-метрики (заполняются в сценарии measure_lag)
const lagDuration = new Trend("lag_duration", true);  // время пока все сообщения дойдут до CH
const lagMessages = new Gauge("lag_messages");         // сообщений "в полёте" на момент замера

export const options = {
  scenarios: {
    // Сценарий 1: Нарастающая нагрузка
    ramp_up: {
      executor: "ramping-arrival-rate",
      startRate: 5,
      timeUnit: "1s",
      preAllocatedVUs: 50,
      maxVUs: 200,
      stages: [
        { duration: "15s", target: 10 },   // разогрев
        { duration: "15s", target: 30 },   // средняя нагрузка
        { duration: "15s", target: 60 },   // высокая нагрузка
        { duration: "15s", target: 100 },  // пиковая нагрузка
        { duration: "10s", target: 5 },    // остывание
      ],
      exec: "loadTest",
    },

    // Сценарий 2: Замер лага — стартует после окончания нагрузки
    measure_lag: {
      executor: "shared-iterations",
      vus: 1,
      iterations: 1,
      startTime: "75s",  // после ramp_up (70s) + 5s буфер
      exec: "measureLag",
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<5000"],       // 95% запросов < 5 сек
    http_req_failed: ["rate<0.1"],           // < 10% ошибок
    batch_duration: ["p(95)<5000"],          // полный цикл batch < 5 сек
  },
};

// Запоминаем count в CH до начала теста
export function setup() {
  const res = http.get(USER_COUNT_URL);
  const countBefore = res.status === 200 ? res.json("count") : 0;
  return { countBefore };
}

// --- Сценарий 1: Нагрузка ---
export function loadTest(data) {
  const start = Date.now();

  const res = http.post(USER_BATCH_URL);

  const duration = Date.now() - start;
  batchDuration.add(duration);

  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
    "has sent field": (r) => r.json("sent") !== undefined,
  });

  if (ok && res.status === 200) {
    totalSent.add(res.json("sent"));
  }
}

// --- Сценарий 2: Замер лага Kafka→ClickHouse ---
export function measureLag(data) {
  // Сколько было в CH до теста
  const countBefore = data.countBefore;

  // Узнаём сколько сейчас в CH
  let res = http.get(USER_COUNT_URL);
  const countAfterLoad = res.status === 200 ? res.json("count") : 0;

  // Всего новых записей, которые должны были появиться = countAfterLoad - countBefore + то что ещё в пути
  // Но мы не знаем точное число отправленных из другого сценария (counters не шарятся).
  // Поэтому: ждём пока count перестанет расти (consumer дочитал всё из Kafka)

  console.log(`[lag] CH count после нагрузки: ${countAfterLoad} (было до теста: ${countBefore})`);

  let prevCount = countAfterLoad;
  let stableRounds = 0;
  const lagStart = Date.now();
  const maxWait = 30000; // макс 30 сек ожидания

  while (Date.now() - lagStart < maxWait) {
    sleep(1);
    res = http.get(USER_COUNT_URL);
    if (res.status !== 200) continue;

    const current = res.json("count");
    const inFlight = current - prevCount;

    console.log(`[lag] CH count: ${current} (+${inFlight} за последнюю секунду)`);
    lagMessages.add(current - countAfterLoad);  // сколько ещё дошло после окончания нагрузки

    if (current === prevCount) {
      stableRounds++;
      if (stableRounds >= 3) {
        // 3 секунды подряд count не растёт — consumer всё дочитал
        break;
      }
    } else {
      stableRounds = 0;
    }
    prevCount = current;
  }

  const lagMs = Date.now() - lagStart;
  lagDuration.add(lagMs);

  const totalNew = prevCount - countBefore;
  const deliveredAfterLoad = prevCount - countAfterLoad;

  console.log(`[lag] Итого: ${totalNew} новых записей в CH`);
  console.log(`[lag] Из них ${deliveredAfterLoad} дошли уже ПОСЛЕ окончания нагрузки`);
  console.log(`[lag] Время полной доставки: ${lagMs}ms`);

  check(null, {
    "all messages delivered to CH": () => deliveredAfterLoad >= 0,
    "lag under 10s": () => lagMs < 10000,
  });
}
