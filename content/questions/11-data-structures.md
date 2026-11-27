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
Breadth-first search (BFS) explores a graph level by level using a queue. Depth-first search (DFS) follows a path deeply before backtracking using a stack or recursion.

#### 1. Example

```text
A connects to B and C
B connects to D
C connects to E

BFS from A: A, B, C, D, E
DFS from A: A, B, D, C, E (one valid order)
```

#### 2. Algorithm

BFS marks the start visited, enqueues it, then repeatedly removes one vertex and enqueues unvisited neighbors. DFS pushes or recursively visits unvisited neighbors. Mark vertices when discovered to avoid cycles and duplicate work.

With adjacency lists, both take O(V+E) time and O(V) auxiliary storage in the usual implementations.

#### 3. Embedded applications

BFS can find shortest paths in an unweighted network; DFS can explore dependency graphs or detect cycles with additional visitation-state tracking. Fixed-size stacks and queues can bound memory when graph size is known.

**Interview takeaway:** BFS is useful for minimum-hop paths; DFS for deep exploration and dependency analysis. Bound graph storage and avoid unbounded recursion in small firmware stacks.

### Which sorting algorithm would you use on a microcontroller? {M}
Sorting algorithm selection on a microcontroller depends on input size, worst-case latency, memory budget and whether stability is needed.

| Algorithm | Worst-case time | Extra space / property |
|---|---|---|
| Insertion sort | O(n²) | O(1), stable |
| Heapsort | O(n log n) | O(1) with iterative sift |
| Merge sort | O(n log n) | Typically O(n), stable |
| Quicksort | O(n²) | Stack depends on implementation |

#### 1. Insertion sort for small arrays

```c
void sort(int *a, size_t n)
{
    for (size_t i = 1; i < n; i++) {
        int key = a[i];
        size_t j = i;
        while (j > 0 && a[j - 1] > key) {
            a[j] = a[j - 1];
            j--;
        }
        a[j] = key;
    }
}
```

This is simple, in-place and efficient for small or nearly sorted arrays.

#### 2. Real-time choice

For larger inputs with strict bounds, consider an iterative heapsort or another algorithm with guaranteed worst-case complexity. Avoid relying on average quicksort performance for hard deadlines without controlling its worst case.

**Interview takeaway:** There is no universal best sort. A small fixed array often benefits from insertion sort; large or deadline-sensitive input requires explicit worst-case analysis.

### How do you compute a CRC and why is it used? {M}
A CRC (Cyclic Redundancy Check) detects accidental data corruption by computing a polynomial remainder over the message bits.

#### 1. CRC-16/Modbus example

```c
uint16_t crc16_modbus(const uint8_t *data, size_t n)
{
    uint16_t crc = 0xFFFF;

    for (size_t i = 0; i < n; i++) {
        crc ^= data[i];
        for (unsigned b = 0; b < 8; b++) {
            if (crc & 1U)
                crc = (crc >> 1) ^ 0xA001U;
            else
                crc >>= 1;
        }
    }
    return crc;
}
```

For ASCII "123456789", the expected check value is 0x4B37. The wire protocol determines how the CRC bytes are serialized.

#### 2. Parameters matter

CRC width, polynomial, initial value, reflection and final XOR determine the algorithm. A hardware CRC peripheral must be configured to match the exact protocol.

#### 3. Why CRC?

CRC detects many burst and random errors efficiently. It does not authenticate the sender and is not a cryptographic integrity mechanism against intentional modification.

**Interview takeaway:** Match all CRC parameters and verify a known test vector. Hardware, table-driven and bitwise implementations must produce the same protocol-defined result.

### How do you implement a moving average filter efficiently? {M}
A moving average filter computes the average of the most recent N samples. A circular buffer and running sum reduce each update from O(N) to O(1).

#### 1. C implementation

```c
#define N 8

struct average {
    int32_t samples[N];
    int64_t sum;
    unsigned pos, count;
};

int32_t update(struct average *a, int32_t x)
{
    if (a->count == N)
        a->sum -= a->samples[a->pos];
    else
        a->count++;

    a->samples[a->pos] = x;
    a->sum += x;
    a->pos = (a->pos + 1) % N;

    return (int32_t)(a->sum / a->count);
}
```

Initialize the structure to zero. The wider accumulator safely holds eight int32_t values. The startup policy averages only the available samples.

#### 2. Example (N=3)

Samples 3, 6, 9 give average 6. When 12 arrives, remove 3 and add 12; the new average is (6+9+12)/3 = 9.

#### 3. Trade-off

A larger window smooths noise but increases delay and reduces responsiveness. Integer division truncates, which may matter for signal-processing precision.

**Interview takeaway:** A running sum and circular storage provide constant-time updates. Size the accumulator for the worst-case sum and define startup behavior.

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
