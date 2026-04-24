# Инструменты профилирования FastAPI/uvicorn

## Sampling-профайлеры (низкий overhead, подходят для продакшена)

- **py-spy** — золотой стандарт для Python. Подключается к уже запущенному процессу по PID, не требует изменений кода, умеет делать flame graphs. Для uvicorn-воркеров: `py-spy record -o profile.svg --pid <PID>` или `py-spy top --pid <PID>` для интерактивного режима. Работает с async — с флагом `--idle` показывает ожидающие корутины, что критично для FastAPI.
- **Pyroscope / Grafana Pyroscope** — continuous profiling в проде, под капотом тот же py-spy. Разворачивается как сайдкар, даёт flame graphs за произвольные временные окна. Полезно, когда надо поймать деградацию, воспроизводящуюся раз в сутки.
- **Austin** — альтернатива py-spy, C-шный frame stack sampler. Интегрируется с VS Code через расширение.

## Deterministic / tracing-профайлеры (высокий overhead, для разработки)

- **cProfile** — встроен в stdlib. Для FastAPI удобнее всего подключать через middleware, профилирующее конкретный запрос, либо через `pyinstrument` (см. ниже). cProfile "из коробки" неудобен для async, но меряет всё достаточно неплохо.
- **Pyinstrument** — statistical profiler, хорошо работает с FastAPI: middleware, которое можно вешать на endpoint. Есть готовая интеграция с FastAPI: middleware, которое при `?profile` в запросе возвращает HTML с деревом вызовов вместо ответа. Правильно работает с async (показывает, где реально висела на await).
- **Scalene** — профилирует CPU, GPU, память, показывает Python vs. native расширения. Полезно, когда узкое место может быть в numpy/pandas/ORM.

---

## py-spy: практика

### Команды

```bash
# Установка
pip install py-spy

# Найти PID процесса
ps aux | grep uvicorn

# Интерактивный профиль (top)
py-spy top --pid <PID> --idle

# Записать flame graph в SVG
py-spy record -o profile.svg --pid <PID> --idle
```

### Что меряли

- **Нагрузка:** `VUS=2500 DURATION=1m k6 run k6/rps.js`
- **Процесс:** мастер-процесс uvicorn (PID 100538)
- **Конфигурация:** `--workers 5`

### Результаты тестирования

| Метрика | Прогон 1 | Прогон 2 |
|---------|----------|----------|
| VUS (цель) | 2500 | 2500 |
| VUS (факт) | 547 | 231 |
| RPS | 1683 | 1991 |
| p(95) | 2.55s | 1.85s |
| errors | 0.50% | 0.24% |

### Выводы

1. **Мастер-процесс uvicorn** не обрабатывает запросы напрямую — он только координирует воркеры.
2. **Основное время** мастер-процесса уходит на:
   - `wait (threading.py)` — ~90% — ожидание воркеров
   - `select (selectors.py)` — I/O мультиплексинг
   - `is_alive`, `ping` (uvicorn/supervisors) — проверка здоровья воркеров
   - multiprocessing (recv/send) — IPC между мастером и воркерами
3. **Система не выдерживает VUS=2500** — фактически достигает только 231–547 VU.
4. Для получения реальной картины обработки запросов нужно профилировать **дочерние процессы-воркеры** (не мастер).

