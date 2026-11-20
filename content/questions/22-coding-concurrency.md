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

**Points:** `count++` on a plain or `volatile` variable is load–add–store and loses updates under concurrency. Atomic RMW operations compile to `LDREX`/`STREX` retry loops on Cortex-M3+ and Armv8.0-A, or to a single `LDADD` with Armv8.1 LSE atomics. Relaxed ordering is enough for a pure statistics counter; use acquire/release when the counter also signals that other data is ready. On Cortex-M0 (no exclusives) atomics are implemented by briefly disabling interrupts.

### Implement a spinlock. {M}
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

### Implement a mutex using atomic compare-and-swap. {M}
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

### Implement a counting semaphore using a mutex and a condition variable. {M}
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

### Implement a reader-writer lock. {H}
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

### Implement a reference counter for a shared object. {M}
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

### Implement once-only initialisation. {M}
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

### Implement a wait with a timeout (condition variable). {M}
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
