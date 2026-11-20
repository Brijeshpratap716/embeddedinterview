---
slug: coding-lists-stacks-queues
title: "Coding: Linked Lists, Stacks & Queues"
icon: 🔗
level: Intermediate
order: 20
desc: Every linked-list operation interviewers ask (insert, delete, nth from end, merge, k-group reverse, intersection, loop removal), Linux-style list_head, stacks, queues, min stack, infix to postfix and an LRU cache in C.
---
Linked-list and stack/queue questions check pointer handling under pressure: NULL checks, the empty list, a one-element list, and not losing the rest of the list while rewiring pointers. Each answer is compact C that was compiled and tested, plus what to say about complexity and edge cases. See the Data Structures topic for reversal, loop detection and ring buffers.

### Create a singly linked list and insert at the beginning and the end. {E}
```c
#include <stdlib.h>

typedef struct node { int val; struct node *next; } node_t;

node_t *new_node(int v)
{
    node_t *n = malloc(sizeof *n);
    if (n) { n->val = v; n->next = NULL; }
    return n;
}

int push_front(node_t **head, int v)              /* O(1) */
{
    node_t *n = new_node(v);
    if (!n) return -1;
    n->next = *head;
    *head = n;
    return 0;
}

int push_back(node_t **head, int v)               /* O(n); keep a tail pointer for O(1) */
{
    node_t *n = new_node(v);
    if (!n) return -1;
    node_t **pp = head;
    while (*pp) pp = &(*pp)->next;                /* walk to the last next-pointer */
    *pp = n;
    return 0;
}
```

**Points:** pass `node_t **head` so the function can change the head; the pointer-to-pointer walk removes the special case for an empty list; check `malloc` failure; keep a tail pointer if appends are frequent. On an MCU, nodes usually come from a static pool instead of `malloc`.

### Delete a node with a given value from a singly linked list. {E}
```c
int delete_value(node_t **head, int v)
{
    for (node_t **pp = head; *pp; pp = &(*pp)->next) {
        if ((*pp)->val == v) {
            node_t *dead = *pp;
            *pp = dead->next;                     /* unlink: works for head and inner nodes */
            free(dead);
            return 0;
        }
    }
    return -1;                                    /* not found */
}
```

**Points:** the double-pointer technique avoids tracking `prev` and special-casing the head; free the node after unlinking; return a status if not found. To delete all matches, do not advance `pp` after a deletion.

### Delete a node when you are given only a pointer to that node (no head). {M}
```c
/* copies the next node into this one and frees the next node */
int delete_given_node(node_t *n)
{
    if (n == NULL || n->next == NULL) return -1;  /* cannot delete the last node this way */
    node_t *next = n->next;
    n->val = next->val;
    n->next = next->next;
    free(next);
    return 0;
}
```

**Points:** you cannot find the previous node, so copy the successor's data into this node and remove the successor instead. It does not work for the tail, and it breaks if other code holds pointers to the successor node (its identity changes), which is why it is a trick, not a general technique.

### Find the nth node from the end of a linked list (and remove it). {E}
```c
/* returns the nth node from the end (n = 1 is the last), or NULL */
node_t *nth_from_end(node_t *head, unsigned n)
{
    node_t *lead = head, *trail = head;
    for (unsigned i = 0; i < n; i++) {
        if (!lead) return NULL;                   /* list shorter than n */
        lead = lead->next;
    }
    while (lead) { lead = lead->next; trail = trail->next; }
    return trail;
}

void remove_nth_from_end(node_t **head, unsigned n)
{
    node_t **pp = head, *lead = *head;
    for (unsigned i = 0; i < n; i++) { if (!lead) return; lead = lead->next; }
    while (lead) { lead = lead->next; pp = &(*pp)->next; }
    node_t *dead = *pp;
    *pp = dead->next;
    free(dead);
}
```

**Points:** two pointers `n` apart: when the leader falls off the end, the trailer is at the answer. One pass, O(1) space. Handle n larger than the list and n == length (removing the head).

### Merge two sorted linked lists. {E}
```c
node_t *merge_sorted(node_t *a, node_t *b)
{
    node_t dummy = { 0, NULL }, *tail = &dummy;
    while (a && b) {
        if (a->val <= b->val) { tail->next = a; a = a->next; }   /* <= keeps it stable */
        else                  { tail->next = b; b = b->next; }
        tail = tail->next;
    }
    tail->next = a ? a : b;                       /* append the remainder */
    return dummy.next;
}
```

**Points:** a dummy head node removes special cases; reuses the existing nodes (no allocation), O(n + m) time, O(1) space; this is the merge step of merge sort on lists.