```log
py-spy top --pid 100538 --idle

Collecting samples from '/usr/local/bin/python3.12 /usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 5' (python v3.12.13)
Total Samples 9700
GIL: 0.00%, Active: 0.00%, Threads: 1

  %Own   %Total  OwnTime  TotalTime  Function (filename)                                                                                                                       
100.00% 100.00%   90.88s    90.93s   wait (threading.py)
  0.00%   0.00%    5.09s     5.09s   select (selectors.py)
  0.00%   0.00%   0.260s    0.260s   _send (multiprocessing/connection.py)
  0.00%   0.00%   0.170s    0.170s   __init__ (multiprocessing/reduction.py)
  0.00%   0.00%   0.110s    0.280s   dumps (multiprocessing/reduction.py)
  0.00%   0.00%   0.110s    0.110s   _recv (multiprocessing/connection.py)
  0.00%   0.00%   0.080s    0.080s   register (selectors.py)
  0.00%   0.00%   0.070s    0.180s   recv (multiprocessing/connection.py)
  0.00%   0.00%   0.070s     5.25s   wait (multiprocessing/connection.py)
  0.00%   0.00%   0.050s    0.050s   _acquire_restore (threading.py)
  0.00%   0.00%   0.040s    0.060s   is_alive (multiprocessing/process.py)
  0.00%   0.00%   0.020s    0.020s   poll (multiprocessing/popen_fork.py)
  0.00%   0.00%   0.010s    0.010s   _check_closed (multiprocessing/connection.py)
  0.00%   0.00%   0.010s     5.26s   _poll (multiprocessing/connection.py)
  0.00%   0.00%   0.010s    0.010s   close (selectors.py)
  0.00%   0.00%   0.010s    0.270s   _send_bytes (multiprocessing/connection.py)
  0.00%   0.00%   0.010s     6.07s   keep_subprocess_alive (uvicorn/supervisors/multiprocess.py)
  0.00% 100.00%   0.000s    97.00s   main (uvicorn/main.py)
  0.00%   0.00%   0.000s    0.560s   send (multiprocessing/connection.py)
  0.00% 100.00%   0.000s    97.00s   run (uvicorn/main.py)
  0.00%   0.00%   0.000s    0.110s   _recv_bytes (multiprocessing/connection.py)
  0.00%   0.00%   0.000s    0.010s   __exit__ (selectors.py)
  0.00% 100.00%   0.000s    97.00s   __call__ (click/core.py)
  0.00% 100.00%   0.000s    97.00s   <module> (uvicorn)
  0.00%   0.00%   0.000s     6.00s   ping (uvicorn/supervisors/multiprocess.py)
  0.00%   0.00%   0.000s     5.26s   poll (multiprocessing/connection.py)
  0.00% 100.00%   0.000s    97.00s   run (uvicorn/supervisors/multiprocess.py)
  0.00%   0.00%   0.000s     6.06s   is_alive (uvicorn/supervisors/multiprocess.py)
  0.00% 100.00%   0.000s    97.00s   invoke (click/core.py)
  0.00% 100.00%   0.000s    97.00s   main (click/core.py)
```


### Следующий шаг

Профилировать отдельные uvicorn-воркеры (дочерние процессы), которые появляются при запуске с `--workers 5`.

---

## cProfile: практика

### Команды

```bash
# Запуск скрипта с профилированием
python -m cProfile -o profile.stats your_script.py

# Анализ результатов (интерактивно)
python -m cProfile -m your_module

# Сохранить и потом посмотреть
python -m cProfile -o profile.stats -m your_module
```

### Для FastAPI

**Вариант 1: через middleware (для конкретного endpoint)**

```python
# app/middleware/profiler.py
import cProfile
import pstats
from io import StringIO

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class ProfilerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        profiler = cProfile.Profile()
        profiler.enable()
        
        response = await call_next(request)
        
        profiler.disable()
        
        # Выводим в консоль или возвращаем по запросу
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print(20)  # топ 20
        print(s.getvalue())
        
        return response
```

**Вариант 2: обёртка для функции**

```python
import cProfile
import pstats
from io import StringIO

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print(20)
    return result, s.getvalue()
```

### Ограничения cProfile

- **Высокий overhead** — замедляет приложение в 2-10x
- **Не очень для async** — плохо видит await
- **Лучше для разработки**, не для прода

### Следующий шаг

Добавить middleware в приложение и протестировать на endpoint.

---


## Austin

### Установка

`austin` из apt — устаревший (1.x), несовместим с `austin-tui` (ждёт бинарный формат MOJO, получает текст → `ValueError: Not a MOJO stream`). Берём бинарник из релиза 3.7.0:

