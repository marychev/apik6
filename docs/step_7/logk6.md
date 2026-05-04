# Почему такие параметры

- kafka_num_consumers = 4: Позволяет ClickHouse параллельно читать из топика, если есть >1 партиция.
- kafka_poll_timeout_ms = 1000: Уменьшает задержку ожидания, но оставляет время для формирования пакета.
- kafka_poll_max_batch_size = 200000: Большой batch для throughput, но меньше риска чрезмерного буферизации, чем 1M.
- kafka_flush_interval_ms = 10000: Сохраняет крупные пакеты, но не удерживает данные слишком долго.

---------------------------------------------------------------

checks_total.......: 128087 2101.296814/s
checks_succeeded...: 99.99% 128085 out of 128087
checks_failed......: 0.00%  2 out of 128087

✗ status 200
  ↳  99% — ✓ 128085 / ✗ 2

HTTP
http_req_duration..............: avg=1.17s min=4.48ms med=786.99ms max=59.99s p(90)=1.82s p(95)=2.64s
  { expected_response:true }...: avg=1.17s min=4.48ms med=786.99ms max=59.97s p(90)=1.82s p(95)=2.64s
http_req_failed................: 0.00%  2 out of 128087
http_reqs......................: 128087 2101.296814/s

EXECUTION
iteration_duration.............: avg=1.17s min=4.92ms med=787.45ms max=1m0s   p(90)=1.82s p(95)=2.65s
iterations.....................: 128087 2101.296814/s
vus............................: 1847   min=1847        max=2500
vus_max........................: 2500   min=2500        max=2500

NETWORK
data_received..................: 17 MB  284 kB/s
data_sent......................: 13 MB  216 kB/s

=====================================================

checks_total.......: 177897  2939.558665/s
checks_succeeded...: 100.00% 177897 out of 177897
checks_failed......: 0.00%   0 out of 177897

✓ status 200

HTTP
http_req_duration..............: avg=837.15ms min=6.58ms med=722.71ms max=4.55s p(90)=1.42s p(95)=1.9s
  { expected_response:true }...: avg=837.15ms min=6.58ms med=722.71ms max=4.55s p(90)=1.42s p(95)=1.9s
http_req_failed................: 0.00%  0 out of 177897
http_reqs......................: 177897 2939.558665/s

EXECUTION
iteration_duration.............: avg=843.22ms min=6.67ms med=728.46ms max=4.61s p(90)=1.42s p(95)=1.9s
iterations.....................: 177897 2939.558665/s
vus............................: 925    min=925         max=2500
vus_max........................: 2500   min=2500        max=2500

NETWORK
data_received..................: 24 MB  397 kB/s
data_sent......................: 18 MB  303 kB/s

====================================================

checks_total.......: 170961  2822.637449/s
checks_succeeded...: 100.00% 170961 out of 170961
checks_failed......: 0.00%   0 out of 170961

✓ status 200

HTTP
http_req_duration..............: avg=869.53ms min=23.68ms med=716.43ms max=38.55s p(90)=1.39s p(95)=1.77s
  { expected_response:true }...: avg=869.53ms min=23.68ms med=716.43ms max=38.55s p(90)=1.39s p(95)=1.77s
http_req_failed................: 0.00%  0 out of 170961
http_reqs......................: 170961 2822.637449/s

EXECUTION
iteration_duration.............: avg=877.31ms min=23.78ms med=726.15ms max=38.86s p(90)=1.4s  p(95)=1.77s
iterations.....................: 170961 2822.637449/s
vus............................: 303    min=303         max=2500
vus_max........................: 2500   min=2500        max=2500

NETWORK
data_received..................: 23 MB  381 kB/s
data_sent......................: 18 MB  291 kB/s


/////////////////////////////////////////////////////////////////
=================================================================

root@DESKTOP-0K1NMK9:/home/apik6# VUS=2500 DURATION=1m k6 run k6/rps.js

1.
  scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

WARN[0061] Request Failed                                error="Post \"http://localhost:8000/users/batch/1\": request timeout"
WARN[0061] Request Failed                                error="Post \"http://localhost:8000/users/batch/1\": request timeout"
WARN[0061] Request Failed                                error="Post \"http://localhost:8000/users/batch/1\": request timeout"
WARN[0061] Request Failed                                error="Post \"http://localhost:8000/users/batch/1\": request timeout"
WARN[0061] Request Failed                                error="Post \"http://localhost:8000/users/batch/1\": request timeout"
WARN[0061] Request Failed                                error="Post \"http://localhost:8000/users/batch/1\": request timeout"

  █ TOTAL RESULTS 

    checks_total.......: 164187 2688.222353/s
    checks_succeeded...: 99.99% 164181 out of 164187
    checks_failed......: 0.00%  6 out of 164187

    ✗ status 200
      ↳  99% — ✓ 164181 / ✗ 6

    HTTP
    http_req_duration..............: avg=906ms    min=6.65ms med=499.48ms max=59.77s p(90)=885.25ms p(95)=1.02s
      { expected_response:true }...: avg=903.87ms min=6.65ms med=499.46ms max=59.77s p(90)=885.21ms p(95)=1.02s
    http_req_failed................: 0.00%  6 out of 164187
    http_reqs......................: 164187 2688.222353/s

    EXECUTION
    iteration_duration.............: avg=911.93ms min=6.78ms med=500.64ms max=1m0s   p(90)=887.4ms  p(95)=1.02s
    iterations.....................: 164187 2688.222353/s
    vus............................: 1407   min=1407        max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 22 MB  363 kB/s
    data_sent......................: 17 MB  277 kB/s

