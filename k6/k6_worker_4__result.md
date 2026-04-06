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
    ✗ 'p(95)<300' p(95)=302.9ms
    ✓ 'p(99)<800' p(99)=498.04ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 42266   667.441781/s
    checks_succeeded...: 100.00% 42266 out of 42266
    checks_failed......: 0.00%   0 out of 42266

    ✓ status is 200

    HTTP
    http_req_duration..............: avg=149.32ms min=15.76ms med=122.97ms max=2.07s   p(90)=234.78ms p(95)=302.9ms
      { expected_response:true }...: avg=149.32ms min=15.76ms med=122.97ms max=2.07s   p(90)=234.78ms p(95)=302.9ms
    http_req_failed................: 0.00%  0 out of 42266
    http_reqs......................: 42266  667.441781/s

    EXECUTION
    iteration_duration.............: avg=142.02ms min=15.9ms  med=123.13ms max=810.5ms p(90)=232.58ms p(95)=295.9ms
    iterations.....................: 42266  667.441781/s
    vus............................: 100    min=100        max=100
    vus_max........................: 100    min=100        max=100

    NETWORK
    data_received..................: 5.7 MB 90 kB/s
    data_sent......................: 4.4 MB 69 kB/s



                                                                                                                                                                                                                                           
running (1m03.3s), 000/100 VUs, 42266 complete and 0 interrupted iterations                                                                                                                                                                
default ✓ [======================================] 100 VUs  1m0s                                                                                                                                                                           
ERRO[0060] thresholds on metrics 'http_req_duration{expected_response:true}' have been crossed
