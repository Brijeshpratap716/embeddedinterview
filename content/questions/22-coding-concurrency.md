---
slug: coding-concurrency
title: "Coding: Concurrency Primitives"
icon: 🔒
level: Advanced
order: 22
desc: Build synchronisation primitives in C: atomic increment, spinlock, mutex with compare-and-swap, semaphore from mutex + condition variable, reader-writer lock, reference counting, once-only initialisation and timed waits.
---
Senior embedded, kernel and systems interviews often ask you to implement a synchronisation primitive from lower-level ones. The interviewer checks the memory ordering, what happens under contention, and the corner cases (spurious wake-ups, overflow, freeing objects while in use). Answers use C11 `<stdatomic.h>` and POSIX threads; the same ideas map to kernel and RTOS APIs.

### Implement an atomic increment. {E}
**Short answer:** Use an atomic read-modify-write so that the load, add and store happen as one indivisible operation: C11 `atomic_fetch_add(&count, 1)` (or `__atomic_fetch_add` with GCC). On Cortex-M3 and above it compiles to an `LDREX`/`ADD`/`STREX` loop that retries if another context touched the variable; on Cortex-M0, which lacks exclusives, use a short critical section that disables interrupts around `count++`.

```c
#include <stdatomic.h>
#include <stdint.h>

static _Atomic uint32_t counter;

uint32_t atomic_inc(void)
{
    return atomic_fetch_add_explicit(&counter, 1u, memory_order_relaxed) + 1u;   /* returns new value */
}

/* the same thing with an explicit compare-and-swap loop */
uint32_t atomic_inc_cas(_Atomic uint32_t *p)
{
    uint32_t old = atomic_load_explicit(p, memory_order_relaxed);
    while (!atomic_compare_exchange_weak_explicit(p, &old, old + 1u,
                                                  memory_order_relaxed, memory_order_relaxed)) {
        /* old now holds the current value; retry */
    }
    return old + 1u;
}
```

**Points:** `count++` on a plain or `volatile` variable is load–add–store and loses updates under concurrency. Atomic RMW operations may compile to `LDREX`/`STREX` retry loops on supporting Cortex-M/AArch32 targets, or `LDXR`/`STXR` loops in AArch64, or to a single `LDADD` with Armv8.1 LSE atomics. Relaxed ordering is enough for a pure statistics counter; use acquire/release when the counter also signals that other data is ready. On Cortex-M0 (no exclusives), a toolchain may use library routines or platform-specific interrupt masking; verify its implementation.

**Why `count++` is not atomic (even with `volatile`)**

```
Thread A: load 5          Thread B: load 5
Thread A: add → 6         Thread B: add → 6
Thread A: store 6         Thread B: store 6     → two increments, value went up by 1
```

`volatile` only forces the compiler to perform the memory accesses; it does not make the three steps indivisible.

**A CAS-loop version (shows the principle)**

```c
#include <stdatomic.h>

int atomic_inc_cas(atomic_int *p)
{
    int old = atomic_load_explicit(p, memory_order_relaxed);
    while (!atomic_compare_exchange_weak_explicit(p, &old, old + 1,
                                                  memory_order_relaxed, memory_order_relaxed)) {
        /* old now holds the current value: retry with it */
    }
    return old + 1;
}
```

**Memory ordering choices**

| Use | Ordering |
|---|---|
| Statistics counter, nobody depends on other data | `memory_order_relaxed` |
| Counter used as a "data ready" sequence number | release on increment, acquire on read |
| Reference counting | relaxed increment, release decrement + acquire fence before free |

**Platform notes:** x86 uses `lock xadd`; Armv8.1-A has a single `LDADD` instruction (LSE atomics); in the Linux kernel use `atomic_inc()` / `atomic_inc_return()`; in FreeRTOS on a single core, `taskENTER_CRITICAL()` around `count++` is the portable choice.

#### What the compare-and-swap loop actually does

