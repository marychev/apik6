

```log
WORKERS - 6
=============
█ THRESHOLDS - Fail

    http_req_duration{expected_response:true}
    ✗ 'p(95)<300' p(95)=331.46ms
    ✓ 'p(99)<800' p(99)=532.07ms

█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=274.43ms
    ✓ 'p(99)<800' p(99)=536.58ms

█ THRESHOLDS - Fail

    http_req_duration{expected_response:true}
    ✗ 'p(95)<300' p(95)=473.74ms
    ✓ 'p(99)<800' p(99)=779.8ms

█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=235.63ms
    ✓ 'p(99)<800' p(99)=345.14ms


WORKERS - 1
=============
█ THRESHOLDS - Fail

    http_req_duration{expected_response:true}
    ✗ 'p(95)<300' p(95)=350.63ms
    ✓ 'p(99)<800' p(99)=588.72ms


█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=268.17ms
    ✓ 'p(99)<800' p(99)=460.88ms


█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=281.86ms
    ✓ 'p(99)<800' p(99)=442.18ms

█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=266.67ms
    ✓ 'p(99)<800' p(99)=368.16ms



WORKERS - 4 (лучший)
=============

█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=259.59ms
    ✓ 'p(99)<800' p(99)=397.94ms

█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=204.98ms
    ✓ 'p(99)<800' p(99)=280.74ms

█ THRESHOLDS + Passed

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=223.85ms
    ✓ 'p(99)<800' p(99)=313.75ms

█ THRESHOLDS

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=216.52ms
    ✓ 'p(99)<800' p(99)=295.13ms



WORKERS - 2
=============
█ THRESHOLDS

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=241.41ms
    ✓ 'p(99)<800' p(99)=418.31ms

█ THRESHOLDS

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=219.45ms
    ✓ 'p(99)<800' p(99)=299.09ms

█ THRESHOLDS

    http_req_duration{expected_response:true}
    ✓ 'p(95)<300' p(95)=203.4ms
    ✓ 'p(99)<800' p(99)=279.07ms

█ THRESHOLDS

    http_req_duration{expected_response:true}
    ✗ 'p(95)<300' p(95)=372.89ms
    ✓ 'p(99)<800' p(99)=638.3ms



```