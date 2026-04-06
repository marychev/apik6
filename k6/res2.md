root@DESKTOP-0K1NMK9:/home/apik6# k6 run --vus 100 --duration 1m k6/k6.js

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
    ✗ 'p(95)<300' p(95)=345.94ms
    ✓ 'p(99)<800' p(99)=684.69ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 28568   456.431765/s
    checks_succeeded...: 100.00% 28568 out of 28568
    checks_failed......: 0.00%   0 out of 28568

    ✓ status is 200

    HTTP
    http_req_duration..............: avg=218.7ms  min=57.86ms med=190.9ms  max=1.56s p(90)=301.19ms p(95)=345.94ms
      { expected_response:true }...: avg=218.7ms  min=57.86ms med=190.9ms  max=1.56s p(90)=301.19ms p(95)=345.94ms
    http_req_failed................: 0.00%  0 out of 28568
    http_reqs......................: 28568  456.431765/s

    EXECUTION
    iteration_duration.............: avg=210.09ms min=57.97ms med=191.04ms max=1.16s p(90)=297.54ms p(95)=337.94ms
    iterations.....................: 28568  456.431765/s
    vus............................: 100    min=100        max=100
    vus_max........................: 100    min=100        max=100

    NETWORK
    data_received..................: 3.9 MB 62 kB/s
    data_sent......................: 2.9 MB 47 kB/s




running (1m02.6s), 000/100 VUs, 28568 complete and 0 interrupted iterations
default ✓ [======================================] 100 VUs  1m0s
ERRO[0060] thresholds on metrics 'http_req_duration{expected_response:true}' have been crossed