Assume count=10. Thread A and B both load 10. A successfully changes 10 to 11. B's compare-and-swap fails and replaces expected with 11; B retries and stores 12. Neither update is lost. A weak compare-and-swap may also fail spuriously, so it belongs inside a retry loop. The unsigned counter wraps modulo its width; if wrap is unacceptable, implement a checked or saturating increment.

On Arm, the compiler may use an exclusive load/store loop or an LSE instruction, depending on the target and toolchain. AArch64 uses LDXR/STXR or their ordering variants, not the AArch32 LDREX/STREX mnemonics. C11 does not guarantee that every atomic type is lock-free; confirm target support before ISR use. Interrupt masking is only a single-core fallback.

### Implement a spinlock. {M}
**Short answer:** A spinlock is a single atomic flag: `lock` repeatedly tries to change it from 0 to 1 with an atomic exchange or compare-and-swap (with **acquire** ordering) and spins until it succeeds; `unlock` stores 0 with **release** ordering. It never sleeps, so it is only suitable for very short critical sections, typically between CPU cores or in interrupt context where sleeping is impossible.

```c
#include <stdatomic.h>

typedef struct { atomic_flag locked; } spinlock_t;
#define SPINLOCK_INIT { ATOMIC_FLAG_INIT }

static inline void spin_lock(spinlock_t *l)
{
    while (atomic_flag_test_and_set_explicit(&l->locked, memory_order_acquire)) {
        /* spin; add a CPU hint here: __asm__ volatile("yield") on Arm, or WFE with SEV on unlock */
    }
}

static inline void spin_unlock(spinlock_t *l)
{
    atomic_flag_clear_explicit(&l->locked, memory_order_release);
}
```

**Points:** **acquire** on lock and **release** on unlock keep the critical section's memory accesses inside it. Spin only for very short sections and only when the holder runs on another core; on a single core with pre-emption, the waiter just burns its time slice (kernels disable pre-emption while holding a spinlock, and use `spin_lock_irqsave` when an ISR can take the same lock). Improvements: test-and-test-and-set (spin on a plain load to reduce cache traffic), exponential back-off, ticket locks for fairness.

**Why acquire and release:** acquire on lock stops reads/writes inside the critical section from moving before the lock is taken; release on unlock makes all writes inside it visible to the next CPU that acquires the lock.

**Test-and-test-and-set (better under contention)**

```c
while (atomic_exchange_explicit(&l->locked, 1, memory_order_acquire)) {
    while (atomic_load_explicit(&l->locked, memory_order_relaxed))
        ;                     /* spin on a plain read: no cache-line ping-pong */
}
```

Waiting with plain loads keeps the cache line shared among waiters; only when it looks free do they attempt the expensive exclusive exchange.

**Improvements used in real systems**

| Technique | Benefit |
|---|---|
| `WFE`/`SEV` (Arm), `PAUSE` (x86) in the spin loop | lower power, less bus traffic |
| Ticket lock (take a number, wait for your turn) | fairness: FIFO order, no starvation |
| MCS / qspinlock (Linux) | each waiter spins on its own cache line; scales to many cores |
| Disable pre-emption while held | holder cannot be scheduled out while others spin |
| `spin_lock_irqsave` | safe when an ISR on the same CPU can take the lock |

**When not to use one:** on a single-core MCU a spinlock between a task and an ISR deadlocks (the ISR spins forever while the task it interrupted holds the lock) — disable interrupts instead. Between tasks on one core, use a mutex.

### Implement a mutex using atomic compare-and-swap. {M}
**Short answer:** Represent the mutex as an atomic integer (0 = unlocked, 1 = locked). `lock` uses compare-and-swap to change 0 to 1; if it fails, someone else holds the mutex, so the thread yields or sleeps and tries again. `unlock` stores 0 with release ordering. A production mutex adds a sleeping wait queue (futex), ownership tracking and, for real-time systems, priority inheritance.

