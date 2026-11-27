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
A ring buffer can avoid locks in a single-producer/single-consumer (SPSC) design if each side owns its index and publication uses the required atomic ordering.

#### 1. C11 example

```c
#include <stdatomic.h>
#include <stdbool.h>
#define N 8

static unsigned char buf[N];
static atomic_uint head, tail;

bool push(unsigned char value)
{
    unsigned h = atomic_load_explicit(&head, memory_order_relaxed);
    unsigned next = (h + 1) % N;
    if (next == atomic_load_explicit(&tail, memory_order_acquire))
        return false;
    buf[h] = value;
    atomic_store_explicit(&head, next, memory_order_release);
    return true;
}

bool pop(unsigned char *value)
{
    unsigned t = atomic_load_explicit(&tail, memory_order_relaxed);
    if (t == atomic_load_explicit(&head, memory_order_acquire))
        return false;
    *value = buf[t];
    atomic_store_explicit(&tail, (t + 1) % N, memory_order_release);
    return true;
}
```

The producer releases head after writing the slot; the consumer acquires head before reading. The consumer similarly publishes tail after reading so the producer cannot reuse a slot prematurely.

#### 2. Limitations

Exactly one producer and one consumer, initialized state, valid output pointer, no concurrent reset. Verify atomics are lock-free and appropriate for the execution context if using this from an ISR. DMA requires a separate ownership/cache protocol.

**Interview takeaway:** Separate index ownership is necessary but not sufficient. Acquire/release ordering protects slot publication and reuse.

### What is the difference between an array and a linked list? {E}
An array stores elements contiguously; a linked list stores nodes connected through pointers, which can occupy unrelated addresses.

| Array | Linked list |
|---|---|
| O(1) indexed access | O(n) indexed access |
| Good cache locality | Pointer chasing may reduce locality |
| Insertion in middle can move elements | O(1) relinking given insertion position |
| Fixed capacity or resized allocation | Nodes can be added/removed separately |
| No per-element link overhead | Link pointer(s) consume memory |

#### 1. Example

An array of 100 four-byte ints requires 400 bytes of element storage. A singly linked node on a typical 64-bit ABI may require 16 bytes for an int, padding and a pointer, so the same 100 values can need about 1600 bytes before allocator metadata.

#### 2. Embedded selection

Use fixed arrays for bounded buffers, fast indexing and cache locality. Use lists when frequent insertion/removal and stable node addresses are valuable. Searching for an insertion position can still cost O(n).

**Interview takeaway:** Linked-list insertion is O(1) only when the relevant position is already known. Consider memory overhead and deterministic allocation.

### What is an intrusive linked list? {M}
An intrusive linked list embeds its linkage directly inside the containing object rather than allocating a separate wrapper node.

#### 1. Linux example

```c
struct device_entry {
    int id;
    struct list_head link;
};

LIST_HEAD(devices);

// Given a live, initialized entry d:
list_add_tail(&d->link, &devices);
```

Iterate using the kernel list helpers:

```c
struct device_entry *d;
list_for_each_entry(d, &devices, link) {
    pr_info("%d\n", d->id);
}
```

The helpers recover the enclosing object from its link, conceptually using container_of.

#### 2. Advantages

No separate list-node allocation, stable containing-object identity and O(1) insertion/removal given a node. An object can belong to several lists if it contains distinct link members.

#### 3. Lifetime rules

Initialize links before use, remove a node from all relevant lists before freeing it, and use required locks or RCU variants for concurrent traversal.

**Interview takeaway:** Intrusive lists embed membership in the object. They reduce allocation overhead but require explicit ownership and lifetime discipline.

### How do you implement a stack and a queue with fixed arrays? {E}
A stack uses LIFO (last in, first out); a queue uses FIFO (first in, first out). Both can be implemented with fixed arrays for deterministic storage.

#### 1. Stack

```c
#define N 16
struct stack {
    int a[N];
    unsigned count;
};

bool push(struct stack *s, int v)
{
    if (s->count == N) return false;
    s->a[s->count++] = v;
    return true;
}

bool pop(struct stack *s, int *v)
{
    if (!s->count) return false;
    *v = s->a[--s->count];
    return true;
}
```

#### 2. Queue

```c
struct queue {
    int a[N];
    unsigned head, tail, count;
};

bool enqueue(struct queue *q, int v)
{
    if (q->count == N) return false;
    q->a[q->tail] = v;
    q->tail = (q->tail + 1) % N;
    q->count++;
    return true;
}

bool dequeue(struct queue *q, int *v)
{
    if (!q->count) return false;
    *v = q->a[q->head];
    q->head = (q->head + 1) % N;
    q->count--;
    return true;
}
```

Initialize structures to zero and supply valid output pointers. These are single-context implementations. All operations are O(1).

