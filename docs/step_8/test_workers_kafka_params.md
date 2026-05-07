# Тестируем приложение без Кликхауса, постепенно меняя нагрузки.

> VUS=2500 DURATION=1m k6 run k6/rps.js

- Железо: Intel i3-1005G1 (2 ядра / 4 потока), 8 GB RAM
- Конфигурация: FastAPI + aiokafka, uvicorn --workers X, Kafka Y broker

Настройки кафка при первом запуске.
```py
UVICORN_WORKERS=1
KAFKA_NUM_PARTITIONS=1
KAFKA_ENGINE_NUM_CONSUMERS=1
KAFKA_ENGINE_POLL_TIMEOUT_MS=1000
KAFKA_ENGINE_POLL_MAX_BATCH_SIZE=200000
KAFKA_ENGINE_FLUSH_INTERVAL_MS=10000
KAFKA_PRODUCER_LINGER_MS=20
KAFKA_PRODUCER_BATCH_SIZE=65536
KAFKA_PRODUCER_COMPRESSION=lz4
KAFKA_PRODUCER_ACKS=1
KAFKA_PRODUCER_IDEMPOTENT=false
KAFKA_NUM_NETWORK_THREADS=2
KAFKA_NUM_IO_THREADS=2
```

================================================================================

## I run = UVICORN_WORKERS=1

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS 
0bd8c23e1efa   apik6-api-1         100.26%   111.8MiB / 5.788GiB   1.89%     14.9MB / 27.4MB   0B / 852kB    6 
232e738e29ea   apik6-kafka-1       2.68%     359.9MiB / 5.788GiB   6.07%     5.39MB / 99kB     0B / 4.75MB   68 
fc370bc88fdf   apik6-zookeeper-1   0.52%     77.28MiB / 5.788GiB   1.30%     40.1kB / 28.9kB   0B / 750kB    49 
```

```log
длительность	        1m00.7s
VUs (max / active min)	2500 / 1546
RPS	                    1392
iterations	            84 452
status 200	            100% (0/84452 failed) 
p50 / p90 / p95	        1.84s / 2.18s / 2.24s
min / avg / max	        9.65ms / 1.77s / 29.26s
data in / out	        188 / 143 kB/s
```

#### Объяснения логов:

* 0/84452 failed — ноль провалов из 84 452 запросов
* data in (received) = 188 kB/s	k6 получает от сервера (тела ответов + заголовки)
* data out (sent)	143 kB/s	k6 отправляет на сервер (тела запросов + заголовки)

Это сетевой трафик во время теста (со стороны k6-клиента). При 1392 RPS это ≈ 135 B на ответ и 103 B на запрос в среднем — т.е. payload очень маленький.


================================================================================

## II run = UVICORN_WORKERS=2

```sh
# docker stats 
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O       PIDS 
b9a104df1f29   apik6-zookeeper-1   0.12%     82.59MiB / 5.788GiB   1.39%     26.9kB / 21.3kB   4.1kB / 393kB   49 
956bdb8c919f   apik6-kafka-1       5.30%     351.7MiB / 5.788GiB   5.93%     4.09MB / 74.6kB   639kB / 537kB   68 
460577079f16   apik6-api-1         189.45%   177.6MiB / 5.788GiB   3.00%     12.5MB / 20.9MB   578kB / 889kB   15 
```

```log
длительность           1m00.3s
VUs (max / active min) 2500 / 1525
RPS                    2626
iterations             158 271
status 200             100% (0/158271 failed)
p50 / p90 / p95        955ms / 1.27s / 1.37s
min / avg / max        7.88ms / 938ms / 17.92s
data in / out          355 / 270 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 1776
RPS                    2745
iterations             165 450
status 200             100% (0/165450 failed)
p50 / p90 / p95        909ms / 1.21s / 1.29s
min / avg / max        6.06ms / 894ms / 14.88s
data in / out          371 / 283 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    2827
iterations             170 572
status 200             100% (0/170572 failed)
p50 / p90 / p95        878ms / 1.31s / 1.39s
min / avg / max        7.01ms / 872ms / 5.13s
data in / out          382 / 291 kB/s
```

================================================================================

## III run = UVICORN_WORKERS=3

```sh
# docker stats 
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O    PIDS 
e7bf8f921b4f   apik6-zookeeper-1   0.33%     78.52MiB / 5.788GiB   1.32%     21.1kB / 18.3kB   0B / 279kB   49 
be3bf6c9f4bb   apik6-kafka-1       5.03%     350MiB / 5.788GiB     5.91%     3.53MB / 71.5kB   0B / 815kB   68 
46857bb17908   apik6-api-1         247.55%   216.7MiB / 5.788GiB   3.66%     11.3MB / 18.1MB   0B / 889kB   21 
```

```log
длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3125
iterations             188 236
status 200             100% (0/188236 failed)
p50 / p90 / p95        806ms / 1.17s / 1.31s
min / avg / max        3.27ms / 790ms / 4.57s
data in / out          422 / 322 kB/s

