---
slug: data-structures
title: Data Structures & Algorithms
icon: 🧮
level: Intermediate
order: 12
desc: Complexity, linked lists, ring buffers, stacks, queues, heaps and priority queues, hashing, trees, graphs, sorting and searching, CRC and filters, written for memory-constrained systems.
---
Firmware interviews ask DSA questions too, but with a twist: no heap, fixed sizes, and an eye on worst-case timing. Each answer gives the short version, then code, complexity and follow-ups. The coding-round topics have many more worked problems.

### What is Big-O notation, and why does worst case matter more in embedded systems? {E}
Big-O notation describes an asymptotic upper bound on how an algorithm's resource usage grows with input size. In interviews it commonly describes time or auxiliary space complexity.

| Complexity | Example |
|---|---|
| O(1) | Array index |
| O(log n) | Binary search in sorted array |
| O(n) | Linear scan |
| O(n log n) | Merge sort |
| O(n²) | Nested all-pairs comparison |

#### 1. Embedded example

A linear search through 100 entries can require 100 comparisons in the worst case. Binary search requires at most about seven comparisons for 100 sorted entries, but maintaining sorted data has a cost.

#### 2. Worst-case timing

Average complexity does not establish a deadline. A hard real-time task needs bounds on input size, memory access, interrupt interference and actual worst-case execution time. An O(1) operation may still have a large or variable constant cost.

**Interview takeaway:** Big-O describes growth, not exact milliseconds. In embedded systems consider worst-case time, stack usage, allocation and actual hardware behavior.

### How do you reverse a singly linked list? {E}
Reverse a singly linked list by changing each node's next pointer to point toward the previous node.

#### 1. Algorithm

```text
Before: 10 -> 20 -> 30 -> NULL
After:  NULL <- 10 <- 20 <- 30 (new head)
```

Maintain three pointers: prev, current and saved next. Save the next pointer before changing it, then advance both working pointers.

#### 2. C implementation

```c
struct node {
    int data;
    struct node *next;
};

struct node *reverse(struct node *head)
{
    struct node *prev = NULL;

    while (head) {
        struct node *next = head->next;
        head->next = prev;
        prev = head;
        head = next;
    }
    return prev;
}
```

Call with head = reverse(head). An empty or single-node list is handled naturally. Assume the list is acyclic and exclusively owned during the update.

#### 3. Complexity

Time O(n), auxiliary space O(1). A recursive approach may use O(n) call-stack space.

**Interview takeaway:** Save the next link before overwriting it. Return the new head; the old head becomes the tail.

### How do you detect a loop in a linked list? {M}
Floyd's cycle detection algorithm uses a slow pointer moving one node at a time and a fast pointer moving two nodes at a time. If a cycle exists, they eventually meet.

#### 1. Detect the loop

```c
bool has_loop(struct node *head)
{
    struct node *slow = head, *fast = head;

    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;

        if (slow == fast)
            return true;
    }
    return false;
}
```

#### 2. Find the cycle entry

After the two pointers meet, move one pointer back to head and advance both one step at a time. Their next meeting is the cycle entry.

```text
A -> B -> C -> D -> E
          ^         |
          +---------+
Cycle entry = C
```

This works because the fast pointer travels twice the slow pointer's distance; the resulting distance relation is a multiple of the cycle length.

#### 3. Complexity

O(n) time and O(1) extra memory, with n counting distinct reachable nodes. A list without a cycle terminates at NULL.

**Interview takeaway:** Always check fast and fast->next before taking two steps. The algorithm assumes valid links and a list that is not concurrently modified.

### How do you find the middle of a linked list in one pass? {E}
Use the slow/fast pointer technique. Slow moves one node and fast moves two nodes each iteration. When fast reaches the end, slow is at the middle.

#### 1. C implementation

```c
struct node *middle(struct node *head)
{
    struct node *slow = head;
    struct node *fast = head;

    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}
```

#### 2. Examples

For 1 -> 2 -> 3 -> 4 -> 5, the result is 3. For 1 -> 2 -> 3 -> 4, the result is the second middle, 3. To choose the first middle, start fast at head->next after checking head.

#### 3. Complexity

O(n) time, O(1) auxiliary memory. This avoids first counting the nodes and then traversing half the list.

**Interview takeaway:** Define which middle to return for even-length lists. An empty list returns NULL; a cyclic list needs separate handling.