```c
#include <stdatomic.h>
#include <sched.h>

typedef struct { atomic_int state; } cas_mutex_t;   /* 0 = unlocked, 1 = locked */
#define CAS_MUTEX_INIT { 0 }

void cas_mutex_lock(cas_mutex_t *m)
{
    int expected = 0;
    while (!atomic_compare_exchange_weak_explicit(&m->state, &expected, 1,
                                                  memory_order_acquire, memory_order_relaxed)) {
        expected = 0;          /* CAS wrote the current value into expected: reset and retry */
        sched_yield();         /* give the CPU away instead of spinning hard */
    }
}

int cas_mutex_trylock(cas_mutex_t *m)
{
    int expected = 0;
    return atomic_compare_exchange_strong_explicit(&m->state, &expected, 1,
                                                   memory_order_acquire, memory_order_relaxed);
}

void cas_mutex_unlock(cas_mutex_t *m)
{
    atomic_store_explicit(&m->state, 0, memory_order_release);
}
```

**Points:** CAS changes 0 → 1 only if the value is still 0, so exactly one thread wins; reset `expected` after a failed CAS. A real mutex **sleeps** instead of yielding in a loop: Linux uses a futex (state 0 = free, 1 = locked, 2 = locked with waiters; `futex_wait`/`futex_wake` only when contended), and RTOS mutexes put the task on a wait list. Real mutexes also record the owner (for priority inheritance and error checking). `weak` CAS may fail spuriously and belongs in loops; `strong` for single attempts.

**How CAS gives mutual exclusion:** `compare_exchange(&m, &expected=0, 1)` succeeds only for the one thread that sees 0 at the moment of the atomic operation; all others see 1 and fail. After a failure, `expected` holds the current value, so it must be reset to 0 before retrying — a classic bug.

**Futex-style three-state mutex (how Linux glibc does it)**

| State | Meaning |
|---|---|
| 0 | unlocked |
| 1 | locked, no waiters |
| 2 | locked, there may be waiters |

- Lock fast path: CAS 0 → 1 (no system call).
- Contended: set the state to 2 and call `futex_wait(&m, 2)` to sleep in the kernel.
- Unlock: atomically exchange with 0; if the old value was 2, call `futex_wake(&m, 1)`.

Uncontended lock/unlock never enter the kernel, which is why pthread mutexes are cheap.

**Spinlock vs mutex**

| | Spinlock | Mutex |
|---|---|---|
| Waiting | burns CPU | sleeps |
| Usable in ISR | yes | no |
| Owner tracking | no | yes (only the owner may unlock; recursive variants) |
| Priority inheritance | no | possible |
| Best for | very short sections, multi-core | longer sections, may block |

**Hybrid:** adaptive mutexes spin briefly (the owner is running on another core and will release soon) before sleeping.

### Implement a counting semaphore using a mutex and a condition variable. {M}
**Short answer:** Keep an integer count protected by a mutex. `wait` (P/take) locks the mutex, waits on the condition variable in a `while (count == 0)` loop, then decrements the count and unlocks. `post` (V/give) locks the mutex, increments the count, signals the condition variable and unlocks. The count represents available resources or pending events.

```c
#include <pthread.h>

typedef struct {
    pthread_mutex_t m;
    pthread_cond_t  cv;
    unsigned count;
} csem_t;

void csem_init(csem_t *s, unsigned initial)
{
    pthread_mutex_init(&s->m, NULL);
    pthread_cond_init(&s->cv, NULL);
    s->count = initial;
}

void csem_wait(csem_t *s)                 /* P / down */
{
    pthread_mutex_lock(&s->m);
    while (s->count == 0)                 /* while, not if: spurious wake-ups */
        pthread_cond_wait(&s->cv, &s->m);
    s->count--;
    pthread_mutex_unlock(&s->m);
}

void csem_post(csem_t *s)                 /* V / up */
{
    pthread_mutex_lock(&s->m);
    s->count++;
    pthread_cond_signal(&s->cv);          /* wake one waiter */
    pthread_mutex_unlock(&s->m);
}
```

**Points:** the mutex protects the count; the condition variable lets waiters sleep until the count is positive; the `while` loop handles spurious wake-ups and other threads taking the unit first. Unlike POSIX `sem_post`, this version is not async-signal-safe (it locks a mutex), so it cannot be posted from a signal handler or ISR.