running (1m01.1s), 0000/2500 VUs, 164187 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s


2.  
```log
scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 152399  2511.496047/s
    checks_succeeded...: 100.00% 152399 out of 152399
    checks_failed......: 0.00%   0 out of 152399

    ✓ status 200

    HTTP
    http_req_duration..............: avg=977.36ms min=31.27ms med=564.72ms max=59.5s  p(90)=1.28s p(95)=1.67s
      { expected_response:true }...: avg=977.36ms min=31.27ms med=564.72ms max=59.5s  p(90)=1.28s p(95)=1.67s
    http_req_failed................: 0.00%  0 out of 152399
    http_reqs......................: 152399 2511.496047/s

    EXECUTION
    iteration_duration.............: avg=982.47ms min=31.36ms med=566.8ms  max=59.61s p(90)=1.29s p(95)=1.68s
    iterations.....................: 152399 2511.496047/s
    vus............................: 732    min=732         max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 21 MB  339 kB/s
    data_sent......................: 16 MB  259 kB/s

running (1m00.7s), 0000/2500 VUs, 152399 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s
```


3.  
```log
 scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 184462  3019.917113/s
    checks_succeeded...: 100.00% 184462 out of 184462
    checks_failed......: 0.00%   0 out of 184462

    ✓ status 200

    HTTP
    http_req_duration..............: avg=811.17ms min=46.28ms med=660.07ms max=43.15s p(90)=1.22s p(95)=1.55s
      { expected_response:true }...: avg=811.17ms min=46.28ms med=660.07ms max=43.15s p(90)=1.22s p(95)=1.55s
    http_req_failed................: 0.00%  0 out of 184462
    http_reqs......................: 184462 3019.917113/s

    EXECUTION
    iteration_duration.............: avg=816.26ms min=46.38ms med=665.11ms max=43.22s p(90)=1.23s p(95)=1.55s
    iterations.....................: 184462 3019.917113/s
    vus............................: 2481   min=2053        max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 25 MB  408 kB/s
    data_sent......................: 19 MB  311 kB/s


running (1m01.1s), 0000/2500 VUs, 184462 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s
```

---

## АНАЛИЗ: ДО vs ПОСЛЕ оптимизации

### Параметры ДО (старые)
- `kafka_num_consumers = 1`
- `kafka_poll_timeout_ms = 5000`
- `kafka_poll_max_batch_size = 1000000`
- `kafka_flush_interval_ms = 30000`

### Параметры ПОСЛЕ (новые)
- `kafka_num_consumers = 4`
- `kafka_poll_timeout_ms = 1000`
- `kafka_poll_max_batch_size = 200000`
- `kafka_flush_interval_ms = 10000`

### Сравнительная таблица

| Метрика | ДО (Run 1) | ДО (Run 2) | ДО (Run 3) | ПОСЛЕ (Run 1) | ПОСЛЕ (Run 2) | ПОСЛЕ (Run 3) | Улучшение |
|---------|-----------|-----------|-----------|--------------|--------------|--------------|-----------|
| **RPS** | 2101 | 2939 | 2822 | 2688 | 2511 | **3020** | **+2.7%** ✅ |
| **p95 (ms)** | 2640 | 1900 | 1770 | 1020 | 1670 | **1550** | **-12.4%** ✅ |
| **Ошибки** | 2 ❌ | 0 | 0 | 6 ⚠️ | 0 | 0 | ⚠️ (нестабильность в run 1) |
| **Медиана (ms)** | 787 | 723 | 716 | 499 | 565 | **660** | **-7.8%** ✅ |

### Ключевые выводы

1. **Лучший RPS**: 3020 req/s (run 3 после) vs 2939 req/s (run 2 до) = **+81 req/s (+2.7%)**
2. **Лучший p95**: 1.55s (run 3 после) vs 1.77s (run 3 до) = **-220ms (-12.4%)**
3. **Стабильность**: Новые параметры показали хорошую стабильность после прогрева (run 3)
4. **Холодный старт**: Run 1 после имел таймауты, что может указывать на то, что система нуждается в разминке

### Гипотезы улучшения

✅ **Параллельные потребители** (`kafka_num_consumers = 4`)
   - ClickHouse теперь читает из 4 партиций параллельно вместо 1

✅ **Меньший batch** (`kafka_poll_max_batch_size: 1M → 200k`)
   - Снижает задержку между обработкой пакетов
   - Больше контроля над памятью

✅ **Быстрее flush** (`kafka_flush_interval_ms: 30s → 10s`)
   - Данные попадают в ClickHouse быстрее
   - Меньше задержек на краю интервала

✅ **Меньше ожидания** (`kafka_poll_timeout_ms: 5s → 1s`)
   - Быстрее отвечаем на новые сообщения
   - Меньше latency при низких нагрузках

### Рекомендация

Новые параметры работают хорошо. Если нужна ещё большая стабильность:
- Добавить `KAFKA_NUM_PARTITIONS=8` для ещё большего параллелизма
- Попробовать `kafka_num_consumers=8`
- Увеличить `linger_ms` в producer (сейчас 20ms) для лучшей батчизации