### How does a circular (ring) buffer work? {E}
A circular buffer stores elements in a fixed-size array and wraps its read/write indices at the end. It avoids shifting existing data after every operation.

#### 1. Design

```text
Slots: [0] [1] [2] [3] [4] [5] [6] [7]
          read -> queued items -> write
Indices wrap from 7 to 0.
```

This example keeps one slot unused so equal read and write indices mean empty.

#### 2. C implementation

```c
#define N 8
struct ring {
    unsigned head, tail;
    unsigned char data[N];
};

bool push(struct ring *r, unsigned char x)
{
    unsigned next = (r->head + 1) % N;
    if (next == r->tail)
        return false;
    r->data[r->head] = x;
    r->head = next;
    return true;
}

bool pop(struct ring *r, unsigned char *x)
{
    if (r->head == r->tail)
        return false;
    *x = r->data[r->tail];
    r->tail = (r->tail + 1) % N;
    return true;
}
```

Initialize head and tail to zero. Capacity is N−1; a count or additional state can support all N slots.

#### 3. Embedded use

UART receive, audio sample queues and producer/consumer pipelines. Push/pop are O(1) and allocate no memory.

**Interview takeaway:** Define empty, full and overflow behavior explicitly. The simple implementation above is single-context only; concurrent access requires a suitable protocol.

### When is a ring buffer safe without locks? {H}
**Short answer:** When there is exactly **one producer and one consumer**, only the producer writes `head` and only the consumer writes `tail`, each index is a word-sized variable updated with a single atomic store, and the producer writes the data **before** publishing the new head (the consumer reads the data **after** seeing the new head). On a single-core MCU, `volatile` indices plus a compiler barrier are enough; on multi-core or weakly ordered CPUs, use C11 atomics with release/acquire ordering. With several producers or consumers you need a lock, a critical section, or a CAS-based design.

```c
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>

#define N 256u
typedef struct {
    uint8_t data[N];
    _Atomic uint32_t head;      /* written only by the producer */
    _Atomic uint32_t tail;      /* written only by the consumer */
} spsc_t;

bool spsc_put(spsc_t *q, uint8_t b)                  /* e.g. in the UART RX ISR */
{
    uint32_t h = atomic_load_explicit(&q->head, memory_order_relaxed);
    uint32_t t = atomic_load_explicit(&q->tail, memory_order_acquire);
    if (h - t == N) return false;
    q->data[h & (N - 1)] = b;                                     /* 1. write data */
    atomic_store_explicit(&q->head, h + 1, memory_order_release);  /* 2. publish */
    return true;
}

bool spsc_get(spsc_t *q, uint8_t *b)                 /* e.g. in a task */
{
    uint32_t t = atomic_load_explicit(&q->tail, memory_order_relaxed);
    uint32_t h = atomic_load_explicit(&q->head, memory_order_acquire);
    if (h == t) return false;
    *b = q->data[t & (N - 1)];                                    /* read data after acquire */
    atomic_store_explicit(&q->tail, t + 1, memory_order_release);  /* free the slot */
    return true;
}
```

**Why each rule matters**

- **Single writer per index:** if two producers both read `head`, both write the same slot and both increment: one item is lost. A read-modify-write without atomic operations is a race.
- **Ordering:** without release/acquire (or barriers), the CPU or compiler may make the new `head` visible before the data, so the consumer reads stale data. Cortex-M0/M3/M4 execute in order and the compiler barrier is the main concern; Cortex-M7, Cortex-A and multi-core systems need real barriers (`dmb`).
- **Atomic index size:** a 32-bit index on a 32-bit MCU is written in one instruction; a 64-bit index on a 32-bit MCU would not be atomic.
- **Cache coherency:** with DMA or another core without coherent caches, the buffer needs cache maintenance or uncached memory.

**Interview follow-up:** "What if two ISRs both write?" Make the producer side a critical section (mask interrupts briefly), or give each ISR its own queue.

### What is the difference between an array and a linked list? {E}
**Short answer:** An array stores elements contiguously, giving O(1) access by index and excellent cache behaviour, but inserting or deleting in the middle needs O(n) shifting and its size is fixed. A linked list stores each element in a separate node with a pointer, giving O(1) insertion and deletion once you have the node and flexible size, but O(n) access by position, pointer overhead and poor cache locality.