**Dry run (count starts at 2: two identical DMA channels)**

| action | count | result |
|---|---|---|
| T1 wait | 1 | gets channel |
| T2 wait | 0 | gets channel |
| T3 wait | 0 | blocks |
| T1 post | 1 → T3 woken → 0 | T3 gets channel |

**Why the `while` loop:** the condition variable can wake spuriously, and with several waiters another thread can take the unit before this one re-acquires the mutex.

**Semaphore vs mutex**

| | Semaphore | Mutex |
|---|---|---|
| Value | 0..N count | locked/unlocked |
| Owner | none: any thread can post | the locking thread must unlock |
| Typical use | count resources, signal events | protect a critical section |
| Priority inheritance | no | yes (in RTOSes and PI mutexes) |

**Extensions:** `try_wait` (return immediately if the count is 0), `timed_wait` with an absolute deadline, and a maximum count (FreeRTOS counting semaphores have one).

**Real APIs:** POSIX `sem_init/sem_wait/sem_post` (`sem_post` is async-signal-safe, unlike this version), FreeRTOS `xSemaphoreCreateCounting`, Zephyr `k_sem`, Linux kernel `struct semaphore` (mostly replaced by mutexes and completions).

### Implement a reader-writer lock. {H}
**Short answer:** Track the number of active readers, whether a writer is active, and (for writer preference) the number of waiting writers, all protected by one mutex with two condition variables. A reader may enter when no writer is active or waiting; a writer may enter only when there are no readers and no active writer. Leaving readers wake a writer when the count reaches zero; a leaving writer wakes everyone.

```c
#include <pthread.h>

typedef struct {
    pthread_mutex_t m;
    pthread_cond_t  readers_ok, writer_ok;
    int readers;            /* active readers */
    int writer;             /* 1 if a writer holds the lock */
    int waiting_writers;    /* writer preference: block new readers while writers wait */
} rwlock_t;

void rw_init(rwlock_t *l)
{
    pthread_mutex_init(&l->m, NULL);
    pthread_cond_init(&l->readers_ok, NULL);
    pthread_cond_init(&l->writer_ok, NULL);
    l->readers = l->writer = l->waiting_writers = 0;
}

void rw_read_lock(rwlock_t *l)
{
    pthread_mutex_lock(&l->m);
    while (l->writer || l->waiting_writers > 0)
        pthread_cond_wait(&l->readers_ok, &l->m);
    l->readers++;
    pthread_mutex_unlock(&l->m);
}

void rw_read_unlock(rwlock_t *l)
{
    pthread_mutex_lock(&l->m);
    if (--l->readers == 0) pthread_cond_signal(&l->writer_ok);
    pthread_mutex_unlock(&l->m);
}

void rw_write_lock(rwlock_t *l)
{
    pthread_mutex_lock(&l->m);
    l->waiting_writers++;
    while (l->writer || l->readers > 0)
        pthread_cond_wait(&l->writer_ok, &l->m);
    l->waiting_writers--;
    l->writer = 1;
    pthread_mutex_unlock(&l->m);
}

void rw_write_unlock(rwlock_t *l)
{
    pthread_mutex_lock(&l->m);
    l->writer = 0;
    if (l->waiting_writers) pthread_cond_signal(&l->writer_ok);
    else pthread_cond_broadcast(&l->readers_ok);          /* let all waiting readers in */
    pthread_mutex_unlock(&l->m);
}
```

**Points:** many readers may hold the lock together, a writer needs exclusive access. Choose a policy: **reader preference** can starve writers; **writer preference** (as here) can starve readers under constant writes; fair (FIFO) versions avoid both. Use rwlocks only for read-mostly data with non-trivial read sections; for tiny sections a plain mutex is often faster. Kernel alternatives for read-mostly data: seqlocks and RCU. POSIX provides `pthread_rwlock_t`.

**Rules (writer-preference version)**

