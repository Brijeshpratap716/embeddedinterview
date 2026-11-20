---
slug: data-structures
title: Data Structures & Algorithms
icon: 🧮
level: Intermediate
order: 11
desc: Linked lists, ring buffers, stacks, queues, hashing, sorting and searching, written for memory-constrained systems.
---
Firmware interviews ask DSA questions too, but with a twist: no heap, fixed sizes, and an eye on worst-case timing.

### How do you reverse a singly linked list? {E}
Walk the list once, reversing each `next` pointer:

```c
struct node { int val; struct node *next; };

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

O(n) time, O(1) memory. Be ready to do it recursively too, and to explain why the iterative version is preferred in embedded code.

### How do you detect a loop in a linked list? {M}
Floyd's tortoise and hare: move one pointer by one node and another by two. If there is a cycle they meet; if the fast pointer reaches `NULL` there is none.

```c
bool has_cycle(struct node *h)
{
    struct node *slow = h, *fast = h;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}
```

To find the start of the loop, reset one pointer to the head after they meet and advance both one step at a time; they meet at the loop's first node.

### How do you find the middle of a linked list in one pass? {E}
Use the same slow/fast pointer technique: when the fast pointer reaches the end, the slow pointer is at the middle. For an even number of nodes this gives the second of the two middle nodes; stop at `fast->next->next == NULL` to get the first.

### How does a circular (ring) buffer work? {E}
A fixed array with a **head** (write) index and a **tail** (read) index that wrap around. It is the standard structure for UART receive, logging and producer/consumer queues without dynamic memory. With a power-of-two size, wrapping is a cheap mask:

```c
#define RB_SIZE 256u                /* power of two */
static uint8_t  buf[RB_SIZE];
static volatile uint32_t head, tail;   /* free-running counters */

bool rb_put(uint8_t b)
{
    if (head - tail == RB_SIZE) return false;      /* full */
    buf[head & (RB_SIZE - 1)] = b;
    head++;
    return true;
}
```

Using free-running counters (and unsigned subtraction) distinguishes full from empty without wasting a slot. See the practice problem *Lock-free ring buffer*.

### When is a ring buffer safe without locks? {H}
With exactly **one producer and one consumer**, where only the producer writes `head` and only the consumer writes `tail`, and each index update is a single atomic store of a word-sized variable. The producer must write the data **before** publishing the new `head`; on a single-core MCU, `volatile` plus a compiler barrier is enough, while on multi-core or out-of-order CPUs you need release/acquire ordering (`atomic_store_explicit(..., memory_order_release)`). With several producers or consumers you need a lock or CAS-based design.

### What is the difference between an array and a linked list? {E}
| | Array | Linked list |
|---|---|---|
| Access by index | O(1) | O(n) |
| Insert/delete in middle | O(n) shifting | O(1) once you have the node |
| Memory | Contiguous, cache friendly | Per-node pointer overhead, scattered |
| Size | Fixed (or realloc) | Grows node by node |

In embedded systems arrays usually win because of cache behaviour and no allocation; linked lists are used with nodes embedded inside other structures (intrusive lists), as in the Linux kernel's `list_head` and RTOS ready lists.

### What is an intrusive linked list? {M}
Instead of a list node pointing to your data, the list links are **embedded inside** your data structure:

```c
struct list_head { struct list_head *next, *prev; };
struct request { int id; struct list_head node; };

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))
```

`container_of` recovers the outer struct from the embedded node. No separate allocation is needed, an object can be on several lists at once, and the list code is generic. This is how Linux and most RTOS kernels build lists.

### How do you implement a stack and a queue with fixed arrays? {E}
A **stack** needs an array and a top index: push writes `a[top++]`, pop reads `a[--top]`, checking for full and empty. A **queue** is a ring buffer with head and tail indexes. Both are O(1) per operation with no allocation, which is why firmware uses them instead of linked implementations.

### Which sorting algorithm would you use on a microcontroller? {M}
- **Insertion sort** for small or nearly sorted arrays: simple, in-place, stable, very fast for n below about 20.
- **Heap sort** when you need guaranteed O(n log n) with O(1) extra memory and no recursion.
- **Quicksort** is fast on average but O(n²) worst case and recursive (stack usage), so be careful; `qsort` from newlib may be fine for non-critical code.
- **Merge sort** is stable and O(n log n) but needs O(n) extra memory.
- **Counting/radix sort** for small integer keys (e.g. 8-bit ADC values).

### How does binary search work and what is the common bug? {E}
On a sorted array, compare the target with the middle element and discard half each time, O(log n). The classic bug is computing the middle as `(low + high) / 2`, which can overflow for large indexes; use `low + (high - low) / 2`. Also be precise about whether `high` is inclusive or exclusive, because mixing them causes infinite loops or missed elements.

### What is a hash table and how do you handle collisions? {M}
A hash table maps keys to buckets using a hash function, for average O(1) lookup. Collisions are handled by **chaining** (each bucket holds a list) or **open addressing** (probe for the next free slot: linear, quadratic or double hashing). For embedded use, a fixed-size open-addressing table with linear probing is common because it needs no allocation and is cache friendly; keep the load factor below about 70%.

### How do you compute a CRC and why is it used? {M}
A Cyclic Redundancy Check treats data as a polynomial over GF(2) and divides it by a generator polynomial; the remainder is the CRC. It reliably detects burst errors and is used in Ethernet, CAN, USB, storage and firmware images. Bitwise CRC-8:

```c
uint8_t crc8(const uint8_t *d, size_t n)   /* poly 0x07 */
{
    uint8_t crc = 0;
    while (n--) {
        crc ^= *d++;
        for (int i = 0; i < 8; i++)
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
    }
    return crc;
}
```

A 256-entry lookup table processes a byte per step; many MCUs have a hardware CRC unit. A CRC detects accidental errors only; use a MAC or signature against tampering.

### How do you implement a moving average filter efficiently? {M}
Keep a ring buffer of the last N samples and a running sum. For each new sample, subtract the oldest, add the newest and store it:

```c
sum += x - win[i];
win[i] = x;
i = (i + 1) & (N - 1);
avg = sum >> LOG2_N;    /* N a power of two */
```

O(1) per sample. When RAM is tight, an **exponential moving average** `y += (x - y) >> k` needs no buffer at all.

### How do you find the maximum subarray sum (Kadane's algorithm)? {M}
Track the best sum ending at the current element and the best overall:

```c
int max_sub(const int *a, size_t n)
{
    int cur = a[0], best = a[0];
    for (size_t i = 1; i < n; i++) {
        cur = (a[i] > cur + a[i]) ? a[i] : cur + a[i];
        if (cur > best) best = cur;
    }
    return best;
}
```

O(n) time and O(1) memory, which also handles arrays of all negative numbers.