| | Array | Linked list |
|---|---|---|
| Access by index | O(1) | O(n) |
| Insert/delete in the middle | O(n) shifting | O(1) given the node (or its predecessor) |
| Memory overhead | none | one or two pointers per node |
| Cache behaviour | excellent (prefetch, contiguous) | poor (nodes scattered) |
| Size | fixed (or realloc) | grows node by node |
| Allocation | one block, often static | per node (or from a pool) |

**In embedded systems:** arrays usually win: no allocation, predictable timing, and better performance for the small n typical in firmware. Linked lists are used where objects must move between collections cheaply: RTOS ready/blocked lists, timer lists, free lists in memory pools, and network buffer chains, usually as **intrusive lists** (next question) with nodes from static pools.

**Real-world note:** even on desktops, iterating an array is often an order of magnitude faster than a linked list of the same length because of cache misses, so "O(1) insert" is not the whole story.

### What is an intrusive linked list? {M}
**Short answer:** In an intrusive list the link pointers are **embedded inside** the data structure itself, instead of a separate list node that points to the data. A generic `container_of` macro recovers the outer structure from the address of the embedded link. No separate allocation is needed per element, an object can be on several lists at once (one embedded link per list), and the same list code works for any type. The Linux kernel's `list_head` and RTOS kernels use this design.

```c
#include <stddef.h>
#include <stdio.h>

struct list_head { struct list_head *next, *prev; };

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

static void list_init(struct list_head *h) { h->next = h->prev = h; }
static void list_add_tail(struct list_head *n, struct list_head *h)
{
    n->prev = h->prev; n->next = h;
    h->prev->next = n; h->prev = n;
}
static void list_del(struct list_head *n)
{
    n->prev->next = n->next; n->next->prev = n->prev;
    n->next = n->prev = NULL;
}

struct request {
    int id;
    struct list_head queue_node;     /* on the pending queue */
    struct list_head all_node;       /* on the list of all requests */
};

int main(void)
{
    struct list_head pending, all;
    list_init(&pending); list_init(&all);
    struct request r[3] = { { .id = 10 }, { .id = 20 }, { .id = 30 } };
    for (int i = 0; i < 3; i++) { list_add_tail(&r[i].queue_node, &pending); list_add_tail(&r[i].all_node, &all); }
    list_del(&r[1].queue_node);                                   /* O(1), no search */

    for (struct list_head *p = pending.next; p != &pending; p = p->next)
        printf("%d ", container_of(p, struct request, queue_node)->id);   /* 10 30 */
    printf("\n");
    return 0;
}
```

**Advantages:** no allocation (works with static objects and pools), O(1) removal given the object (doubly linked, circular with a sentinel head, so no special cases for empty or end), type-generic code, and better cache behaviour (link and data in the same cache line).

**Caveats:** an object must not be added twice to the same list via the same link; lifetime is the user's responsibility; and you must remove the object from every list before freeing it.

### How do you implement a stack and a queue with fixed arrays? {E}
**Short answer:** A **stack** (LIFO) needs an array and a `top` index: push writes `a[top++]`, pop reads `a[--top]`, checking for full (`top == N`) and empty (`top == 0`). A **queue** (FIFO) is a ring buffer with head and tail indices. Both give O(1) operations with no dynamic allocation, which is why firmware prefers them to linked implementations.

```c
#include <stdbool.h>
#include <stdio.h>

#define N 4
typedef struct { int a[N]; int top; } istack_t;

bool push(istack_t *s, int v) { if (s->top == N) return false; s->a[s->top++] = v; return true; }
bool pop(istack_t *s, int *v) { if (s->top == 0) return false; *v = s->a[--s->top]; return true; }

typedef struct { int a[N]; unsigned head, tail, count; } iqueue_t;

bool enqueue(iqueue_t *q, int v)
{
    if (q->count == N) return false;
    q->a[q->tail] = v; q->tail = (q->tail + 1) % N; q->count++;
    return true;
}
bool dequeue(iqueue_t *q, int *v)
{
    if (q->count == 0) return false;
    *v = q->a[q->head]; q->head = (q->head + 1) % N; q->count--;
    return true;
}

int main(void)
{
    istack_t s = {0}; iqueue_t q = {0}; int v;
    for (int i = 1; i <= 3; i++) { push(&s, i); enqueue(&q, i); }
    while (pop(&s, &v)) printf("%d ", v);         /* 3 2 1 */
    printf("| ");
    while (dequeue(&q, &v)) printf("%d ", v);     /* 1 2 3 */
    printf("\n");
    return 0;
}
```