### Remove duplicates from a sorted linked list. {E}
```c
void remove_dups_sorted(node_t *head)
{
    node_t *cur = head;
    while (cur && cur->next) {
        if (cur->val == cur->next->val) {
            node_t *dup = cur->next;
            cur->next = dup->next;
            free(dup);                            /* do not advance: next may also be a duplicate */
        } else {
            cur = cur->next;
        }
    }
}
```

**Points:** in a sorted list duplicates are adjacent: one pass, O(1) space. For an unsorted list, use a hash set or bitmap of seen values (O(n)) or nested loops (O(n²) without extra memory).

### Reverse a linked list in groups of k. {H}
```c
/* reverses each block of k nodes; a final block shorter than k is left as is */
node_t *reverse_k_group(node_t *head, int k)
{
    node_t dummy = { 0, head }, *group_prev = &dummy;
    for (;;) {
        node_t *kth = group_prev;
        for (int i = 0; i < k && kth; i++) kth = kth->next;
        if (!kth) break;                          /* fewer than k nodes left */
        node_t *group_next = kth->next;
        node_t *prev = group_next, *cur = group_prev->next;
        while (cur != group_next) {               /* standard reversal inside the group */
            node_t *nx = cur->next;
            cur->next = prev;
            prev = cur;
            cur = nx;
        }
        node_t *first = group_prev->next;         /* becomes the last node of the group */
        group_prev->next = kth;
        group_prev = first;
    }
    return dummy.next;
}
/* 1-2-3-4-5, k = 2 -> 2-1-4-3-5 */
```

**Points:** find the k-th node first so you know a full group exists; reverse within the group while linking its tail to the next group; reconnect the previous group. O(n) time, O(1) space.

### Find the intersection point of two linked lists. {M}
```c
node_t *intersection(node_t *a, node_t *b)
{
    node_t *p = a, *q = b;
    while (p != q) {
        p = p ? p->next : b;                      /* switch lists at the end */
        q = q ? q->next : a;
    }
    return p;                                     /* meeting node, or NULL if they never meet */
}
```

**Points:** after switching heads, both pointers travel `len(a) + len(b)` steps, so they line up at the intersection (or both become NULL at the same time). O(n + m), O(1) space. Alternative: compute both lengths, advance the longer list by the difference, then walk together. Compare **node addresses**, not values.

### Check whether a linked list is a palindrome. {M}
```c
#include <stdbool.h>

static node_t *reverse(node_t *h)
{
    node_t *prev = NULL;
    while (h) { node_t *n = h->next; h->next = prev; prev = h; h = n; }
    return prev;
}

bool is_palindrome_list(node_t *head)
{
    node_t *slow = head, *fast = head;
    while (fast && fast->next) { slow = slow->next; fast = fast->next->next; }
    node_t *second = reverse(slow), *p = head, *q = second;
    bool ok = true;
    while (q) { if (p->val != q->val) { ok = false; break; } p = p->next; q = q->next; }
    reverse(second);                              /* restore the list */
    return ok;
}
```

