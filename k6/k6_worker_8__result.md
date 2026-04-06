 k6 run --vus 100 --duration 1m k6/k6.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: k6/k6.js
        output: -

     scenarios: (100.00%) 1 scenario, 100 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 100 looping VUs for 1m0s (gracefulStop: 30s)



  █ THRESHOLDS

    http_req_duration{expected_response:true}
    ✗ 'p(95)<300' p(95)=312.99ms
    ✓ 'p(99)<800' p(99)=484.75ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 40245   652.539864/s
    checks_succeeded...: 100.00% 40245 out of 40245
    checks_failed......: 0.00%   0 out of 40245

    ✓ status is 200

    HTTP
    http_req_duration..............: avg=152.91ms min=16.49ms med=128.61ms max=1.82s p(90)=257.13ms p(95)=312.99ms
      { expected_response:true }...: avg=152.91ms min=16.49ms med=128.61ms max=1.82s p(90)=257.13ms p(95)=312.99ms
    http_req_failed................: 0.00%  0 out of 40245
    http_reqs......................: 40245  652.539864/s

    EXECUTION
    iteration_duration.............: avg=149.13ms min=16.63ms med=128.59ms max=1.01s p(90)=254.99ms p(95)=309.11ms
    iterations.....................: 40245  652.539864/s
    vus............................: 100    min=100        max=100
    vus_max........................: 100    min=100        max=100

    NETWORK
    data_received..................: 5.4 MB 88 kB/s
    data_sent......................: 4.1 MB 67 kB/s



                                                                                                                                                                                                                                       
running (1m01.7s), 000/100 VUs, 40245 complete and 0 interrupted iterations                                                                                                                                                            
default ✓ [======================================] 100 VUs  1m0s                                                                                                                                                                       
ERRO[0060] thresholds on metrics 'http_req_duration{expected_response:true}' have been crossed