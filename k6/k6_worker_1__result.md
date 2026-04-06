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
    ✗ 'p(95)<300' p(95)=337.4ms
    ✓ 'p(99)<800' p(99)=441.59ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 30833   488.983117/s
    checks_succeeded...: 100.00% 30833 out of 30833
    checks_failed......: 0.00%   0 out of 30833

    ✓ status is 200

    HTTP
    http_req_duration..............: avg=204.11ms min=72.36ms med=175.9ms  max=1.86s    p(90)=289.33ms p(95)=337.4ms
      { expected_response:true }...: avg=204.11ms min=72.36ms med=175.9ms  max=1.86s    p(90)=289.33ms p(95)=337.4ms
    http_req_failed................: 0.00%  0 out of 30833
    http_reqs......................: 30833  488.983117/s

    EXECUTION
    iteration_duration.............: avg=194.74ms min=72.46ms med=175.94ms max=587.57ms p(90)=285.73ms p(95)=330.23ms
    iterations.....................: 30833  488.983117/s
    vus............................: 100    min=100        max=100
    vus_max........................: 100    min=100        max=100

    NETWORK
    data_received..................: 4.2 MB 66 kB/s
    data_sent......................: 3.2 MB 50 kB/s



                                                                                                                                                                                                                                           
running (1m03.1s), 000/100 VUs, 30833 complete and 0 interrupted iterations                                                                                                                                                                
default ✓ [======================================] 100 VUs  1m0s                                                                                                                                                                           
ERRO[0060] thresholds on metrics 'http_req_duration{expected_response:true}' have been crossed