**Embedded uses:** stacks for expression evaluation, undo, depth-first traversal without recursion, and parsing nested structures; queues for events, commands and data between ISRs and tasks.

**Variants:** a **deque** (double-ended queue, push/pop at both ends with a ring buffer), a **priority queue** (heap, next question), and a **stack that returns its minimum in O(1)** (keep a second stack of minimums; see the coding topics).

**Error handling:** always report overflow and underflow (return codes, counters) rather than silently overwriting; in safety-critical code, overflow is often treated as a fault.

### What is a binary heap, and how do you use it as a priority queue or timer queue? {M}
**Short answer:** A binary heap is a complete binary tree stored in an array where each parent is ≤ its children (min-heap). The smallest element is always at index 0, insertion and removal of the minimum take O(log n) by "sifting" elements up or down, and no pointers or allocation are needed. That makes it a good fixed-size **priority queue**, for example a software timer queue ordered by expiry time or an event scheduler.

```c
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#define CAP 16
typedef struct { uint32_t expiry; int id; } tmr_t;
static tmr_t heap[CAP];
static int n;

static void swap(int i, int j) { tmr_t t = heap[i]; heap[i] = heap[j]; heap[j] = t; }

bool heap_push(tmr_t t)
{
    if (n == CAP) return false;
    int i = n++;
    heap[i] = t;
    while (i > 0 && heap[(i - 1) / 2].expiry > heap[i].expiry) {   /* sift up */
        swap(i, (i - 1) / 2);
        i = (i - 1) / 2;
    }
    return true;
}

bool heap_pop(tmr_t *out)
{
    if (n == 0) return false;
    *out = heap[0];
    heap[0] = heap[--n];
    for (int i = 0;;) {                                            /* sift down */
        int l = 2 * i + 1, r = l + 1, m = i;
        if (l < n && heap[l].expiry < heap[m].expiry) m = l;
        if (r < n && heap[r].expiry < heap[m].expiry) m = r;
        if (m == i) break;
        swap(i, m);
        i = m;
    }
    return true;
}

int main(void)
{
    tmr_t t[] = { {50, 1}, {10, 2}, {30, 3}, {20, 4}, {40, 5} };
    for (int i = 0; i < 5; i++) heap_push(t[i]);
    tmr_t x;
    while (heap_pop(&x)) printf("t%d@%u ", x.id, x.expiry);   /* t2@10 t4@20 t3@30 t5@40 t1@50 */
    printf("\n");
    return 0;
}
```

**Array layout:** for the node at index i, the parent is `(i − 1) / 2` and the children are `2i + 1` and `2i + 2`.

**Timer queue design comparison**

| Structure | Insert | Next expiry | Cancel |
|---|---|---|---|
| Unsorted array | O(1) | O(n) | O(1) with index |
| Sorted linked list (FreeRTOS delayed list) | O(n) | O(1) | O(1) |
| Binary heap | O(log n) | O(1) peek, O(log n) pop | O(log n) with stored index |
| Timer wheel (Linux timers) | O(1) | O(1) amortised | O(1) |
| Red-black tree (Linux hrtimers) | O(log n) | O(1) cached leftmost | O(log n) |

**Wrap-around note:** with 32-bit tick counters, compare expiry times with `(int32_t)(a - b) < 0` instead of `a < b`, so ordering stays correct across overflow (as long as timeouts are less than half the counter range).

### How does binary search work and what is the common bug? {E}
**Short answer:** On a sorted array, compare the target with the middle element and discard the half that cannot contain it, repeating until found or the range is empty: O(log n). The classic bug is computing the middle as `(low + high) / 2`, which can overflow when indices are large; use `low + (high − low) / 2`. The other common bugs are mixing inclusive and exclusive bounds, which causes infinite loops or missed elements, and unsigned underflow with `high = mid − 1` when `mid` is 0.

