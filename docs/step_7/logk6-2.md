# Apply
KAFKA_ENGINE_NUM_CONSUMERS = 4
linger_ms=100,  # 20 → 100 (больше время для батчинга)
max_batch_size=131072,  # 64KB → 128KB
compression_type="lz4",
acks=1,
idempotent=False

----------------------------------------------

1.  VUS=2500 DURATION=1m k6 run k6/rps.js
```log
 scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 160156  2562.453017/s
    checks_succeeded...: 100.00% 160156 out of 160156
    checks_failed......: 0.00%   0 out of 160156

    ✓ status 200

    HTTP
    http_req_duration..............: avg=960.19ms min=87.67ms med=772.88ms max=57.06s p(90)=1.46s p(95)=1.77s
      { expected_response:true }...: avg=960.19ms min=87.67ms med=772.88ms max=57.06s p(90)=1.46s p(95)=1.77s
    http_req_failed................: 0.00%  0 out of 160156
    http_reqs......................: 160156 2562.453017/s

    EXECUTION
    iteration_duration.............: avg=938.58ms min=87.75ms med=772.03ms max=55.44s p(90)=1.42s p(95)=1.65s
    iterations.....................: 160156 2562.453017/s
    vus............................: 1830   min=1830        max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 22 MB  346 kB/s
    data_sent......................: 17 MB  264 kB/s

running (1m02.5s), 0000/2500 VUs, 160156 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s
```


2.
```log
scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 133354  2138.593601/s
    checks_succeeded...: 100.00% 133354 out of 133354
    checks_failed......: 0.00%   0 out of 133354

    ✓ status 200

    HTTP
    http_req_duration..............: avg=1.14s min=65.9ms  med=881.35ms max=52.49s p(90)=2.04s p(95)=2.47s
      { expected_response:true }...: avg=1.14s min=65.9ms  med=881.35ms max=52.49s p(90)=2.04s p(95)=2.47s
    http_req_failed................: 0.00%  0 out of 133354
    http_reqs......................: 133354 2138.593601/s

    EXECUTION
    iteration_duration.............: avg=1.12s min=66.39ms med=877.65ms max=50.7s  p(90)=1.94s p(95)=2.38s
    iterations.....................: 133354 2138.593601/s
    vus............................: 172    min=172         max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 18 MB  289 kB/s
    data_sent......................: 14 MB  220 kB/s

running (1m02.4s), 0000/2500 VUs, 133354 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s
```


3.
```log
scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 122994  1957.51499/s
    checks_succeeded...: 100.00% 122994 out of 122994
    checks_failed......: 0.00%   0 out of 122994

    ✓ status 200

    HTTP
    http_req_duration..............: avg=1.23s min=35.84ms med=576.89ms max=1m0s p(90)=1.35s p(95)=1.86s
      { expected_response:true }...: avg=1.23s min=35.84ms med=576.89ms max=1m0s p(90)=1.35s p(95)=1.86s
    http_req_failed................: 0.00%  0 out of 122994
    http_reqs......................: 122994 1957.51499/s

    EXECUTION
    iteration_duration.............: avg=1.21s min=36.03ms med=569.57ms max=1m0s p(90)=1.35s p(95)=1.81s
    iterations.....................: 122994 1957.51499/s
    vus............................: 395    min=0           max=2500
    vus_max........................: 2500   min=1034        max=2500

    NETWORK
    data_received..................: 17 MB  264 kB/s
    data_sent......................: 13 MB  202 kB/s


running (1m02.8s), 0000/2500 VUs, 122994 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s
```
=========================================

# Apply == UVICORN_WORKERS:-4

1.
```log
scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 180220  2913.871586/s
    checks_succeeded...: 100.00% 180220 out of 180220
    checks_failed......: 0.00%   0 out of 180220

    ✓ status 200

    HTTP
    http_req_duration..............: avg=833.56ms min=14.72ms med=424.14ms max=1m0s   p(90)=925.11ms p(95)=1.2s 
      { expected_response:true }...: avg=833.56ms min=14.72ms med=424.14ms max=1m0s   p(90)=925.11ms p(95)=1.2s 
    http_req_failed................: 0.00%  0 out of 180220
    http_reqs......................: 180220 2913.871586/s

    EXECUTION
    iteration_duration.............: avg=826.48ms min=14.79ms med=424.84ms max=59.88s p(90)=903.35ms p(95)=1.11s
    iterations.....................: 180220 2913.871586/s
    vus............................: 2500   min=0           max=2500
    vus_max........................: 2500   min=2096        max=2500

    NETWORK
    data_received..................: 24 MB  393 kB/s
    data_sent......................: 19 MB  300 kB/s

running (1m01.8s), 0000/2500 VUs, 180220 complete and 0 interrupted iterations
```