```bash
sudo apt remove -y austin
cd /tmp
wget https://github.com/P403n1x87/austin/releases/download/v3.7.0/austin-3.7.0-gnu-linux-amd64.tar.xz
tar -xf austin-3.7.0-gnu-linux-amd64.tar.xz
sudo mv austin /usr/local/bin/austin
austin --version   # 3.7.0
```

Снять защиту ptrace для attach к чужому PID (до перезагрузки):

```bash
sudo sysctl kernel.yama.ptrace_scope=0
```

`austin-tui` не завёлся (версионный конфликт формата). Работаем напрямую через `austin -o file` — для документации даже удобнее, сразу получаем текстовый collapsed-формат.

### Находим воркер (не мастер!)

```bash
ps auxf | grep uvicorn                 # найти PID мастера
pgrep -P <MASTER_PID> -a               # дети мастера
```

Воркеры: `spawn_main ... --multiprocessing-fork` (5 штук при `--workers 5`). Плюс один `resource_tracker` — служебный, не трогаем.

### Анализ collapsed-файла

Формат: каждая строка — путь вызова через `;`, в конце число μs этого сэмпла.

```
P263578;T0:9;...;asyncio/runners.py:Runner.run:118 10569
```

Топ leaf-функций (фильтр `/^[^#]/` отбрасывает строки метаданных типа `# duration:`):

```bash
awk -F';' '/^[^#]/ {
  n = split($NF, a, " ")
  t = a[n]
  leaf = a[1]; for (i=2; i<n; i++) leaf = leaf " " a[i]
  totals[leaf] += t
} END { for (f in totals) printf "%12d μs  %s\n", totals[f], f }' \
/tmp/profile.austin | sort -rn | head -15
```

### Мои запуски

> Важный момент про воркеры
Профилируем один воркер из пяти. Значит, в топе увидим то, что делает конкретно он (обработку части запросов), а не картину «мастер ждёт воркеров», как было с py-spy. Это наша настоящая цель.

```sh
sudo austin -i 10000 -t 60000 -o /tmp/profile.austin --pid 263578
# -i 10000 = сэмпл каждые 10 мс
# -t 60000 = работать 60 секунд и выйти
```

Wall-clock топ — теперь всё честно
```
μs	        функция	                                смысл
146 963 022	Connection._recv:395	                  pong-thread весь прогон ждал ping мастера
90 183 424	Runner.run:118	asyncio                 event loop в epoll_wait
6 450 289	  StreamHandler.flush:1144	              логи — flush stdout/stderr
1 594 055	  ipaddress.ip_address:54	                парсинг IP-адреса клиента (access-log?)
1 415 494	  socket.detach:515	
1 215 540	  starlette/_exception_handler	          обработка запроса (top-frame Starlette)
1 113 246	  uvicorn httptools.on_response_complete	завершение ответа
1 032 921	  pydantic.BaseModel.__init__:263	        создание моделей
915 288	    logging._acquireLock:240	              лок логгера
```
Даже в wall-clock первые две строки — это ожидания (pong и asyncio), а после них уже появляются настоящие горячие места:
- Логирование (~7.4s суммарно): StreamHandler.flush + _acquireLock. Это подозрительно — в недавнем коммите ты уже drop hot-path logger, но на воркере всё ещё 6.4 сек во flush. Это, скорее всего, uvicorn access log. Если его выключить — можно получить сразу заметный выигрыш.
- pydantic.BaseModel.init (~1s) — создание моделей на каждый запрос.
- ipaddress.ip_address (~1.6s) — тоже вероятно access-log, X-Forwarded-For парсит.

### CPU-mode прогон

Повторили тот же сценарий с флагом `-C` — Austin считает только время, когда поток реально на CPU:

```bash
sudo austin -C -i 10000 -t 60000 -o /tmp/profile.austin.cpu --pid <WORKER_PID>
```

Топ CPU-mode:

| μs | функция |
|---|---|
| 26 829 410 | `multiprocessing/connection.py:Connection._recv:395` |
| 26 797 641 | `asyncio/runners.py:Runner.run:118` |
| 5 420 184 | `threading.py:Condition.wait:359` |
| 5 318 475 | `multiprocessing/resource_tracker.py:main:251` |
| < 11 ms | всё остальное — pydantic, orjson, starlette **отсутствуют** |

В wall-clock мы видели 6.4s в `StreamHandler.flush`, 1s в pydantic, 1.6s в ipaddress. В CPU-mode их нет. Это главный урок этого прогона — объяснение ниже в выводах.

### Сравнение прогонов и overhead самого Austin

| Конфиг | RPS | VUS (факт) | p(95) | errors |
|---|---|---|---|---|
| py-spy на мастере (baseline) | 1683–1991 | 231–547 | 1.85–2.55s | 0.24–0.50% |
| austin wall-clock на воркере | 1232 | 355–2500 | 5.18s | 0.23% |
| austin CPU-mode на воркере | **1720** | 1906–2500 | 2.15s | 0.03% |

Wall-clock режим просаживает RPS на ~30%. CPU-mode возвращает производительность к baseline. На проде — только `-C`.

### Выводы

1. **Python-сэмплер не видит native-код.** Austin раскручивает только Python-стек. Под `Runner.run:118` внутри asyncio — нативный `epoll_wait` в C, на экране это один Python-кадр. То же для pydantic v2 (Rust-ядро), orjson (C), httptools (C), clickhouse-driver (частично C).
2. **Wall-clock mode ≠ где горит CPU.** В топе доминируют ожидания (pong-recv, epoll_wait). Смотреть надо **ниже** первых 2 строк — там реальные горячие Python-места, но с оговоркой из п.1: время native-кода приписывается ближайшему Python-родителю.
3. **Логирование — заметная статья расходов.** `StreamHandler.flush` 6.4 с + `_acquireLock` 0.9 с за минуту на один воркер — кандидаты на отключение uvicorn access log или переход на асинхронный handler.
4. **CPU-mode вытягивает только Python-CPU.** На стеке с нативными расширениями (pydantic-core Rust, orjson C) CPU-mode даёт почти пустой топ. Это НЕ значит, что приложение простаивает — это значит, что узкое место **в C/Rust**, куда Python-сэмплерам хода нет. Чтобы заглянуть туда, нужен сэмплер с native-stacks (py-spy `--native`, perf, Scalene).
5. **Austin сам добавляет overhead.** Wall-clock на воркере уронил RPS с ~1700 до 1232. На проде — только `-C`.
6. **Картина с py-spy согласуется.** py-spy на мастере видел `threading.wait` (координация), Austin на воркере видит `Runner.run` + `Connection._recv` (asyncio + pong-thread). Оба сэмплера рисуют одно и то же: воркер большую часть wall-времени **ждёт**.

### Следующий шаг

1. Проверить гипотезу про логирование: отключить uvicorn access log (`--access-log=False`) → прогон k6 без профайлера → сравнить RPS.
2. Попробовать **py-spy с `--native`** или **Scalene** — они умеют заглянуть в C-расширения и закроют слепую зону CPU-mode Austin.

---

## Scalene: практика (попытка)

### Что пробовали

Scalene позиционирует себя как профайлер, показывающий Python vs native vs system time, плюс память. Хотелось закрыть слепую зону Austin CPU-mode (время в C/Rust расширениях).

В отличие от py-spy и Austin, Scalene **не умеет attach к уже запущенному процессу**: только launch-time. Поэтому запускали внутри api-контейнера через `docker compose run`, обернув uvicorn в тонкий launcher-скрипт:

```bash
docker compose stop api
docker rm -f api_profile 2>/dev/null

docker compose run --service-ports --name api_profile api sh -c '
  pip install -q "scalene<2" &&
  cat > /tmp/run_uvicorn.py <<PYEOF
import uvicorn
config = uvicorn.Config("app.main:app", host="0.0.0.0", port=8000)
uvicorn.Server(config).run()
PYEOF
  scalene --cli --profile-all \
          --profile-only "/code,starlette,fastapi,uvicorn,pydantic,orjson" \
          --outfile /tmp/scalene.txt /tmp/run_uvicorn.py
'
```