```c
#include <stdio.h>
#include <stddef.h>

/* returns index of key, or -1; half-open range [lo, hi) avoids the unsigned underflow */
long bsearch_int(const int *a, size_t n, int key)
{
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (a[mid] < key)      lo = mid + 1;
        else if (a[mid] > key) hi = mid;
        else                   return (long)mid;
    }
    return -1;
}

/* lower bound: first index with a[i] >= key (useful for insertion points and lookup tables) */
size_t lower_bound(const int *a, size_t n, int key)
{
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (a[mid] < key) lo = mid + 1; else hi = mid;
    }
    return lo;
}

int main(void)
{
    int a[] = { 2, 5, 8, 12, 16, 23, 38 };
    printf("%ld %ld %zu\n", bsearch_int(a, 7, 23), bsearch_int(a, 7, 7), lower_bound(a, 7, 13));   /* 5 -1 4 */
    return 0;
}
```

**Embedded uses:** lookup tables (e.g. a thermistor resistance-to-temperature table, then linear interpolation between the two neighbours), finding a record in a sorted flash log, and bisection when tuning a parameter.

**Variants:** first/last occurrence, search in a rotated sorted array, and searching on the answer (e.g. the smallest buffer size that satisfies a condition).

### What is a hash table and how do you handle collisions? {M}
**Short answer:** A hash table maps keys to array buckets with a hash function, giving O(1) average lookup, insertion and deletion. When two keys map to the same bucket (a collision), it is handled by **chaining** (each bucket holds a linked list of entries) or **open addressing** (probe for another slot: linear, quadratic or double hashing). For embedded use, a fixed-size open-addressing table with linear probing is common: no allocation, cache friendly, and predictable memory; keep the load factor below about 70% so probe sequences stay short.

```c
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#define TBL 16u                          /* power of two */
typedef struct { uint32_t key; int val; bool used; } slot_t;
static slot_t tbl[TBL];

static uint32_t hash32(uint32_t x)       /* integer mixing hash */
{
    x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16;
    return x;
}

bool ht_put(uint32_t key, int val)
{
    for (uint32_t i = 0, h = hash32(key); i < TBL; i++) {
        slot_t *s = &tbl[(h + i) & (TBL - 1)];
        if (!s->used || s->key == key) { s->key = key; s->val = val; s->used = true; return true; }
    }
    return false;                                         /* full */
}

bool ht_get(uint32_t key, int *val)
{
    for (uint32_t i = 0, h = hash32(key); i < TBL; i++) {
        slot_t *s = &tbl[(h + i) & (TBL - 1)];
        if (!s->used) return false;                       /* empty slot ends the probe */
        if (s->key == key) { *val = s->val; return true; }
    }
    return false;
}

int main(void)
{
    ht_put(0x100, 1); ht_put(0x7E3, 2); ht_put(0xCAFE, 3);
    int v;
    printf("%d ", ht_get(0x7E3, &v) ? v : -1);
    printf("%d\n", ht_get(0x123, &v) ? v : -1);           /* 2 -1 */
    return 0;
}
```

**Deletion with open addressing:** you cannot simply mark a slot empty, because that would break the probe chain for keys inserted after it; use a **tombstone** marker or re-insert the following cluster (backward-shift deletion).

**Choosing a hash function:** fast and well-mixing (FNV-1a for strings, multiply-shift or murmur finalisers for integers). Hash tables used with untrusted input (network keys) need a seeded hash (SipHash) to avoid attackers forcing collisions.

**Worst case:** O(n) if many keys collide, so hard real-time code sometimes prefers a sorted array with binary search (O(log n) guaranteed) or a perfect hash generated offline for a fixed key set (e.g. command names).

### What are binary search trees, and why use a balanced tree? {M}
**Short answer:** In a binary search tree (BST), every node's left subtree has smaller keys and its right subtree larger keys, so search, insert and delete follow one path from the root: O(height). If keys arrive in sorted order, a plain BST degenerates into a linked list (height n, O(n) operations). **Self-balancing trees** (red-black, AVL) restructure with rotations to keep the height O(log n) in the worst case, and they keep keys in order (unlike hash tables), supporting in-order traversal and range queries.