длительность           1m00.7s
VUs (max / active min) 2500 / 1270
RPS                    3244
iterations             197 033
status 200             100% (0/197033 failed)
p50 / p90 / p95        649ms / 1.10s / 1.25s
min / avg / max        3.11ms / 755ms / 25.18s
data in / out          438 / 334 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3219
iterations             194 045
status 200             100% (0/194045 failed)
p50 / p90 / p95        666ms / 1.14s / 1.31s
min / avg / max        3.75ms / 762ms / 23.27s
data in / out          435 / 332 kB/s
```


================================================================================

## IV  run = UVICORN_WORKERS=4

```sh
# docker stats 
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS 
ab895ee94b06   apik6-zookeeper-1   0.29%     75.55MiB / 5.788GiB   1.27%     21kB / 17.3kB     0B / 348kB    49 
0172a88b8c80   apik6-kafka-1       5.09%     357.2MiB / 5.788GiB   6.03%     8.23MB / 127kB    0B / 7.85MB   68 
146ce59e1448   apik6-api-1         294.03%   256.2MiB / 5.788GiB   4.32%     25.8MB / 41.7MB   0B / 979kB    27 
```

```log
длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3195
iterations             192 764
status 200             100% (0/192764 failed)
p50 / p90 / p95        746ms / 1.22s / 1.38s
min / avg / max        1.14ms / 770ms / 3.03s
data in / out          431 / 329 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2336
RPS                    3336
iterations             201 186
status 200             100% (0/201186 failed)
p50 / p90 / p95        727ms / 1.18s / 1.32s
min / avg / max        4.38ms / 736ms / 2.62s
data in / out          450 / 344 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3467
iterations             208 774
status 200             100% (0/208774 failed)
p50 / p90 / p95        701ms / 1.12s / 1.31s
min / avg / max        3.64ms / 710ms / 5.70s
data in / out          468 / 357 kB/s
```

================================================================================

## V  run = UVICORN_WORKERS=5 - !!!

```sh
# docker stats 
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS 
9cdd661add5e   apik6-zookeeper-1   0.13%     78.13MiB / 5.788GiB   1.32%     25.6kB / 21.7kB   0B / 389kB    51 
6b3e634e8636   apik6-kafka-1       4.53%     361.4MiB / 5.788GiB   6.10%     16.2MB / 237kB    0B / 14.4MB   68 
ee22518ce4c8   apik6-api-1         303.48%   299.2MiB / 5.788GiB   5.05%     49.5MB / 82.2MB   0B / 889kB    33 
```

```log
длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3458
iterations             208 668
status 200             100% (0/208668 failed)
p50 / p90 / p95        685ms / 1.18s / 1.33s
min / avg / max        5.13ms / 714ms / 3.15s
data in / out          467 / 356 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3274
iterations             197 655
status 200             100% (0/197655 failed)
p50 / p90 / p95        588ms / 1.25s / 1.44s
min / avg / max        3.62ms / 752ms / 23.18s
data in / out          442 / 337 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3397
iterations             205 149
status 200             100% (0/205149 failed)
p50 / p90 / p95        684ms / 1.23s / 1.40s
min / avg / max        4.19ms / 724ms / 3.28s
data in / out          459 / 350 kB/s
```


================================================================================

## VI  run = UVICORN_WORKERS=6

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O       PIDS 
a127234e6fea   apik6-zookeeper-1   0.24%     75.94MiB / 5.788GiB   1.28%     24.2kB / 22.2kB   4.1kB / 262kB   49 
0c4672adf501   apik6-kafka-1       5.27%     352.7MiB / 5.788GiB   5.95%     4.56MB / 98.1kB   0B / 2.72MB     68 
4e501924d0c8   apik6-api-1         285.71%   337.4MiB / 5.788GiB   5.69%     14.4MB / 23.4MB   0B / 889kB      39 
```