### На какие грабли наступили

1. **Scalene 2.2.1 vs 1.5.x — разный CLI.** В свежей версии `run`/`view` как подкоманды, `run` поддерживает всего 4 флага и не принимает `-m module`. Пришлось пинить `pip install "scalene<2"`.
2. **Нет `-m module` — нужен wrapper-скрипт.** Scalene 1.x тоже принимает только файл. Написали двухстрочную обёртку `run_uvicorn.py`.
3. **`uvicorn.run(..., workers=1)` запускает supervisor + форкает ребёнка.** Scalene профилирует supervisor, который ничего не делает. Пришлось переписать обёртку на явный `Config + Server().run()` — in-process, без supervisor.
4. **Default `profile-all` не включён.** Без него Scalene видит только сам target-файл. При 2-строчном wrapper-е отчёт получается почти пустой.
5. **SIGINT не гарантирует запись отчёта.** Контейнер выходил с кодом 130 (SIGINT), `/tmp/scalene.txt` в нём не создавался. Пробовали `--profile-interval 20` и bind-mount на хост — итогом так и не получили отчёт с реальным наполнением.
6. **Overhead катастрофический на async-стеке.** Даже в тех прогонах, где отчёт записался:
   | Конфиг | RPS | p(95) | errors |
   |---|---|---|---|
   | py-spy на мастере (baseline) | 1683–1991 | 1.85–2.55s | 0.24–0.50% |
   | Scalene workers=1 (first try) | 414 | 58.58s | 8.50% |
   | Scalene in-process (Server.run) | 626 | 4.43s | 2.03% |

### Что получилось в отчётах

Все полученные файлы (22 строки) содержали только:
- сам wrapper `/tmp/run_uvicorn.py` с `64% Python / 7% native / 28% system` на строке `uvicorn.Server(config).run()`
- случайно зацепленный `/code/clickhouse_app/client.py` с нулевым CPU

Ни starlette, ни fastapi, ни pydantic в отчёты не попали, несмотря на `--profile-all` и `--profile-only`.

### Почему свернули

Соотношение «потраченное время / полученная информация» ушло в минус. Scalene построен под CPU-bound синхронные скрипты; на FastAPI/asyncio в контейнере он требует слишком много подгонки (wrapper, env, сигнал-хэндлинг, bind-mount, версия), и даже при всём этом таргетная информация (Python vs native разбивка по pydantic/orjson) не вытягивается надёжно. Для этой задачи корректнее **py-spy --native** или **perf**, которые видят C-стеки напрямую.

### Выводы

1. **Scalene плохо дружит с async-сервером в контейнере.** Для скрипт-подобных CPU-нагрузок — ок, для FastAPI/uvicorn — слишком хрупко.
2. **`uvicorn.run(workers=N)` всегда поднимает supervisor,** даже при N=1. Для in-process запуска под профайлером нужен явный `Server(config).run()`.
3. **Default Scalene профилирует только target-файл.** Для реального приложения обязательно `--profile-all`, иначе отчёт пустой.
4. **Сигнал-хэндлинг Scalene + uvicorn + docker** — зона риска. `--profile-interval` + bind-mount на хост надёжнее, чем надеяться на чистый shutdown.

---

## Итог обучения

Освоили **py-spy** и **Austin** (оба sampling, низкий overhead). Этого достаточно, чтобы увидеть картину Python-слоя на FastAPI. Для заглядывания в C/Rust расширения — оставляем на будущее: `py-spy record --native` или `perf` на хосте.

**cProfile**, **Pyinstrument**, **Pyroscope** не трогали в этом раунде — они требуют либо правки кода (middleware), либо отдельной инфраструктуры (сайдкар-сервер). Секции с теорией и заготовками оставлены для ориентации.