```c
#include <stdio.h>
#include <stddef.h>

struct tnode { int key; struct tnode *left, *right; };

struct tnode *bst_insert(struct tnode *root, struct tnode *n)    /* n comes from a pool */
{
    struct tnode **p = &root;
    while (*p) p = (n->key < (*p)->key) ? &(*p)->left : &(*p)->right;   /* iterative: no recursion */
    n->left = n->right = NULL;
    *p = n;
    return root;
}

struct tnode *bst_find(struct tnode *r, int key)
{
    while (r && r->key != key) r = (key < r->key) ? r->left : r->right;
    return r;
}

static void inorder(const struct tnode *r) { if (!r) return; inorder(r->left); printf("%d ", r->key); inorder(r->right); }

int main(void)
{
    static struct tnode pool[6];
    int keys[] = { 50, 30, 70, 20, 40, 60 };
    struct tnode *root = NULL;
    for (int i = 0; i < 6; i++) { pool[i].key = keys[i]; root = bst_insert(root, &pool[i]); }
    inorder(root); printf("| found 40: %s\n", bst_find(root, 40) ? "yes" : "no");   /* 20 30 40 50 60 70 | yes */
    return 0;
}
```

**Where balanced trees appear in systems software**

- Linux: red-black trees (`rbtree`) for the CFS/EEVDF run queue, hrtimers, virtual memory areas (now a maple tree), epoll; Zephyr's scalable scheduler queue.
- Interval trees for overlapping ranges (memory regions, IOMMU mappings).
- B-trees and B+ trees for filesystems and databases on flash (high fan-out, fewer reads).

**Traversals:** in-order (sorted output), pre-order (copy/serialise a tree), post-order (free a tree), level-order (BFS with a queue). For embedded code, avoid deep recursion on unbalanced trees; use iterative traversals with an explicit stack.

### How do BFS and DFS work, and where are graphs used in embedded software? {M}
**Short answer:** **Breadth-first search (BFS)** visits nodes level by level using a queue, and finds the shortest path in an unweighted graph. **Depth-first search (DFS)** goes as deep as possible along each branch before backtracking, using a stack or recursion, and is used for cycle detection, topological ordering and connectivity. Both are O(V + E). Embedded uses include dependency ordering (initialising drivers after their dependencies), deadlock detection (cycles in a lock or wait-for graph), routing in mesh networks, and state machines.

```c
#include <stdio.h>
#include <stdbool.h>

#define V 6
/* adjacency matrix: small, static; use adjacency lists for sparse/large graphs */
static const bool adj[V][V] = {
    /* 0 */ {0,1,1,0,0,0},
    /* 1 */ {0,0,0,1,0,0},
    /* 2 */ {0,0,0,1,1,0},
    /* 3 */ {0,0,0,0,0,1},
    /* 4 */ {0,0,0,0,0,1},
    /* 5 */ {0,0,0,0,0,0},
};

void bfs(int start, int dist[V])
{
    int q[V], head = 0, tail = 0;
    for (int i = 0; i < V; i++) dist[i] = -1;
    dist[start] = 0; q[tail++] = start;
    while (head < tail) {
        int u = q[head++];
        for (int v = 0; v < V; v++)
            if (adj[u][v] && dist[v] < 0) { dist[v] = dist[u] + 1; q[tail++] = v; }
    }
}

int main(void)
{
    int d[V];
    bfs(0, d);
    for (int i = 0; i < V; i++) printf("%d ", d[i]);   /* 0 1 1 2 2 3 */
    printf("\n");
    return 0;
}
```

**DFS notes:** use three colours (unvisited, in progress, done) to detect cycles in a directed graph: reaching an "in progress" node means a cycle. Post-order DFS gives a reverse topological order. Kahn's algorithm (repeatedly remove nodes with no incoming edges) gives a topological order without recursion — see the systems coding topic.

**Weighted shortest paths:** Dijkstra's algorithm with a priority queue (non-negative weights), Bellman-Ford with negative weights; used in routing protocols (OSPF, RPL in 6LoWPAN meshes).

**Memory:** an adjacency matrix needs V² bits/bytes (fine for small V, e.g. a bitmap of 32×32); adjacency lists need O(V + E).

### Which sorting algorithm would you use on a microcontroller? {M}
**Short answer:** It depends on n, memory and timing requirements. **Insertion sort** for small (n below ~20–30) or nearly sorted arrays: simple, in-place, stable and fastest in practice for tiny inputs. **Heap sort** when you need guaranteed O(n log n) with O(1) extra memory and no recursion. **Quicksort** is fastest on average but has an O(n²) worst case and uses recursion (stack); use median-of-three pivots and recurse on the smaller half if you use it. **Merge sort** is stable and O(n log n) but needs O(n) extra memory. **Counting or radix sort** for small integer keys (e.g. 8- or 12-bit ADC values) in O(n + k).

