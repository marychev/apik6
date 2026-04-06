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
    ✓ 'p(95)<300' p(95)=255.58ms
    ✓ 'p(99)<800' p(99)=399.14ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 46863   734.275976/s
    checks_succeeded...: 100.00% 46863 out of 46863
    checks_failed......: 0.00%   0 out of 46863

    ✓ status is 200

    HTTP
    http_req_duration..............: avg=135.85ms min=11.16ms med=114.18ms max=2.12s    p(90)=213.64ms p(95)=255.58ms
      { expected_response:true }...: avg=135.85ms min=11.16ms med=114.18ms max=2.12s    p(90)=213.64ms p(95)=255.58ms
    http_req_failed................: 0.00%  0 out of 46863
    http_reqs......................: 46863  734.275976/s

    EXECUTION
    iteration_duration.............: avg=128.04ms min=11.31ms med=114.24ms max=831.36ms p(90)=211.23ms p(95)=249.76ms
    iterations.....................: 46863  734.275976/s
    vus............................: 100    min=100        max=100
    vus_max........................: 100    min=100        max=100

    NETWORK
    data_received..................: 6.3 MB 99 kB/s
    data_sent......................: 4.8 MB 76 kB/s




running (1m03.8s), 000/100 VUs, 46863 complete and 0 interrupted iterations
default ✓ [======================================] 100 VUs  1m0s