| Operation | Waits while | On exit |
|---|---|---|
| `read_lock` | `writer_active || writers_waiting > 0` | — |
| `read_unlock` | — | `readers--`; if 0, signal a writer |
| `write_lock` | `writer_active || readers > 0` (counted in `writers_waiting`) | — |
| `write_unlock` | — | `writer_active = false`; broadcast to readers and writers |

**Dry run:** R1 and R2 read together (readers = 2). W1 arrives → waits (`writers_waiting = 1`). R3 arrives → waits because a writer is waiting (prevents writer starvation). R1, R2 leave → readers = 0 → W1 runs. W1 leaves → broadcast → R3 runs.

**Policies**

- **Reader preference:** maximises read throughput, but a constant stream of readers starves writers.
- **Writer preference:** writers get in quickly; readers can starve under constant writes.
- **Fair (phase-fair / FIFO):** alternates, bounded waiting for both.

**When it pays off:** read sections that are long relative to the locking overhead, and data that is read far more often than written (configuration tables, routing tables). For short sections a plain mutex is often faster, because the rwlock's internal counters cause cache-line contention.

**Alternatives:** seqlocks (writers never wait for readers, readers retry), RCU (readers take no lock at all; writers publish new copies), POSIX `pthread_rwlock_t`, Linux `rw_semaphore`.

### Implement a reference counter for a shared object. {M}
**Short answer:** Store an atomic count in the object. Each new owner calls `get` (atomic increment). Each owner calls `put` when done (atomic decrement); the caller that brings the count to zero frees the object. Use relaxed ordering for the increment, release ordering for the decrement, and an acquire fence before freeing so the freeing thread sees all other owners' writes.

```c
#include <stdatomic.h>
#include <stdlib.h>

typedef struct buffer {
    atomic_uint refs;
    size_t len;
    unsigned char data[];
} buffer_t;

buffer_t *buf_new(size_t len)
{
    buffer_t *b = malloc(sizeof *b + len);
    if (b) { atomic_init(&b->refs, 1u); b->len = len; }     /* creator holds one reference */
    return b;
}

buffer_t *buf_get(buffer_t *b)                               /* take an extra reference */
{
    atomic_fetch_add_explicit(&b->refs, 1u, memory_order_relaxed);
    return b;
}

void buf_put(buffer_t *b)                                    /* drop a reference */
{
    if (atomic_fetch_sub_explicit(&b->refs, 1u, memory_order_release) == 1u) {
        atomic_thread_fence(memory_order_acquire);           /* see all writes made before other puts */
        free(b);                                             /* last reference: destroy */
    }
}
```

**Points:** increment can be relaxed (you already hold a reference, so the object cannot disappear); the decrement uses release, and the thread that drops the last reference uses an acquire fence before freeing, so it sees every other thread's writes. Guard against overflow in long-running systems (the Linux kernel's `refcount_t` saturates instead of wrapping, which turns use-after-free bugs into leaks). You may only `get` a reference from an object you already hold a reference to; looking an object up in a shared table and taking a reference needs the table's lock (or `refcount_inc_not_zero` with RCU).

**Lifecycle example**

| event | count |
|---|---|
| create (creator holds a reference) | 1 |
| pass to a worker thread: `get` | 2 |
| creator done: `put` | 1 |
| worker done: `put` → reaches 0 → free | 0 |

**Why the memory ordering matters:** thread A writes into the object, then calls `put` (release). Thread B's `put` brings the count to 0; its acquire fence guarantees A's writes are visible before B runs the destructor — otherwise the destructor could see stale data or the freeing could be reordered before A's last writes.

**Rules that prevent use-after-free**

- Only call `get` on an object you already hold a reference to (or that is protected by a lock while you look it up). Getting a reference to an object found in a shared table requires the lookup and the increment to happen under the table's lock, or using `refcount_inc_not_zero()` so a dying object is not revived.
- Every `get` must have exactly one matching `put` on every path, including error paths.