```c
#include <stdio.h>
#include <stddef.h>

void insertion_sort(int *a, size_t n)
{
    for (size_t i = 1; i < n; i++) {
        int key = a[i];
        size_t j = i;
        while (j > 0 && a[j - 1] > key) { a[j] = a[j - 1]; j--; }
        a[j] = key;
    }
}

int main(void)
{
    int a[] = { 7, 3, 9, 1, 4, 1, 8 };
    insertion_sort(a, 7);
    for (int i = 0; i < 7; i++) printf("%d ", a[i]);   /* 1 1 3 4 7 8 9 */
    printf("\n");
    return 0;
}
```

**Typical embedded sorting problems and good answers**

| Problem | Good choice |
|---|---|
| Median filter of 5–9 samples (remove spikes) | insertion sort of a copy, or a sorting network |
| Sort 1000 16-bit sensor readings | radix/counting sort or heap sort |
| Keep the top-k largest values | min-heap of size k, O(n log k) |
| Nearly sorted log entries by timestamp | insertion sort |
| Must be stable and n is large | merge sort with a static scratch buffer |
| Standard library available, non-critical code | `qsort` (check its stack usage and that its worst case is acceptable) |

**Hard real-time:** prefer algorithms whose worst case is acceptable and bounded (heap sort, fixed sorting networks) over ones that are fast "on average".

**Sorting networks:** fixed sequences of compare-and-swap operations for a known small n (for example, 19 compare-swaps give the median of 9 values); branch-free and constant time, used in DSP median filters.

### How do you compute a CRC and why is it used? {M}
**Short answer:** A Cyclic Redundancy Check treats the data as a polynomial over GF(2), divides it by a fixed generator polynomial, and uses the remainder as the check value. It is very good at detecting accidental errors, including all single-bit errors, all bursts shorter than the CRC width, and most other patterns, so it is used in Ethernet, CAN, USB, storage, flash images and serial protocols. Bitwise implementations are tiny; table-driven implementations process a byte per lookup; many MCUs have a hardware CRC unit.

```c
#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

uint8_t crc8(const uint8_t *d, size_t n)              /* CRC-8, poly 0x07, init 0 (SMBus PEC) */
{
    uint8_t crc = 0;
    while (n--) {
        crc ^= *d++;
        for (int i = 0; i < 8; i++)
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
    }
    return crc;
}

uint16_t crc16_modbus(const uint8_t *d, size_t n)     /* reflected poly 0xA001, init 0xFFFF */
{
    uint16_t crc = 0xFFFF;
    while (n--) {
        crc ^= *d++;
        for (int i = 0; i < 8; i++)
            crc = (crc & 1) ? (uint16_t)((crc >> 1) ^ 0xA001) : (uint16_t)(crc >> 1);
    }
    return crc;
}

uint32_t crc32(const uint8_t *d, size_t n)            /* IEEE 802.3 (zlib), reflected 0xEDB88320 */
{
    uint32_t crc = 0xFFFFFFFFu;
    while (n--) {
        crc ^= *d++;
        for (int i = 0; i < 8; i++) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

int main(void)
{
    const uint8_t s[] = "123456789";                  /* standard check string */
    printf("%02X %04X %08X\n", crc8(s, 9), crc16_modbus(s, 9), crc32(s, 9));   /* F4 4B37 CBF43926 */
    return 0;
}
```

**Parameters that define a CRC:** width, polynomial, initial value, input/output reflection and final XOR. Two "CRC-16" implementations with different parameters give different results, so always check against the standard check value for "123456789".

**CRC vs checksum vs hash vs MAC**

| | Detects | Protects against tampering |
|---|---|---|
| Sum / XOR checksum | some errors, weak | no |
| CRC | accidental errors, strong for bursts | no (easy to forge) |
| Cryptographic hash (SHA-256) | any change | only if the hash itself is protected |
| MAC / signature (HMAC, ECDSA) | any change | yes |

**Embedded uses:** image integrity in bootloaders (CRC32 for corruption, a signature for authenticity), configuration blocks in flash, and frame checks in UART protocols.