**Interview takeaway:** Check overflow and underflow. A circular queue avoids moving elements; a stack needs only a top/count index.

### What is a binary heap, and how do you use it as a priority queue or timer queue? {M}
A binary heap is a complete binary tree stored compactly in an array. A min-heap keeps every parent no greater than its children, so the minimum is at index zero.

#### 1. Index relationships

For zero-based index i, parent=(i−1)/2 for i>0, left=2i+1 and right=2i+2, when children exist.

#### 2. Example insertion

```text
Heap: [2, 5, 7, 9]
Insert 1 at end: [2, 5, 7, 9, 1]
Sift up:         [2, 1, 7, 9, 5]
Sift up:         [1, 2, 7, 9, 5]
```

To remove the minimum, move the last element to the root and sift it downward using the smaller child.

| Operation | Complexity |
|---|---|
| Peek minimum | O(1) |
| Insert | O(log n) |
| Remove minimum | O(log n) |
| Build heap bottom-up | O(n) |

#### 3. Embedded use

Store timers by expiry time or jobs by priority. Use fixed-capacity storage where required and a wrap-safe deadline comparison for modular time counters.

**Interview takeaway:** A heap is not a fully sorted array. It maintains the root extreme efficiently and offers bounded logarithmic insertion/removal.

### How does binary search work and what is the common bug? {E}
Binary search finds a value in a sorted array by repeatedly discarding half of the remaining search range.

#### 1. C implementation

```c
bool binary_search(const int *a, size_t n, int key,
                   size_t *index)
{
    size_t lo = 0, hi = n;

    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (a[mid] == key) {
            if (index) *index = mid;
            return true;
        }
        if (a[mid] < key)
            lo = mid + 1;
        else
            hi = mid;
    }
    return false;
}
```

This uses a half-open interval [lo, hi), avoiding unsigned underflow at mid=0. For [2,4,6,8,10] and key 8, first examine 6, then 10, then 8.

#### 2. Common mistakes

Using mid=(lo+hi)/2 can overflow for large indices. Incorrect endpoint updates can leave the search interval unchanged and cause an infinite loop. The array must be sorted according to the comparison used.

Time O(log n), extra space O(1). For duplicates this returns any matching index; lower-bound search is needed for the first occurrence.

**Interview takeaway:** Use overflow-safe midpoint calculation and maintain a clear interval invariant.

### What is a hash table and how do you handle collisions? {M}
A hash table maps keys to array positions using a hash function. It provides fast average lookup and insertion when keys are distributed well and the load factor is controlled.

#### 1. Collision handling

```text
hash(key) % capacity -> bucket
Different keys may select the same bucket.
```

Separate chaining stores colliding entries in a list or another bucket structure. Open addressing probes other slots, for example using linear probing.

#### 2. Fixed-table lookup example

```c
#define N 16
struct entry { bool used; unsigned key; int value; };
static struct entry table[N];

bool lookup(unsigned key, int *value)
{
    unsigned start = key % N;
    for (unsigned i = 0; i < N; i++) {
        struct entry *e = &table[(start + i) % N];
        if (!e->used)
            return false;
        if (e->key == key) {
            *value = e->value;
            return true;
        }
    }
    return false;
}
```

This assumes entries are inserted by the same probe sequence and never deleted without preserving probe chains. Deletion needs tombstones or a correct reorganization algorithm.

#### 3. Complexity

Average lookup can be O(1), but worst case O(n). Fixed capacity avoids resizing in embedded code; full-table handling is mandatory.

**Interview takeaway:** A hash function does not eliminate collisions. Bound probes and capacity when timing predictability matters.

### What are binary search trees, and why use a balanced tree? {M}
A binary search tree (BST) keeps keys in ordered subtrees: keys smaller than a node are on its left, larger keys on its right, with a chosen duplicate policy.

#### 1. Example

```text
       8
      / \
     3   12
    / \    \
   1   5    15
```

In-order traversal produces sorted keys. Searching for 5 follows 8 -> 3 -> 5.

#### 2. Why balance?

An ordinary BST can become a chain if sorted keys are inserted, giving O(n) lookup. Balanced trees such as AVL and red-black trees maintain logarithmic height through rotations and metadata.

| Tree | Typical search worst case |
|---|---|
| Unbalanced BST | O(n) |
| Balanced BST | O(log n) |

#### 3. Embedded use

Use a balanced tree for ordered timer deadlines, address ranges or dynamic ordered records when iteration and predecessor/successor lookup are needed. Linux uses red-black trees in various subsystems.

**Interview takeaway:** A BST provides ordering, not guaranteed logarithmic performance unless its height is bounded. A heap is preferable when only the minimum/maximum is needed.

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