**Overflow/underflow protection:** Linux `refcount_t` saturates at a maximum and warns on underflow instead of wrapping, turning many use-after-free bugs into memory leaks (much less dangerous).

**Where it is used:** Linux `kref`, `struct device` and file references, C++ `std::shared_ptr`, COM `AddRef/Release`, network buffers shared between protocol layers, DMA buffers shared between drivers (dma-buf).

### Implement once-only initialisation. {M}
**Short answer:** Use a state variable with three values — not started, in progress, done. The first thread to change 'not started' to 'in progress' with compare-and-swap runs the initialiser and then stores 'done' with release ordering. Other threads either see 'done' (acquire load, fast path) or wait until it becomes done. Everyone returns only after initialisation has **finished**.

```c
#include <pthread.h>
#include <stdatomic.h>

/* 1. POSIX */
static pthread_once_t once = PTHREAD_ONCE_INIT;
static void init_tables(void) { /* expensive one-time setup */ }
void use_tables(void) { pthread_once(&once, init_tables); /* ... */ }

/* 2. Hand-rolled with atomics: 0 = not started, 1 = running, 2 = done */
static atomic_int init_state;

void call_once_manual(void (*fn)(void))
{
    if (atomic_load_explicit(&init_state, memory_order_acquire) == 2) return;   /* fast path */
    int expected = 0;
    if (atomic_compare_exchange_strong_explicit(&init_state, &expected, 1,
                                                memory_order_acquire, memory_order_acquire)) {
        fn();                                                                  /* we won: initialise */
        atomic_store_explicit(&init_state, 2, memory_order_release);
    } else {
        while (atomic_load_explicit(&init_state, memory_order_acquire) != 2) { /* wait for the winner */ }
    }
}
```

**Points:** exactly one thread runs the initialiser and everyone else waits until it has **finished** (not just started); the release store publishes the initialised data, and the acquire load on the fast path makes it visible. Plain "check a flag, then init" is a race (double-checked locking without atomics is broken). Also available: C11 `call_once`, C++ static local initialisation (thread-safe since C++11), Linux `DO_ONCE`. On a bare-metal MCU, do one-time setup before enabling interrupts and starting tasks instead.

**Why the naive version is broken**

```c
if (!initialised) {      /* two threads can both see false */
    init();              /* init runs twice */
    initialised = true;  /* another thread may see true before init's writes are visible */
}
```

Two problems: double initialisation, and a thread seeing the flag set before the initialised data is visible (reordering). The CAS fixes the first; release/acquire fixes the second.

**States and transitions**

| state | meaning | other threads |
|---|---|---|
| 0 | not started | try CAS 0 → 1 |
| 1 | running | wait (spin with yield, or block on a futex/condition variable) |
| 2 | done | fast path: return immediately |

**Error handling:** if the initialiser can fail, go back to state 0 (so another call retries) or store a failed state and return the error to every caller.

**Standard facilities**

- C11 `call_once(&flag, fn)` with `ONCE_FLAG_INIT`; POSIX `pthread_once`.
- C++11 function-local `static` objects are initialised thread-safely ("magic statics").
- Linux kernel: `DO_ONCE()`, `static_key`-based helpers.
- Bare-metal single-core firmware: simply initialise everything in `main()` before enabling interrupts and starting the scheduler — no once-logic needed.

### Implement a wait with a timeout (condition variable). {M}
**Short answer:** Compute an absolute deadline once (current time on `CLOCK_MONOTONIC` plus the timeout), then lock the mutex and call `pthread_cond_timedwait` in a loop while the condition is false. If it returns `ETIMEDOUT`, check the condition one last time and return a timeout error if it is still false. Because the deadline is absolute, spurious wake-ups do not extend the total waiting time.

