> k6 run --vus 100 --duration 1m k6.js

         /\      Grafana   /‾‾/  
    /\  /  \     |\  __   /  /   
   /  \/    \    | |/ /  /   ‾‾\ 
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/ 


     execution: local
        script: k6.js
        output: -

     scenarios: (100.00%) 1 scenario, 100 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 100 looping VUs for 1m0s (gracefulStop: 30s)



  █ THRESHOLDS 

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=9.38ms
    ✓ 'p(99)<800' p(99)=9.9ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS 

    checks_total.......: 715436  11922.522503/s
    checks_succeeded...: 100.00% 715436 out of 715436
    checks_failed......: 0.00%   0 out of 715436

    ✓ status is 200

    HTTP
    http_req_duration..............: avg=8.34ms min=2.03ms med=8.22ms max=125.54ms p(90)=9.07ms p(95)=9.38ms
      { expected_response:true }...: avg=8.34ms min=2.03ms med=8.22ms max=125.54ms p(90)=9.07ms p(95)=9.38ms
    http_req_failed................: 0.00%  0 out of 715436
    http_reqs......................: 715436 11922.522503/s

    EXECUTION
    iteration_duration.............: avg=8.38ms min=2.08ms med=8.25ms max=125.92ms p(90)=9.11ms p(95)=9.41ms
    iterations.....................: 715436 11922.522503/s
    vus............................: 100    min=100         max=100
    vus_max........................: 100    min=100         max=100

    NETWORK
    data_received..................: 122 MB 2.0 MB/s
    data_sent......................: 50 MB  835 kB/s




running (1m00.0s), 000/100 VUs, 715436 complete and 0 interrupted iterations
default ✓ [======================================] 100 VUs  1m0s