```log
длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3320
iterations             200 475
status 200             100% (0/200475 failed)
p50 / p90 / p95        635ms / 1.30s / 1.50s
min / avg / max        10.65ms / 744ms / 3.21s
data in / out          448 / 342 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3130
iterations             188 558
status 200             100% (0/188558 failed)
p50 / p90 / p95        674ms / 1.39s / 1.64s
min / avg / max        4.23ms / 788ms / 14.66s
data in / out          423 / 322 kB/s
```

================================================================================

## VII  run = UVICORN_WORKERS=4 | KAFKA_NUM_PARTITIONS=2 | KAFKA_ENGINE_NUM_CONSUMERS=2

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS 
7fe2efd7c679   apik6-zookeeper-1   3.93%     103.9MiB / 5.788GiB   1.75%     36.8kB / 29.6kB   74.9MB / 557kB    50 
175598ad3022   apik6-kafka-1       12.75%    429.7MiB / 5.788GiB   7.25%     55.8MB / 474kB    94.6MB / 56.3MB   68 
1501912e907f   apik6-api-1         372.94%   276.7MiB / 5.788GiB   4.67%     176MB / 282MB     42MB / 1.02MB     27 
```

```log
длительность           1m00.5s
VUs (max / active min) 2500 / 847
RPS                    3465
iterations             209 527
status 200             100% (0/209527 failed)
p50 / p90 / p95        674ms / 1.07s / 1.33s
min / avg / max        7.00ms / 708ms / 3.21s
data in / out          468 / 357 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 533
RPS                    3576
iterations             216 000
status 200             100% (0/216000 failed)
p50 / p90 / p95        637ms / 1.19s / 1.54s
min / avg / max        5.64ms / 684ms / 8.53s
data in / out          483 / 368 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 1418
RPS                    3729
iterations             225 288
status 200             100% (0/225288 failed)
p50 / p90 / p95        522ms / 874ms / 1.00s
min / avg / max        4.40ms / 658ms / 41.00s
data in / out          503 / 384 kB/s
```

_active min < max (например 2500/847):	были моменты, когда часть VU простаивала → сервер успевал отвечать быстрее, чем VU генерировали нагрузку, либо ramp-up/ramp-down фазы (старт/остановка теста)_


================================================================================

## VIII  run = UVICORN_WORKERS=5 | KAFKA_NUM_PARTITIONS=2 | KAFKA_ENGINE_NUM_CONSUMERS=2

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O    PIDS 
cfe59511f402   apik6-zookeeper-1   0.15%     76.64MiB / 5.788GiB   1.29%     22kB / 18.8kB     0B / 315kB   49 
5f959d490fdf   apik6-kafka-1       13.51%    349.8MiB / 5.788GiB   5.90%     370kB / 41.7kB    0B / 262kB   68 
0185032927e2   apik6-api-1         231.64%   283.1MiB / 5.788GiB   4.78%     2.53MB / 2.84MB   0B / 889kB   33 

CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O    PIDS 
cfe59511f402   apik6-zookeeper-1   0.15%     76.64MiB / 5.788GiB   1.29%     22.5kB / 19kB     0B / 344kB   49 
5f959d490fdf   apik6-kafka-1       32.22%    356.9MiB / 5.788GiB   6.02%     4.73MB / 79.3kB   0B / 279kB   68 
0185032927e2   apik6-api-1         230.70%   299MiB / 5.788GiB     5.04%     16MB / 24.6MB     0B / 889kB   33 

CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS 
cfe59511f402   apik6-zookeeper-1   0.18%     76.66MiB / 5.788GiB   1.29%     25.2kB / 20.6kB   0B / 455kB    49 
5f959d490fdf   apik6-kafka-1       2.94%     365MiB / 5.788GiB     6.16%     16MB / 166kB      0B / 14.6MB   68 
0185032927e2   apik6-api-1         277.45%   302MiB / 5.788GiB     5.09%     50.9MB / 81.6MB   0B / 889kB    33  
```