```c
#include <errno.h>
#include <pthread.h>
#include <stdbool.h>
#include <time.h>

static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  cv;
static bool data_ready;

void init_cv(void)
{
    pthread_condattr_t a;
    pthread_condattr_init(&a);
    pthread_condattr_setclock(&a, CLOCK_MONOTONIC);     /* immune to wall-clock changes */
    pthread_cond_init(&cv, &a);
}

/* returns true if data became ready, false on timeout */
bool wait_ready(unsigned timeout_ms)
{
    struct timespec deadline;
    clock_gettime(CLOCK_MONOTONIC, &deadline);
    deadline.tv_sec  += timeout_ms / 1000;
    deadline.tv_nsec += (long)(timeout_ms % 1000) * 1000000L;
    if (deadline.tv_nsec >= 1000000000L) { deadline.tv_sec++; deadline.tv_nsec -= 1000000000L; }

    pthread_mutex_lock(&m);
    int rc = 0;
    while (!data_ready && rc != ETIMEDOUT)
        rc = pthread_cond_timedwait(&cv, &m, &deadline);   /* absolute deadline: loop-safe */
    bool ok = data_ready;
    pthread_mutex_unlock(&m);
    return ok;
}
```

**Points:** use an **absolute** deadline computed once, so spurious wake-ups and retries do not extend the total wait; use `CLOCK_MONOTONIC` so NTP or user time changes do not break the timeout; normalise `tv_nsec`; after a timeout, still check the predicate (the event may have happened just at the deadline). RTOS equivalents take a timeout in ticks (`xSemaphoreTake(sem, pdMS_TO_TICKS(100))`, `k_sem_take(&s, K_MSEC(100))`); in bare-metal code, compare against a tick counter. Every wait in production code should have a timeout and a defined recovery.

**Building the deadline correctly**

```c
#include <time.h>

struct timespec deadline_after_ms(long ms)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    t.tv_sec  += ms / 1000;
    t.tv_nsec += (ms % 1000) * 1000000L;
    if (t.tv_nsec >= 1000000000L) { t.tv_sec++; t.tv_nsec -= 1000000000L; }   /* normalise */
    return t;
}
```

The condition variable must be created with `pthread_condattr_setclock(&attr, CLOCK_MONOTONIC)`; otherwise the default `CLOCK_REALTIME` is used, and an NTP correction or a user changing the clock could make the wait far shorter or longer.

**Why a relative timeout per loop iteration is wrong:** each spurious wake-up would restart the full timeout, so the total wait could become unbounded.

**Return value contract:** return success if the condition became true (even if that happened exactly at the deadline), a timeout error otherwise. The caller always gets the mutex back, held, so it can inspect the shared state.

**Equivalents elsewhere**

| Environment | Call |
|---|---|
| FreeRTOS | `xSemaphoreTake(sem, pdMS_TO_TICKS(100))`, `xQueueReceive(q, &m, ticks)` |
| Zephyr | `k_sem_take(&sem, K_MSEC(100))` |
| Linux kernel | `wait_event_timeout(wq, cond, msecs_to_jiffies(100))`, `wait_for_completion_timeout()` |
| C++ | `cv.wait_until(lock, deadline, predicate)` |
| Bare metal | poll the flag and a hardware counter with a wrap-safe deadline check |

**Design rule:** every wait for hardware or another component should have a timeout and a defined recovery action, so one failure cannot hang the whole system.

### How do you publish data safely between two threads using C11 atomics? {M}
**Short answer:** Publish a ready flag with release semantics after writing data. A reader that observes the publication using an acquire load can then safely access the published data.

```c
#include <stdatomic.h>
static int data;
static atomic_int ready = 0;

void producer(void)
{
    data = 100;
    atomic_store_explicit(&ready, 1, memory_order_release);
}
int consumer(void)
{
    if (atomic_load_explicit(&ready, memory_order_acquire))
        return data;
    return -1;
}
```

```text
Producer                    Consumer
data = 100                  load ready (acquire)
store ready (release) ---> if ready == 1: read data
```

**Why:** If the acquire load reads the release store, the producer's preceding write happens-before the consumer's read.

**Limitation:** This is one-time publication. Reusing the buffer concurrently requires a separate ownership protocol or lock. Volatile alone is not sufficient.

**Interview takeaway:** Acquire/release creates a synchronization relationship without requiring sequential consistency for every operation.