### How do you implement a moving average filter efficiently? {M}
**Short answer:** Keep a ring buffer of the last N samples and a running sum. For each new sample, subtract the oldest sample, add the newest, and store it in the buffer: O(1) per sample regardless of N. Use a power-of-two N so the division is a shift. When RAM is tight, an **exponential moving average** (`y += (x − y) >> k`) needs no buffer at all.

```c
#include <stdint.h>
#include <stdio.h>

#define LOG2_N 3
#define N (1u << LOG2_N)                  /* 8-sample window */

typedef struct { uint16_t win[N]; uint32_t sum; uint8_t i; } mavg_t;

uint16_t mavg_update(mavg_t *f, uint16_t x)
{
    f->sum += (uint32_t)x - f->win[f->i];      /* unsigned wrap cancels out correctly */
    f->win[f->i] = x;
    f->i = (uint8_t)((f->i + 1) & (N - 1));
    return (uint16_t)(f->sum >> LOG2_N);
}

typedef struct { int32_t y; } ema_t;           /* fixed point: y holds value << 4 */
int32_t ema_update(ema_t *f, int32_t x, int k)  /* alpha = 1/2^k */
{
    f->y += ((x << 4) - f->y) >> k;
    return f->y >> 4;
}

int main(void)
{
    mavg_t m = {0};
    ema_t e = { 0 };
    for (int t = 0; t < 12; t++) {
        uint16_t x = (t < 4) ? 0 : 800;        /* step input */
        printf("%u/%ld ", mavg_update(&m, x), (long)ema_update(&e, x, 2));
    }
    printf("\n");
    return 0;
}
```

**Details**

- The sum must be wide enough: N × max sample (8 × 4095 fits easily in 32 bits).
- During the first N samples the average includes the zero-initialised buffer; pre-fill with the first sample if that matters.
- The moving average delays the signal by (N − 1)/2 samples and is a weak low-pass filter with ripples in its frequency response.
- **EMA** has an equivalent time constant of about 2^k samples, costs one subtraction and shift, but keeps fractional precision only if you store the state with extra bits (as above).
- **Median filter** (median of the last 3–9 samples) removes spikes that averages smear.
- For sharper frequency responses, use FIR/IIR filters (CMSIS-DSP provides optimised versions).

### How do you find the maximum subarray sum (Kadane's algorithm)? {M}
**Short answer:** Scan the array once, tracking the best sum of a subarray that **ends at the current element** (either extend the previous best-ending subarray or start fresh at this element) and the best sum seen overall. O(n) time and O(1) memory. Initialising both with the first element (not 0) makes it correct for arrays where every number is negative (the answer is then the largest single element).

```c
#include <stdio.h>
#include <stddef.h>

/* returns the max sum and the [start, end] indices of one maximum subarray; n must be >= 1 */
long max_subarray(const int *a, size_t n, size_t *start, size_t *end)
{
    long cur = a[0], best = a[0];
    size_t cur_start = 0;
    *start = *end = 0;
    for (size_t i = 1; i < n; i++) {
        if (cur < 0) { cur = a[i]; cur_start = i; }     /* a negative prefix only hurts: restart */
        else         { cur += a[i]; }
        if (cur > best) { best = cur; *start = cur_start; *end = i; }
    }
    return best;
}

int main(void)
{
    int a[] = { -2, 1, -3, 4, -1, 2, 1, -5, 4 };
    int b[] = { -8, -3, -6, -2, -5 };
    size_t s, e;
    long m = max_subarray(a, 9, &s, &e);
    printf("%ld [%zu..%zu]\n", m, s, e);               /* 6 [3..6] */
    m = max_subarray(b, 5, &s, &e);
    printf("%ld [%zu..%zu]\n", m, s, e);               /* -2 [3..3] */
    return 0;
}
```

**Why it works:** the best subarray ending at position i is either a[i] alone or a[i] plus the best subarray ending at i − 1; if that previous best is negative, dropping it can only improve the sum.

**Common mistakes:** starting with `best = 0` (returns 0 for all-negative input, which is the answer only if an empty subarray is allowed), and integer overflow on long arrays (use a wider type for the sum).

**Variants:** maximum circular subarray (max of the normal answer and total − minimum subarray, handling the all-negative case), maximum product subarray (track both max and min because negatives flip signs), and the embedded version: "find the window of samples with the highest energy".