```log
длительность           1m00.4s
VUs (max / active min) 2500 / 2500
RPS                    3508
iterations             211 833
status 200             100% (0/211833 failed)
p50 / p90 / p95        678ms / 1.13s / 1.28s
min / avg / max        4.92ms / 699ms / 12.91s
data in / out          474 / 361 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 2500
RPS                    3658
iterations             221 125
status 200             100% (0/221125 failed)
p50 / p90 / p95        652ms / 1.08s / 1.23s
min / avg / max        6.02ms / 672ms / 12.53s
data in / out          494 / 377 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 2500
RPS                    3761
iterations             227 013
status 200             100% (0/227013 failed)
p50 / p90 / p95        606ms / 1.08s / 1.24s
min / avg / max        3.11ms / 653ms / 18.33s
data in / out          508 / 387 kB/s
```


================================================================================

## IX  run = UVICORN_WORKERS=4 | KAFKA_NUM_PARTITIONS=3 | KAFKA_ENGINE_NUM_CONSUMERS=3

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS 
0a1ec23116b8   apik6-zookeeper-1   0.14%     101.8MiB / 5.788GiB   1.72%     32.2kB / 29.4kB   74.8MB / 332kB    49 
9fcdfc916642   apik6-kafka-1       30.89%    425.3MiB / 5.788GiB   7.18%     635kB / 64.8kB    94.6MB / 250kB    69 
5de04ab880af   apik6-api-1         262.38%   263.2MiB / 5.788GiB   4.44%     3.57MB / 4.29MB   41.9MB / 1.05MB   27 

CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS 
0a1ec23116b8   apik6-zookeeper-1   0.13%     102.2MiB / 5.788GiB   1.72%     36.9kB / 32.2kB   74.8MB / 496kB    49 
9fcdfc916642   apik6-kafka-1       2.49%     439.7MiB / 5.788GiB   7.42%     33.5MB / 289kB    94.6MB / 30.6MB   68 
5de04ab880af   apik6-api-1         281.64%   274.9MiB / 5.788GiB   4.64%     104MB / 169MB     41.9MB / 1.05MB   27 
```

```log
длительность           1m00.4s
VUs (max / active min) 2500 / 326
RPS                    3579
iterations             216 216
status 200             100% (0/216216 failed)
p50 / p90 / p95        618ms / 1.21s / 1.38s
min / avg / max        1.10ms / 684ms / 4.06s
data in / out          483 / 369 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 2312
RPS                    3873
iterations             233 892
status 200             100% (0/233892 failed)
p50 / p90 / p95        421ms / 1.03s / 1.16s
min / avg / max        10.57ms / 635ms / 47.63s
data in / out          523 / 399 kB/s

длительность           1m01.0s
VUs (max / active min) 2500 / 832
RPS                    3395
iterations             207 233
status 200             100% (0/207233 failed)
p50 / p90 / p95        619ms / 1.26s / 1.52s
min / avg / max        7.27ms / 714ms / 7.92s
data in / out          458 / 350 kB/s
```


================================================================================

## X  run = UVICORN_WORKERS=5 | KAFKA_NUM_PARTITIONS=3 | KAFKA_ENGINE_NUM_CONSUMERS=3

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O    PIDS 
e782ef62e33d   apik6-zookeeper-1   0.31%     78.48MiB / 5.788GiB   1.32%     25.3kB / 23kB     0B / 328kB   50 
7fd7760539d2   apik6-kafka-1       25.50%    373.2MiB / 5.788GiB   6.30%     4.85MB / 75.8kB   0B / 1.3MB   68 
912c5f4d430e   apik6-api-1         252.41%   298.7MiB / 5.788GiB   5.04%     15.4MB / 25.1MB   0B / 889kB   33 

CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS 
e782ef62e33d   apik6-zookeeper-1   0.15%     78.54MiB / 5.788GiB   1.33%     28.1kB / 24.6kB   0B / 401kB    50 
7fd7760539d2   apik6-kafka-1       5.14%     383.2MiB / 5.788GiB   6.46%     27.5MB / 226kB    0B / 22.9MB   68 
912c5f4d430e   apik6-api-1         292.24%   305.2MiB / 5.788GiB   5.15%     83.9MB / 139MB    0B / 889kB    33 
 
```

