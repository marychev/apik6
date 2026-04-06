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
    ✗ 'p(95)<300' p(95)=469.52ms
    ✓ 'p(99)<800' p(99)=777.41ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 33584   530.103031/s
    checks_succeeded...: 100.00% 33584 out of 33584
    checks_failed......: 0.00%   0 out of 33584

    ✓ status is 200

    HTTP
    http_req_duration..............: avg=188.19ms min=15.92ms med=151.17ms max=2.35s    p(90)=343.49ms p(95)=469.52ms
      { expected_response:true }...: avg=188.19ms min=15.92ms med=151.17ms max=2.35s    p(90)=343.49ms p(95)=469.52ms
    http_req_failed................: 0.00%  0 out of 33584
    http_reqs......................: 33584  530.103031/s

    EXECUTION
    iteration_duration.............: avg=178.73ms min=16.13ms med=151.09ms max=956.08ms p(90)=339.14ms p(95)=458.73ms
    iterations.....................: 33584  530.103031/s
    vus............................: 100    min=100        max=100
    vus_max........................: 100    min=100        max=100

    NETWORK
    data_received..................: 4.5 MB 72 kB/s
    data_sent......................: 3.5 MB 55 kB/s



                                                                                                                                                                                                                                       
running (1m03.4s), 000/100 VUs, 33584 complete and 0 interrupted iterations                                                                                                                                                            
default ✓ [======================================] 100 VUs  1m0s                                                                                                                                                                       
ERRO[0060] thresholds on metrics 'http_req_duration{expected_response:true}' have been crossed