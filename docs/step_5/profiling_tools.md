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