2. 
```log
 scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 182736  2926.085818/s
    checks_succeeded...: 100.00% 182736 out of 182736
    checks_failed......: 0.00%   0 out of 182736

    ✓ status 200

    HTTP
    http_req_duration..............: avg=842.16ms min=91.27ms med=765.63ms max=7.89s p(90)=1.35s p(95)=1.61s
      { expected_response:true }...: avg=842.16ms min=91.27ms med=765.63ms max=7.89s p(90)=1.35s p(95)=1.61s
    http_req_failed................: 0.00%  0 out of 182736
    http_reqs......................: 182736 2926.085818/s

    EXECUTION
    iteration_duration.............: avg=820.93ms min=91.34ms med=764.72ms max=8.4s  p(90)=1.27s p(95)=1.45s
    iterations.....................: 182736 2926.085818/s
    vus............................: 2500   min=2500        max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 25 MB  395 kB/s
    data_sent......................: 19 MB  301 kB/s

running (1m02.5s), 0000/2500 VUs, 182736 complete and 0 interrupted iterations
```

3.  
```log
scenarios: (100.00%) 1 scenario, 2500 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 2500 looping VUs for 1m0s (gracefulStop: 30s)

  █ TOTAL RESULTS 

    checks_total.......: 183553  2940.285542/s
    checks_succeeded...: 100.00% 183553 out of 183553
    checks_failed......: 0.00%   0 out of 183553

    ✓ status 200

    HTTP
    http_req_duration..............: avg=833.95ms min=42.9ms  med=623.07ms max=1m1s   p(90)=1.07s p(95)=1.29s
      { expected_response:true }...: avg=833.95ms min=42.9ms  med=623.07ms max=1m1s   p(90)=1.07s p(95)=1.29s
    http_req_failed................: 0.00%  0 out of 183553
    http_reqs......................: 183553 2940.285542/s

    EXECUTION
    iteration_duration.............: avg=814.22ms min=45.24ms med=626.39ms max=59.58s p(90)=1.04s p(95)=1.21s
    iterations.....................: 183553 2940.285542/s
    vus............................: 1156   min=1156        max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 25 MB  397 kB/s
    data_sent......................: 19 MB  303 kB/s

running (1m02.4s), 0000/2500 VUs, 183553 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s
```

================================================

# Apply == KAFKA_ENGINE_NUM_CONSUMERS = 8

1. 
```log
TOTAL RESULTS 

    checks_total.......: 181510 2892.60454/s
    checks_succeeded...: 99.99% 181503 out of 181510
    checks_failed......: 0.00%  7 out of 181510

    ✗ status 200
      ↳  99% — ✓ 181503 / ✗ 7

    HTTP
    http_req_duration..............: avg=847.71ms min=9.1ms  med=472.44ms max=1m1s p(90)=915.91ms p(95)=1.28s
      { expected_response:true }...: avg=845.36ms min=9.1ms  med=472.44ms max=1m1s p(90)=915.8ms  p(95)=1.28s
    http_req_failed................: 0.00%  7 out of 181510
    http_reqs......................: 181510 2892.60454/s

    EXECUTION
    iteration_duration.............: avg=824.31ms min=9.24ms med=471.32ms max=1m0s p(90)=876.27ms p(95)=1.12s
    iterations.....................: 181510 2892.60454/s
    vus............................: 599    min=599         max=2500
    vus_max........................: 2500   min=2500        max=2500

    NETWORK
    data_received..................: 25 MB  391 kB/s
    data_sent......................: 19 MB  298 kB/s

running (1m02.7s), 0000/2500 VUs, 181510 complete and 0 interrupted iterations
```

3.
```
TOTAL RESULTS 

    checks_total.......: 194263 3148.065159/s
    checks_succeeded...: 99.75% 193786 out of 194263
    checks_failed......: 0.24%  477 out of 194263

    ✗ status 200
      ↳  99% — ✓ 193786 / ✗ 477

    HTTP
    http_req_duration..............: avg=781.29ms min=23.71ms med=414.51ms max=1m0s p(90)=744.12ms p(95)=843.71ms
      { expected_response:true }...: avg=633.87ms min=23.71ms med=413.97ms max=1m0s p(90)=740.35ms p(95)=836.37ms
    http_req_failed................: 0.24%  477 out of 194263
    http_reqs......................: 194263 3148.065159/s

    EXECUTION
    iteration_duration.............: avg=772.61ms min=23.8ms  med=414.17ms max=1m0s p(90)=734.61ms p(95)=824.26ms
    iterations.....................: 194263 3148.065159/s
    vus............................: 474    min=474           max=2500
    vus_max........................: 2500   min=2500          max=2500

    NETWORK
    data_received..................: 26 MB  424 kB/s
    data_sent......................: 20 MB  324 kB/s

running (1m01.7s), 0000/2500 VUs, 194263 complete and 0 interrupted iterations
default ✓ [======================================] 2500 VUs  1m0s
```




ERRORS

api-1         | ValueError: acks=0 not supported if enable_idempotence=True