**Points:** find the middle with slow/fast pointers, reverse the second half, compare, and restore it (good manners: do not leave the caller's list modified). O(n) time, O(1) space.

### Detect and remove a loop in a linked list. {M}
```c
void remove_loop(node_t *head)
{
    node_t *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) break;
    }
    if (!fast || !fast->next) return;             /* no loop */

    slow = head;
    if (slow == fast) {                           /* loop starts at the head */
        while (fast->next != slow) fast = fast->next;
    } else {
        while (slow->next != fast->next) { slow = slow->next; fast = fast->next; }
    }
    fast->next = NULL;                            /* fast is the last node in the loop */
}
```

**Points:** Floyd's algorithm finds a meeting point; moving one pointer back to the head and advancing both one step at a time makes them meet at the loop's start (here we stop one node earlier so we can cut the link). Handle the case where the loop starts at the head. O(n), O(1) space.

### Implement a doubly linked list with insert and delete. {E}
```c
#include <stdlib.h>

typedef struct dnode { int val; struct dnode *prev, *next; } dnode_t;
typedef struct { dnode_t *head, *tail; } dlist_t;

int dlist_push_back(dlist_t *l, int v)
{
    dnode_t *n = malloc(sizeof *n);
    if (!n) return -1;
    n->val = v; n->next = NULL; n->prev = l->tail;
    if (l->tail) l->tail->next = n; else l->head = n;
    l->tail = n;
    return 0;
}

void dlist_remove(dlist_t *l, dnode_t *n)          /* O(1) given the node */
{
    if (n->prev) n->prev->next = n->next; else l->head = n->next;
    if (n->next) n->next->prev = n->prev; else l->tail = n->prev;
    free(n);
}
```

**Points:** removal is O(1) when you have the node (no search for the predecessor), which is why OS kernels use doubly linked lists for run queues and timers; the cost is an extra pointer per node. Update `head`/`tail` in the edge cases.

### Implement a circular linked list. {E}
```c
#include <stdio.h>
#include <stdlib.h>

/* keep a pointer to the TAIL: tail->next is the head, so both ends are O(1) */
int cl_push_back(node_t **tail, int v)
{
    node_t *n = malloc(sizeof *n);
    if (!n) return -1;
    n->val = v;
    if (*tail == NULL) n->next = n;               /* single node points to itself */
    else { n->next = (*tail)->next; (*tail)->next = n; }
    *tail = n;
    return 0;
}

void cl_print(const node_t *tail)
{
    if (!tail) return;
    const node_t *p = tail->next;                 /* head */
    do { printf("%d ", p->val); p = p->next; } while (p != tail->next);
    printf("\n");
}
```

**Points:** there is no NULL at the end, so traversal stops when you return to the start (`do ... while`); keeping a tail pointer gives O(1) insertion at both ends. Uses: round-robin scheduling lists, circular buffers of objects.

### Implement a Linux-style intrusive doubly linked list (list_head). {H}
```c
#include <stddef.h>

struct list_head { struct list_head *next, *prev; };

#define LIST_HEAD_INIT(name) { &(name), &(name) }
static inline void INIT_LIST_HEAD(struct list_head *h) { h->next = h; h->prev = h; }

static inline void __list_add(struct list_head *n, struct list_head *prev, struct list_head *next)
{
    next->prev = n; n->next = next; n->prev = prev; prev->next = n;
}
static inline void list_add(struct list_head *n, struct list_head *head)      { __list_add(n, head, head->next); }  /* at front */
static inline void list_add_tail(struct list_head *n, struct list_head *head) { __list_add(n, head->prev, head); }  /* at back */

static inline void list_del(struct list_head *e)
{
    e->next->prev = e->prev;
    e->prev->next = e->next;
    e->next = e->prev = NULL;                     /* the kernel poisons these instead */
}
static inline int list_empty(const struct list_head *h) { return h->next == h; }

#define container_of(ptr, type, member) ((type *)((char *)(ptr) - offsetof(type, member)))
#define list_entry(ptr, type, member) container_of(ptr, type, member)
#define list_for_each(pos, head) for (pos = (head)->next; pos != (head); pos = pos->next)
#define list_for_each_safe(pos, n, head) \
    for (pos = (head)->next, n = pos->next; pos != (head); pos = n, n = pos->next)

/* usage */
struct task { int id; struct list_head node; };
/* struct list_head ready = LIST_HEAD_INIT(ready);
   list_add_tail(&t->node, &ready);
   struct list_head *p; list_for_each(p, &ready) { struct task *t = list_entry(p, struct task, node); } */
```

**Points:** the list node is embedded **inside** the object, so no separate allocation per list entry, one object can be on several lists (several `list_head` members), and the same list code works for every type. The head is a sentinel in a circular list, so there are no NULL checks. `container_of` recovers the object. Use the `_safe` iterator when deleting while iterating.

### Implement a stack using an array and using a linked list. {E}
```c
#include <stdbool.h>
#include <stdlib.h>

/* array stack: fixed capacity, no allocation */
#define STACK_CAP 32
typedef struct { int data[STACK_CAP]; int top; } astack_t;   /* top = number of items */

bool as_push(astack_t *s, int v) { if (s->top == STACK_CAP) return false; s->data[s->top++] = v; return true; }
bool as_pop(astack_t *s, int *v) { if (s->top == 0) return false; *v = s->data[--s->top]; return true; }

/* linked-list stack: unbounded, push/pop at the head */
typedef struct snode { int v; struct snode *next; } snode_t;

bool ls_push(snode_t **top, int v)
{
    snode_t *n = malloc(sizeof *n);
    if (!n) return false;
    n->v = v; n->next = *top; *top = n;
    return true;
}

bool ls_pop(snode_t **top, int *v)
{
    if (!*top) return false;
    snode_t *n = *top; *v = n->v; *top = n->next; free(n);
    return true;
}
```

**Points:** check overflow and underflow and report them; the array version is deterministic and allocation-free (preferred on MCUs); the list version grows as needed but allocates per push. All operations are O(1).

### Implement a queue using an array (circular queue) and using a linked list. {E}
```c
#include <stdbool.h>
#include <stdlib.h>

/* circular array queue with an explicit count (no wasted slot) */
#define Q_CAP 8
typedef struct { int buf[Q_CAP]; unsigned head, count; } cqueue_t;

bool cq_push(cqueue_t *q, int v)
{
    if (q->count == Q_CAP) return false;                  /* full */
    q->buf[(q->head + q->count) % Q_CAP] = v;
    q->count++;
    return true;
}

bool cq_pop(cqueue_t *q, int *v)
{
    if (q->count == 0) return false;                      /* empty */
    *v = q->buf[q->head];
    q->head = (q->head + 1) % Q_CAP;
    q->count--;
    return true;
}

/* linked-list queue: enqueue at tail, dequeue at head */
typedef struct qn { int v; struct qn *next; } qn_t;
typedef struct { qn_t *head, *tail; } lqueue_t;

bool lq_push(lqueue_t *q, int v)
{
    qn_t *n = malloc(sizeof *n);
    if (!n) return false;
    n->v = v; n->next = NULL;
    if (q->tail) q->tail->next = n; else q->head = n;
    q->tail = n;
    return true;
}

bool lq_pop(lqueue_t *q, int *v)
{
    if (!q->head) return false;
    qn_t *n = q->head;
    *v = n->v;
    q->head = n->next;
    if (!q->head) q->tail = NULL;                         /* queue became empty */
    free(n);
    return true;
}
```

**Points:** in the circular queue, indexes wrap with `%` (or `& (CAP-1)` if CAP is a power of two); tracking `count` distinguishes full from empty (the alternative is leaving one slot empty). The linked-list version must reset `tail` when the queue empties. For an ISR producer and a task consumer, use the lock-free SPSC ring buffer in the embedded coding topic instead.

### Implement two stacks in one array. {E}
```c
#include <stdbool.h>

#define CAP 16
typedef struct { int a[CAP]; int top1, top2; } two_stacks_t;   /* top1 = -1, top2 = CAP initially */

void ts_init(two_stacks_t *s) { s->top1 = -1; s->top2 = CAP; }
bool ts_push1(two_stacks_t *s, int v) { if (s->top1 + 1 == s->top2) return false; s->a[++s->top1] = v; return true; }
bool ts_push2(two_stacks_t *s, int v) { if (s->top1 + 1 == s->top2) return false; s->a[--s->top2] = v; return true; }
bool ts_pop1(two_stacks_t *s, int *v) { if (s->top1 < 0) return false; *v = s->a[s->top1--]; return true; }
bool ts_pop2(two_stacks_t *s, int *v) { if (s->top2 == CAP) return false; *v = s->a[s->top2++]; return true; }
```

**Points:** grow one stack from each end towards the middle; the array is full only when the tops meet, so space is shared efficiently (better than splitting it in half). The same idea is the classic heap-grows-up / stack-grows-down memory layout.

### Implement a queue using two stacks. {M}
```c
/* uses the array stack from above */
typedef struct { astack_t in, out; } squeue_t;

bool sq_push(squeue_t *q, int v) { return as_push(&q->in, v); }

bool sq_pop(squeue_t *q, int *v)
{
    if (q->out.top == 0) {                       /* refill only when out is empty */
        int x;
        while (as_pop(&q->in, &x)) as_push(&q->out, x);
    }
    return as_pop(&q->out, v);
}
```

**Points:** pushing everything from `in` to `out` reverses the order, so the oldest element ends up on top of `out`. Each element moves at most twice, so operations are **amortised O(1)** (a single pop can be O(n)).

### Implement a min stack (getMin in O(1)). {M}
```c
#include <stdbool.h>

#define MS_CAP 32
typedef struct { int val[MS_CAP], min[MS_CAP]; int top; } minstack_t;

bool ms_push(minstack_t *s, int v)
{
    if (s->top == MS_CAP) return false;
    s->val[s->top] = v;
    s->min[s->top] = (s->top == 0 || v < s->min[s->top - 1]) ? v : s->min[s->top - 1];
    s->top++;
    return true;
}
bool ms_pop(minstack_t *s, int *v) { if (s->top == 0) return false; *v = s->val[--s->top]; return true; }
bool ms_min(const minstack_t *s, int *m) { if (s->top == 0) return false; *m = s->min[s->top - 1]; return true; }
```

**Points:** store, for each level, the minimum of everything at or below it; then the minimum is always at the top, O(1) for all operations at the cost of a second array. Space can be reduced by pushing to the min stack only when a new minimum (or equal) arrives.

### Convert an infix expression to postfix (shunting-yard). {M}
```c
#include <ctype.h>

static int prec(char op) { return (op == '+' || op == '-') ? 1 : (op == '*' || op == '/') ? 2 : 0; }

/* single-character operands, + - * / and parentheses; out must be large enough */
void infix_to_postfix(const char *in, char *out)
{
    char st[64]; int top = 0, k = 0;
    for (; *in; in++) {
        char c = *in;
        if (isalnum((unsigned char)c)) out[k++] = c;
        else if (c == '(') st[top++] = c;
        else if (c == ')') {
            while (top && st[top - 1] != '(') out[k++] = st[--top];
            if (top) top--;                                   /* discard '(' */
        } else if (prec(c)) {
            while (top && prec(st[top - 1]) >= prec(c))       /* >= : left-associative */
                out[k++] = st[--top];
            st[top++] = c;
        }
    }
    while (top) out[k++] = st[--top];
    out[k] = '\0';
}
/* "a+b*(c-d)" -> "abcd-*+" */
```

**Points:** operands go straight to the output; operators wait on a stack and are popped while the stack top has higher or equal precedence (use `>` for right-associative operators like `^`); parentheses group. Real versions handle multi-digit numbers, errors (unbalanced parentheses) and unary minus.

### Evaluate a postfix expression. {E}
```c
#include <ctype.h>

/* single-digit operands; returns 0 and sets *ok = 0 on error */
long eval_postfix(const char *s, int *ok)
{
    long st[64]; int top = 0;
    *ok = 1;
    for (; *s; s++) {
        if (isdigit((unsigned char)*s)) { st[top++] = *s - '0'; continue; }
        if (*s == ' ') continue;
        if (top < 2) { *ok = 0; return 0; }
        long b = st[--top], a = st[--top];               /* order matters for - and / */
        switch (*s) {
        case '+': st[top++] = a + b; break;
        case '-': st[top++] = a - b; break;
        case '*': st[top++] = a * b; break;
        case '/': if (b == 0) { *ok = 0; return 0; } st[top++] = a / b; break;
        default: *ok = 0; return 0;
        }
    }
    if (top != 1) { *ok = 0; return 0; }
    return st[0];
}
/* "231*+9-" -> 2 + 3*1 - 9 = -4 */
```

**Points:** push operands, pop two for each operator (the first popped is the **right** operand), push the result; at the end exactly one value must remain. Check stack underflow, division by zero and leftover values.

### Implement an LRU cache. {H}
```c
#include <stdbool.h>
#include <string.h>

/* fixed capacity, keys 0..MAX_KEY-1, O(1) get/put using an index table + doubly linked list */
#define CAPACITY 4
#define MAX_KEY  1024

typedef struct { int key, val, prev, next; } entry_t;    /* links are indexes into the pool */
typedef struct {
    entry_t e[CAPACITY];
    int where[MAX_KEY];          /* key -> slot index, or -1 */
    int head, tail, used;        /* head = most recent, tail = least recent */
} lru_t;

void lru_init(lru_t *c) { memset(c->where, -1, sizeof c->where); c->head = c->tail = -1; c->used = 0; }

static void unlink_e(lru_t *c, int i)
{
    entry_t *x = &c->e[i];
    if (x->prev >= 0) c->e[x->prev].next = x->next; else c->head = x->next;
    if (x->next >= 0) c->e[x->next].prev = x->prev; else c->tail = x->prev;
}
static void push_front_e(lru_t *c, int i)
{
    c->e[i].prev = -1; c->e[i].next = c->head;
    if (c->head >= 0) c->e[c->head].prev = i; else c->tail = i;
    c->head = i;
}

bool lru_get(lru_t *c, int key, int *val)
{
    int i = c->where[key];
    if (i < 0) return false;
    unlink_e(c, i); push_front_e(c, i);                    /* mark as most recently used */
    *val = c->e[i].val;
    return true;
}

void lru_put(lru_t *c, int key, int val)
{
    int i = c->where[key];
    if (i >= 0) { c->e[i].val = val; unlink_e(c, i); push_front_e(c, i); return; }
    if (c->used < CAPACITY) i = c->used++;
    else { i = c->tail; c->where[c->e[i].key] = -1; unlink_e(c, i); }   /* evict LRU */
    c->e[i].key = key; c->e[i].val = val; c->where[key] = i;
    push_front_e(c, i);
}
```

**Points:** a hash map (here a direct index table, since keys are small) finds an entry in O(1), and a doubly linked list keeps entries in recency order: move to front on every access, evict from the tail when full. With arbitrary keys, replace `where[]` with a hash table. Using indexes into a fixed pool instead of pointers makes it allocation-free for embedded use. Real uses: page caches, DNS caches, a cache of decoded fonts/images on a display device.