```log
длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3587
iterations             216 279
status 200             100% (0/216279 failed)
p50 / p90 / p95        580ms / 1.29s / 1.55s
min / avg / max        5.13ms / 684ms / 3.48s
data in / out          484 / 370 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 2500
RPS                    3786
iterations             228 591
status 200             100% (0/228591 failed)
p50 / p90 / p95        532ms / 1.22s / 1.39s
min / avg / max        7.19ms / 647ms / 17.02s
data in / out          511 / 390 kB/s

длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3857
iterations             232 492
status 200             100% (0/232492 failed)
p50 / p90 / p95        497ms / 1.19s / 1.38s
min / avg / max        8.20ms / 637ms / 25.51s
data in / out          521 / 397 kB/s
```


================================================================================

## XI  run = UVICORN_WORKERS=5 | KAFKA_NUM_PARTITIONS=3 | KAFKA_ENGINE_NUM_CONSUMERS=3 | KAFKA_NUM_NETWORK_THREADS=3 | KAFKA_NUM_IO_THREADS=3

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O    PIDS 
ecacae0bcd35   apik6-zookeeper-1   1.89%     76.47MiB / 5.788GiB   1.29%     26.7kB / 23.8kB   0B / 328kB   50 
13960f7b5f37   apik6-kafka-1       4.96%     360.2MiB / 5.788GiB   6.08%     5.62MB / 92.6kB   0B / 217kB   71 
44e3b039709d   apik6-api-1         310.96%   300.8MiB / 5.788GiB   5.07%     18.1MB / 29.1MB   0B / 889kB   33 

```

```log
длительность           1m00.3s
VUs (max / active min) 2500 / 2500
RPS                    3678
iterations             221 923
status 200             100% (0/221923 failed)
p50 / p90 / p95        536ms / 1.30s / 1.51s
min / avg / max        7.05ms / 667ms / 3.65s
data in / out          497 / 379 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 2500
RPS                    3835
iterations             231 762
status 200             100% (0/231762 failed)
p50 / p90 / p95        535ms / 1.21s / 1.46s
min / avg / max        6.74ms / 641ms / 2.55s
data in / out          518 / 395 kB/s

длительность           1m00.5s
VUs (max / active min) 2500 / 491
RPS                    3888
iterations             235 302
status 200             100% (0/235302 failed)
p50 / p90 / p95        492ms / 1.17s / 1.39s
min / avg / max        6.87ms / 630ms / 27.43s
data in / out          525 / 401 kB/s
```

================================================================================

## XII  run = ADVICES OF CLOUDE

```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O    PIDS 
2e16465ac9ee   apik6-zookeeper-1   0.15%     76.4MiB / 5.788GiB    1.29%     25.1kB / 22.9kB   0B / 262kB   49 
79e79dd51334   apik6-kafka-1       28.98%    344.2MiB / 5.788GiB   5.81%     185kB / 50.7kB    0B / 184kB   70 
16d2055ebb69   apik6-api-1         208.51%   251.3MiB / 5.788GiB   4.24%     1.8MB / 1.79MB    0B / 983kB   27 

CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O    PIDS 
2e16465ac9ee   apik6-zookeeper-1   0.15%     75.69MiB / 5.788GiB   1.28%     25.7kB / 23.3kB   0B / 279kB   49 
79e79dd51334   apik6-kafka-1       8.05%     354.9MiB / 5.788GiB   5.99%     8.24MB / 86.3kB   0B / 229kB   70 
16d2055ebb69   apik6-api-1         291.51%   255.4MiB / 5.788GiB   4.31%     26.9MB / 42.2MB   0B / 983kB   27 
```

```log
длительность           1m00.4s
VUs (max / active min) 2500 / 1926
RPS                    3809
iterations             230 040
status 200             100% (0/230040 failed)
p50 / p90 / p95        615ms / 912ms / 1.03s
min / avg / max        32.22ms / 643ms / 3.79s
data in / out          514 / 392 kB/s

длительность           1m00.4s
VUs (max / active min) 2500 / 2500
RPS                    4097
iterations             247 416
status 200             100% (0/247416 failed)
p50 / p90 / p95        512ms / 995ms / 1.15s
min / avg / max        51.59ms / 597ms / 7.41s
data in / out          553 / 422 kB/s

```


Изучил .env, docker-compose.yml и твою историю тестов. Важный момент: ClickHouse сейчас закомментирован, поэтому параметры KAFKA_ENGINE_* (consumer-сторона) не влияют на текущий тест — нагружается только producer-side и брокер.

Рекомендуемая конфигурация под 2 ядра
```
UVICORN_WORKERS=4

KAFKA_NUM_PARTITIONS=4

KAFKA_ENGINE_NUM_CONSUMERS=4
KAFKA_ENGINE_POLL_TIMEOUT_MS=500
KAFKA_ENGINE_POLL_MAX_BATCH_SIZE=500000
KAFKA_ENGINE_FLUSH_INTERVAL_MS=7500

KAFKA_PRODUCER_LINGER_MS=50
KAFKA_PRODUCER_BATCH_SIZE=262144
KAFKA_PRODUCER_COMPRESSION=lz4
KAFKA_PRODUCER_ACKS=1
KAFKA_PRODUCER_IDEMPOTENT=false

KAFKA_NUM_NETWORK_THREADS=2
KAFKA_NUM_IO_THREADS=4
```

Что и зачем поменял
```log
параметр	                было → стало	        почему
UVICORN_WORKERS	            5 → 4	                5 на 2 ядрах = лишний context-switch; 4 даёт чуть меньше CPU-конкуренции при сохранении параллелизма producer'ов
KAFKA_NUM_PARTITIONS	    3 → 4	                кратно числу uvicorn workers и consumers — равномерное распределение
KAFKA_PRODUCER_LINGER_MS	20 → 50	                крупнее батчи → меньше сетевых запросов к брокеру, выше throughput (latency +30ms некритично при p95=1.4s)
KAFKA_PRODUCER_BATCH_SIZE	65536 → 262144 (256KB)	вмещает больше сообщений в один батч — главный рычаг throughput
KAFKA_NUM_NETWORK_THREADS	3 → 2	                на 2 ядрах больше потоков ≠ быстрее, лишь конкурируют
KAFKA_NUM_IO_THREADS	    3 → 4	                основная работа брокера — диск; чуть больший пул помогает
KAFKA_ENGINE_*	            подкручено	            пригодится когда включишь ClickHouse
```

Что оставил как было (правильно подобрано)
- COMPRESSION	lz4	лучший баланс CPU/сети
- ACKS	1	    не теряем данные при падении leader, но не ждём всех реплик
- IDEMPOTENT	false	максимум скорости (включать только при exactly-once)



## XIII  run = ADVICES OF CLOUDE

Главные кандидаты на дальнейший тюнинг
- LINGER_MS — попробовать 100 (если max latency не критичен)
- BATCH_SIZE — попробовать 524288 (512KB)
- UVICORN_WORKERS — погонять 3 vs 4 vs 5 на этом же конфиге


```sh
# docker stats
CONTAINER ID   NAME                CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O     PIDS 
0c4fae65a460   apik6-zookeeper-1   0.12%     81.12MiB / 5.788GiB   1.37%     28.4kB / 25.9kB   0B / 295kB    49 
ca1b6243fd94   apik6-kafka-1       12.14%    359.3MiB / 5.788GiB   6.06%     2.27MB / 76.8kB   0B / 1.58MB   70 
436849cb89d2   apik6-api-1         252.29%   291.7MiB / 5.788GiB   4.92%     8.49MB / 12.4MB   0B / 889kB    33 

```

```log
длительность           1m00.4s
VUs (max / active min) 2500 / 2500
RPS                    3945
iterations             238 174
status 200             100% (0/238174 failed)
p50 / p90 / p95        591ms / 918ms / 1.03s
min / avg / max        9.85ms / 623ms / 4.68s
data in / out          533 / 406 kB/s

```


================================================================================

- [ ][ ]: в docker-compose.yml в секцию kafka: добавить KAFKA_HEAP_OPTS: "-Xmx1G -Xms1G".

================================================================================

> как мне проверить что после перезапуска применилась новая настройка UVICORN_WORKERS
```sh
docker logs apik6-api-1 2>&1 | grep "Started server process"
# docker exec apik6-api-1 printenv UVICORN_WORKERS
# docker exec apik6-api-1 sh -c 'grep -l uvicorn /proc/*/cmdline 2>/dev/null | wc -l'
```


---------------------------------------------------------------------------------
---------------------------------------------------------------------------------
---------------------------------------------------------------------------------

## Параметр и его объяснение

> UVICORN_WORKERS — количество процессов-воркеров uvicorn, обслуживающих HTTP-запросы.
- что делает:           запускает N независимых процессов приложения, каждый со своим event loop
- зачем:                обойти GIL Python и задействовать несколько ядер CPU
- как масштабируется:	каждый воркер = +1 процесс в памяти, делит порт через SO_REUSEPORT
- типичное значение:    2 × CPU_cores (для CPU-bound) или = CPU_cores (для I/O-bound с asyncio)
- на 2 ядрах:   	    разумно 2–4; больше — рост context-switch без выигрыша
- где используется:     uvicorn app:main --workers $UVICORN_WORKERS или в CMD Dockerfile

> KAFKA_NUM_PARTITIONS — число партиций при создании топика.
- что делает:       	делит топик на N независимых очередей
- зачем:            	параллелизм потребителей: 1 партиция = 1 consumer одновременно
- как масштабируется:	больше партиций → больше параллельных consumer'ов; но растёт overhead на брокере
- типичное значение:	= числу consumer'ов в группе или кратно ему
- на 2 ядрах:       	2–4 разумно; 1 = строго последовательная обработка

> KAFKA_ENGINE_NUM_CONSUMERS — сколько consumer-потоков в одной таблице Kafka Engine.
- что делает:       	запускает N тредов, читающих из топика параллельно
- зачем:            	ускорить чтение из Kafka в CH, если партиций > 1
- ограничение:      	не больше числа партиций (лишние треды простаивают)

> KAFKA_ENGINE_POLL_TIMEOUT_MS — макс. время ожидания батча при опросе брокера.
- что делает:       	как долго consumer ждёт сообщений за один poll()
- trade-off:        	больше → крупнее батчи, выше латентность; меньше → быстрее реакция, мельче батчи
- типично:          	100–5000 ms

> KAFKA_ENGINE_POLL_MAX_BATCH_SIZE — максимум строк, забираемых за один poll.
- что делает:       	верхний предел сообщений на один цикл чтения
- зачем:            	крупные батчи = меньше overhead на запись в MergeTree
- trade-off:        	больше → выше throughput, выше память и латентность

> KAFKA_ENGINE_FLUSH_INTERVAL_MS — как часто CH сбрасывает накопленные данные в целевую таблицу.
- что делает:       	принудительный flush, если батч не дошёл до max_block_size
- зачем:            	гарантирует, что данные не «застрянут» при низком трафике
- trade-off:        	больше → крупнее части (parts), меньше merge-нагрузка; меньше → свежее данные, больше мелких parts

> KAFKA_PRODUCER_LINGER_MS — задержка перед отправкой батча.
- что делает:       	producer ждёт linger_ms, чтобы накопить больше сообщений в батч
- trade-off:        	0 = моментально (мелкие батчи); 5–50 = выше throughput, +latency

> KAFKA_PRODUCER_BATCH_SIZE — макс. размер одного батча в байтах.
- что делает:       	верхний лимит на размер батча перед отправкой
- trade-off:        	больше → реже сетевые запросы, выше throughput; больше памяти на producer
- типично:            	16384–1048576 (16KB–1MB)

> KAFKA_PRODUCER_COMPRESSION — алгоритм сжатия батчей.
- none:             	без сжатия — минимум CPU, максимум сети
- lz4:              	быстрый, средняя степень сжатия — лучший баланс
- snappy:           	похож на lz4, чуть медленнее
- gzip:             	сильное сжатие, дорогой по CPU
- zstd:             	сильное сжатие, эффективнее gzip

> KAFKA_PRODUCER_ACKS — уровень подтверждения от брокеров.
значение	смысл	                    trade-off
- 0	        producer не ждёт ack	    максимум скорости, риск потери
- 1	        ждёт ack от leader-брокера	баланс скорости и надёжности
- all/-1	ждёт ack от всех реплик	    максимум надёжности, минимум скорости

> KAFKA_PRODUCER_IDEMPOTENT — гарантия отсутствия дублей при ретраях.
- что делает:      	producer присваивает sequence-номер сообщениям; брокер дедуплицирует
- зачем:        	при сетевых сбоях ретраи не создают дубли
- trade-off:    	требует acks=all и снижает throughput на ~5–10%
- значение:     	true для exactly-once семантики; false для максимальной скорости

> KAFKA_NUM_NETWORK_THREADS — число сетевых потоков брокера.
- что делает:   	    потоки, принимающие соединения от клиентов и читающие/пишущие сетевые буферы
- зачем:        	    обработка сетевого I/O — приём запросов от producer'ов/consumer'ов, отправка ответов
- как масштабируется:	больше клиентов / выше throughput → больше потоков
- дефолт:           	3
- типичное значение:	3–8; равно или чуть меньше числа CPU-ядер
- симптом нехватки: 	растёт RequestQueueTimeMs, очередь запросов на брокере

> KAFKA_NUM_IO_THREADS — число потоков обработки запросов (дисковый I/O).
- что делает:       	читают запросы из очереди и выполняют их: пишут на диск, читают сегменты лога
- зачем:            	основная работа брокера — persist'ить сообщения на диск и отдавать по запросу
- как масштабируется:	упирается в диск; больше потоков ≠ больше IOPS, если диск медленный
- дефолт:           	8
- типичное значение:	8–16; ≈ 2× числа дисков
- симптом нехватки: 	растёт RequestHandlerAvgIdlePercent ↓ (близко к 0), запросы копятся

_На 2-ядерной машине ставить >4 / >8 обычно бессмысленно — потоки начнут конкурировать за CPU._


---------------------------------------------------------------------------------
---------------------------------------------------------------------------------
---------------------------------------------------------------------------------

### Полезные команды

Топики

```sh
# список топиков
docker exec -it <kafka_container> kafka-topics.sh --bootstrap-server localhost:9092 --list

# детали по топику (партиции, replication)
docker exec -it <kafka_container> kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic <topic_name>

# все топики разом
docker exec -it <kafka_container> kafka-topics.sh --bootstrap-server localhost:9092 --describe
```


Сообщения / лаг

```sh
# количество сообщений в топике (high - low watermark по партициям)
docker exec -it <kafka_container> kafka-run-class.sh kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic <topic_name>

# почитать последние N сообщений (Ctrl+C чтобы выйти)
docker exec -it <kafka_container> kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic <topic_name> --from-beginning --max-messages 5

# хвост (только новые)
docker exec -it <kafka_container> kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic <topic_name>
```


Consumer groups (главное для лага)

```sh
# список групп
docker exec -it <kafka_container> kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# лаг по группе — CURRENT-OFFSET, LOG-END-OFFSET, LAG
docker exec -it <kafka_container> kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group <group_name>

# лаг по всем группам
docker exec -it <kafka_container> kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups
```


Брокер / здоровье

```sh
# логи брокера
docker logs --tail 100 <kafka_container>

# конфиг брокера
docker exec -it <kafka_container> kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-name 1 --describe
```