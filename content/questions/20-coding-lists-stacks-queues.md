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
**Short answer:** A singly linked list is a chain of nodes, each holding a value and a pointer to the next node, with the last node pointing to NULL. Inserting at the front creates a node, points it at the current head and makes it the new head: O(1). Inserting at the end walks to the last node's `next` pointer and stores the new node there: O(n), or O(1) if you keep a tail pointer.

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

**Why `node_t **head`:** C passes arguments by value. If the function received `node_t *head`, assigning a new head would only change its local copy; the caller's list would still start at the old node (or stay NULL when the list was empty).

**The pointer-to-pointer walk in `push_back`:** `pp` points at "the link that should receive the new node" — first the caller's `head` variable, then each node's `next` field. When `*pp` is NULL, that link is the end of the list, whether the list was empty or not, so no special case is needed.

**Dry run:** start empty → `push_back(&h, 1)` sets `h` → [1]; `push_front(&h, 0)` → [0] → [1]; `push_back(&h, 2)` → [0] → [1] → [2].

**Printing and freeing (always mention freeing)**

```c
void print_list(const node_t *h) { for (; h; h = h->next) printf("%d -> ", h->val); puts("NULL"); }

void free_list(node_t **head)
{
    node_t *n = *head;
    while (n) { node_t *next = n->next; free(n); n = next; }   /* save next before free */
    *head = NULL;
}
```

**Embedded variant:** allocate nodes from a fixed array pool with a free list (O(1), no fragmentation, no `malloc` failures at run time).

**Insert after a given node** is O(1): `n->next = pos->next; pos->next = n;` — order matters, otherwise the rest of the list is lost.

#### Complete list lifetime

```c
void destroy_list(node_t **head)
{
    while (*head) {
        node_t *dead = *head;
        *head = dead->next;
        free(dead);
    }
}
```

Starting with NULL, push_front(10), push_back(20), push_front(5) produces 5 → 10 → 20 → NULL. Destroying the list leaves head equal to NULL. If a tail is maintained for O(1) appending, deletion of the last node must also update it. Nodes must be exclusively owned by the list or follow a documented sharing protocol.

### Delete a node with a given value from a singly linked list. {E}
**Short answer:** Walk the list with a pointer to the link that points at the current node (`node_t **pp`). When `(*pp)->val` matches, make the link skip the node (`*pp = node->next`) and free the node. Using the pointer-to-pointer means deleting the head needs no special case. O(n) time, O(1) space.

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

**Dry run: delete 3 from [1] → [3] → [5]**

1. `pp = &head`, `*pp` is node 1 → no match → `pp = &node1->next`.
2. `*pp` is node 3 → match → `node1->next = node3->next` (node 5), free node 3.
3. Result: [1] → [5].

**Deleting the head:** `pp` is `&head`, so `*pp = head->next` updates the caller's head directly.

**Version with a `prev` pointer (what many people write first)**

```c
node_t *cur = *head, *prev = NULL;
while (cur && cur->val != key) { prev = cur; cur = cur->next; }
if (!cur) return -1;                 /* not found */
if (prev) prev->next = cur->next;    /* middle or end */
else      *head = cur->next;         /* head node: special case */
free(cur);
```

**Edge cases to state:** empty list, key not found, key at head, key at tail, deleting all occurrences (continue the loop without advancing `pp` after a deletion), and saving `next` before calling `free`.

**Doubly linked lists** delete in O(1) given the node, because the node knows its predecessor.

#### Pointer-to-pointer trace

For head → 10 → 20 → 30, pp first points to head. After advancing, pp points to the next member of node 10. Deleting 20 changes that member directly to point to 30. If deleting 10, pp instead points to head, so the same assignment updates the caller's head. Save the old node, unlink, then free. To delete every match rather than the first, continue from the same pp after deletion.

### Delete a node when you are given only a pointer to that node (no head). {M}
**Short answer:** You cannot reach the previous node, so instead of removing this node you copy the **next** node's value (and next pointer) into it and free the next node. The list then looks as if the given node was deleted. This trick fails for the last node, which has no next node to copy from.

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

**Dry run:** list [4] → [5] → [1] → [9], given pointer to 5.
- Copy node 1 into node 5: node holds value 1, next = node 9.
- Free the old node 1.
- List is now [4] → [1] → [9].

**Why it is a trick, not a real deletion**

- The **identity** of the node changes: any other pointer that referred to the original "1" node is now dangling, and anything pointing at the "5" node now sees value 1. In systems with external references (e.g. intrusive lists, handles) this is dangerous.
- It copies the payload, which can be expensive for big nodes.
- It cannot delete the tail (common follow-up: mark it as a sentinel/dummy, or say the problem guarantees it is not the tail).

**What to say in an interview:** explain the trick, then mention that in real code you use a doubly linked list (O(1) removal with the node's own `prev`) or keep a pointer to the predecessor.

### Find the nth node from the end of a linked list (and remove it). {E}
**Short answer:** Use two pointers: move the first one n nodes ahead, then move both one step at a time until the first reaches the end. The second pointer is then n nodes from the end. To remove that node, start both from a dummy node in front of the head so the second pointer stops just **before** the target. One pass, O(n) time, O(1) space.

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

**Dry run: remove the 2nd from the end of [1] → [2] → [3] → [4] → [5]**

1. `dummy → 1 → 2 → 3 → 4 → 5`; `fast` and `slow` start at dummy.
2. Move `fast` n + 1 = 3 steps: fast at node 3.
3. Move both until `fast` is NULL: fast 3→4→5→NULL; slow dummy→1→2→3.
4. `slow` (node 3) is just before the target (node 4): `slow->next = slow->next->next`.
5. Result: 1 → 2 → 3 → 5.

**Why the dummy node:** if n equals the list length, the head itself is removed; with a dummy in front, the "previous node" always exists, so no special case.

**Validation:** if n is larger than the length, `fast` becomes NULL during the first loop — return an error instead of dereferencing NULL.

**Two-pass alternative:** count the length L, then walk to node L − n. Equally O(n), but it reads the list twice; interviewers usually want the one-pass version.

**Related problems using the same "gap" idea:** find the middle (fast moves 2, slow moves 1), rotate a list right by k (find the k-th from the end, cut and reconnect), and check if a list has at least k nodes.

### Merge two sorted linked lists. {E}
**Short answer:** Use a dummy node and a tail pointer. Repeatedly compare the heads of the two lists, link the smaller node after the tail and advance in that list; when one list runs out, link the rest of the other list. No new nodes are allocated — the existing nodes are relinked. O(n + m) time, O(1) space.

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

**Dry run: [1 → 3 → 5] and [2 → 4 → 6]**

| compare | take | merged so far |
|---|---|---|
| 1 vs 2 | 1 | 1 |
| 3 vs 2 | 2 | 1 2 |
| 3 vs 4 | 3 | 1 2 3 |
| 5 vs 4 | 4 | 1 2 3 4 |
| 5 vs 6 | 5 | 1 2 3 4 5 |
| a empty | rest of b | 1 2 3 4 5 6 |

**Stability:** taking from the first list when values are equal (`<=`) keeps equal elements in their original relative order.

**Recursive version (short but uses O(n + m) stack)**

```c
node_t *merge_rec(node_t *a, node_t *b)
{
    if (!a) return b;
    if (!b) return a;
    if (a->val <= b->val) { a->next = merge_rec(a->next, b); return a; }
    b->next = merge_rec(a, b->next); return b;
}
```

Mention that the iterative version is preferred on embedded targets because of stack limits.

**Follow-ups:** merge k sorted lists (min-heap of the k heads: O(N log k), or pairwise merging), merge sort for linked lists (split with slow/fast, sort halves, merge), and merging two sorted arrays from the back into the larger array (O(1) extra space).

### Remove duplicates from a sorted linked list. {E}
**Short answer:** In a sorted list, equal values are next to each other. Walk the list and, whenever the next node has the same value as the current one, unlink and free the next node; otherwise move forward. One pass, O(n) time, O(1) space.

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

**Dry run: [1 → 1 → 2 → 3 → 3]**

| current | next | action |
|---|---|---|
| 1 | 1 | remove next → 1 → 2 → 3 → 3 |
| 1 | 2 | advance |
| 2 | 3 | advance |
| 3 | 3 | remove next → 1 → 2 → 3 |
| 3 | NULL | stop |

**Important detail:** after removing a duplicate, do **not** advance — the new next node may also be a duplicate (e.g. 1 → 1 → 1).

**Variants**

- **Remove all nodes that have duplicates** (keep only distinct values: 1 → 2 → 3 → 3 → 4 becomes 1 → 2 → 4): use a dummy head and skip whole runs.
- **Unsorted list:** use a hash set / bitmap of values already seen (O(n) time, O(n) memory), or for each node scan the rest of the list (O(n²) time, O(1) memory), or sort first (merge sort, O(n log n)).
- **Arrays:** the same two-pointer idea compacts a sorted array in place and returns the new length.

### Reverse a linked list in groups of k. {H}
**Short answer:** Process the list one block of k nodes at a time: first check that k nodes remain (otherwise leave the tail as it is), reverse the links inside the block, then connect the node before the block to the block's new first node and the block's new last node to the next block. A dummy node in front of the head removes the special case for the first block. O(n) time, O(1) space.

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

**Dry run: 1 → 2 → 3 → 4 → 5, k = 2**

| group | before | after reversing | list |
|---|---|---|---|
| 1st (1,2) | dummy → 1 → 2 → 3 | dummy → 2 → 1 → 3 | 2 1 3 4 5 |
| 2nd (3,4) | 1 → 3 → 4 → 5 | 1 → 4 → 3 → 5 | 2 1 4 3 5 |
| 3rd (5) | only 1 node < k | unchanged | 2 1 4 3 5 |

**Key pointers in each round**

- `group_prev`: the node just before the group (dummy at first).
- `kth`: the last node of the group (becomes its first node after reversal).
- `group_next`: the node after the group; reversal starts with `prev = group_next` so the reversed group's tail automatically links to the rest.
- After reversal, the group's original first node becomes `group_prev` for the next round.

**Common mistakes:** reversing a final partial group (read the problem: some versions want it reversed too), losing `group_next` before the reversal, and forgetting to reconnect `group_prev->next`.

**Related:** reverse nodes between positions m and n, swap nodes in pairs (k = 2), and rotate a list by k.

### Find the intersection point of two linked lists. {M}
**Short answer:** Walk two pointers, one per list; when a pointer reaches the end of its list, restart it at the head of the **other** list. Both pointers then travel the same total distance (length A + length B), so they arrive at the intersection node at the same moment — or both reach NULL together if the lists do not intersect. O(n + m) time, O(1) space.

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

**Picture**

```
A: a1 → a2 ↘
             c1 → c2 → c3
B: b1 → b2 → b3 ↗
```

Lengths: A has 2 unique + 3 shared = 5, B has 3 unique + 3 shared = 6.
- Pointer p walks a1 a2 c1 c2 c3, then b1 b2 b3 → reaches c1 after 2 + 3 + 3 = 8 steps.
- Pointer q walks b1 b2 b3 c1 c2 c3, then a1 a2 → reaches c1 after 3 + 3 + 2 = 8 steps.
- They meet at c1.

**"Intersection" means the same node in memory**, not equal values: after the intersection the lists share every node, which is why we compare pointers.

**Length-difference method (easy to explain)**

1. Compute lengths `la` and `lb`.
2. Advance the longer list's pointer by `|la − lb|`.
3. Move both together until they are equal.

**Other approaches:** store all nodes of A in a hash set and look up B's nodes (O(n) memory); temporarily connect A's tail to B's head and use Floyd's loop detection to find the cycle start (modifies the lists, so restore them).

**Embedded relevance:** detecting shared buffers or descriptor chains, and debugging corrupted free lists where two chains merge unexpectedly.

### Check whether a linked list is a palindrome. {M}
**Short answer:** Find the middle with slow/fast pointers, reverse the second half in place, compare the first half with the reversed second half node by node, then reverse the second half back to restore the list. O(n) time and O(1) extra space.

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

**Dry run: 1 → 2 → 3 → 2 → 1**

1. slow stops at 3 (middle), fast reaches the end.
2. Reverse from 3: second half becomes 1 → 2 → 3.
3. Compare first half 1, 2, 3… with 1, 2, 3 → all equal → palindrome. (For odd lengths the middle node is compared with itself, which is harmless.)
4. Reverse the second half again so the caller's list is unchanged.

**Even length 1 → 2 → 2 → 1:** slow stops at the second 2; the reversed second half is 1 → 2; comparison 1 = 1, 2 = 2 → palindrome.

**Simpler alternatives (more memory)**

| Method | Space |
|---|---|
| Copy values into an array and compare from both ends | O(n) |
| Push the first half onto a stack, pop while walking the second half | O(n/2) |
| Recursion that compares on the way back | O(n) stack |
| Reverse half in place (above) | O(1) |

**Point interviewers like:** restoring the list (functions that only "check" something should not leave the data modified), and being careful in multithreaded code — the list is temporarily broken while it is reversed, so hold a lock.

### Detect and remove a loop in a linked list. {M}
**Short answer:** Detect the loop with Floyd's tortoise and hare (slow moves 1, fast moves 2; they meet only if there is a loop). Then move one pointer back to the head and advance both one step at a time: they meet at the first node of the loop. Stop one step earlier — when their `next` pointers are equal — so the pointer inside the loop is at the loop's last node, and set its `next` to NULL. O(n) time, O(1) space.

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

**Dry run: 1 → 2 → 3 → 4 → 5 → (back to 3)**

1. Floyd: slow 1,2,3,4,5,3… fast 1,3,5,4,3,5… → they meet at node 4 (for example).
2. Reset slow to the head (1). Advance both until `slow->next == fast->next`:
   - slow 1, fast 4: next are 2 and 5 → continue
   - slow 2, fast 5: next are 3 and 3 → stop.
3. `fast` (node 5) is the last node of the loop → `fast->next = NULL`.
4. List: 1 → 2 → 3 → 4 → 5 → NULL.

**Why the special case for a loop starting at the head:** if the loop begins at node 1, slow (reset to the head) and fast meet immediately at the head, and the `next`-comparison trick does not find the predecessor; walk `fast` around the loop until `fast->next == head` instead.

**Simpler-to-explain alternative:** after detecting the meeting point, count the loop length λ (walk until back at the meeting node), then start two pointers at the head with one λ nodes ahead; when the leading pointer's `next` equals the trailing pointer, cut there.

**Other methods:** a hash set of visited nodes (O(n) memory; the first repeated node is the loop start), or marking nodes with a visited flag (needs a spare field).

### Implement a doubly linked list with insert and delete. {E}
**Short answer:** Each node has `prev` and `next` pointers, so you can walk in both directions and delete a node in O(1) when you have a pointer to it. Insertion and deletion must update up to four pointers (the node's own two and the neighbours' links), and must update the head (and tail) when the node is at an end.

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

**Insert after node `pos` (order matters)**

```c
n->prev = pos;
n->next = pos->next;
if (pos->next) pos->next->prev = n;
pos->next = n;
```

**Delete node `n`**

```c
if (n->prev) n->prev->next = n->next; else *head = n->next;   /* n was the head */
if (n->next) n->next->prev = n->prev;                         /* else n was the tail */
free(n);
```

**Dry run:** list A ⇄ B ⇄ C, delete B → A.next = C and C.prev = A → A ⇄ C.

**Singly vs doubly linked**

| | Singly | Doubly |
|---|---|---|
| Memory per node | 1 pointer | 2 pointers |
| Delete given the node | O(n) (need predecessor) | O(1) |
| Traverse backwards | no | yes |
| Pointer updates per operation | fewer | more (more room for bugs) |

**Making it simpler:** a **circular doubly linked list with a sentinel head** (like Linux `list_head`) has no NULL pointers at all: an empty list is a head pointing to itself, and insert/delete have no special cases.

**Uses:** LRU caches (move a node to the front in O(1)), RTOS ready lists and timer lists, undo/redo history, and any queue where items are removed from the middle.

### Implement a circular linked list. {E}
**Short answer:** In a circular linked list the last node points back to the first instead of NULL, so you can keep going around forever. It is convenient for round-robin scheduling and rotating buffers. Keeping a pointer to the **tail** (rather than the head) is a common trick: the head is `tail->next`, so both inserting at the front and at the end are O(1).

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

**Traversal must stop when you return to the start (not at NULL)**

```c
void print_circular(const node_t *tail)
{
    if (!tail) { puts("empty"); return; }
    const node_t *p = tail->next;           /* head */
    do { printf("%d ", p->val); p = p->next; } while (p != tail->next);
    putchar('\n');
}
```

A `while (p != NULL)` loop on a circular list never ends — the classic bug.

**O(1) inserts with a tail pointer**

- Insert at the front: `n->next = tail->next; tail->next = n;`
- Insert at the end: do the same, then `tail = n;`
- Empty list: `n->next = n; tail = n;`

**Dry run:** insert 1, 2, 3 at the end → tail = 3, 3 → 1 → 2 → 3 (back to 1).

**Uses:** round-robin scheduling among tasks of equal priority, the Josephus problem (remove every k-th node until one remains), multiplayer turn order, and circular playlists. Note that ring **buffers** (arrays with wrapping indices) are usually better than circular **lists** for data streams.

**Detecting whether a list is circular:** Floyd's algorithm or check whether walking from the head returns to the head.

### Implement a Linux-style intrusive doubly linked list (list_head). {H}
**Short answer:** Embed a small `struct list_head { next, prev }` inside each object instead of allocating separate list nodes. The list is circular with a sentinel head (an empty list points to itself), so `list_add` and `list_del` are a few pointer assignments with no special cases, and `container_of` gets back from the embedded `list_head` to the containing object. Objects can be on several lists at once by embedding several `list_head` members.

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

**Core operations (as in `include/linux/list.h`)**

| Function | Effect |
|---|---|
| `INIT_LIST_HEAD(h)` | `h->next = h->prev = h` (empty list) |
| `list_add(new, head)` | insert right after `head` (stack/LIFO order) |
| `list_add_tail(new, head)` | insert before `head`, i.e. at the end (queue/FIFO order) |
| `list_del(entry)` | link `entry->prev` and `entry->next` together; poison the entry's pointers |
| `list_empty(head)` | `head->next == head` |
| `list_for_each(pos, head)` | `for (pos = head->next; pos != head; pos = pos->next)` |
| `list_entry(ptr, type, member)` | `container_of(ptr, type, member)` |
| `list_for_each_entry_safe(pos, n, head, member)` | iterate while deleting the current entry |

**How `container_of` works:** the address of the containing struct = address of the member − `offsetof(type, member)`. For `struct task { int id; struct list_head node; }` with `node` at offset 4, a `list_head` at 0x20001004 belongs to the task at 0x20001000.

**Why delete during iteration needs the `_safe` variant:** after `list_del(pos)` (and freeing `pos`), `pos->next` is no longer valid; the safe version saves `n = pos->next` before the loop body runs.

**Advantages over a generic list of `void *`:** no separate node allocation (works with static objects), type-safe access through `container_of`, better cache locality, and O(1) removal of any object without searching.

**Poisoning:** Linux sets deleted pointers to `LIST_POISON1/2` so a use after deletion faults immediately instead of corrupting memory.

### Implement a stack using an array and using a linked list. {E}
**Short answer:** A stack is last-in, first-out. With an **array**, keep a `top` index: push stores at `a[top++]` (fail if full), pop returns `a[--top]` (fail if empty). With a **linked list**, push inserts at the head and pop removes the head. Both give O(1) push and pop; the array is fixed-size and cache-friendly, the list grows dynamically but needs allocation per element.

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

**Dry run:** push 1, push 2, push 3 → top = 3; pop → 3, pop → 2; push 9 → stack [1, 9].

**Array vs linked list**

| | Array stack | Linked-list stack |
|---|---|---|
| Capacity | fixed (or grow with realloc) | limited only by memory |
| Push/pop | O(1) | O(1) |
| Memory per item | item only | item + pointer + allocator overhead |
| Failure mode | overflow when full | `malloc` failure |
| Embedded preference | yes (static array) | rarely |

**Edge cases to handle explicitly:** pop/peek on an empty stack (underflow) and push on a full stack (overflow) — return an error code rather than reading garbage or writing past the array.

**Stack applications interviewers like:** balanced brackets (push opening, pop and match on closing), undo history, expression evaluation (infix → postfix, postfix evaluation), iterative depth-first search, converting recursion to iteration (useful on MCUs with small stacks), and reversing a sequence.

**Balanced parentheses in a few lines**

```c
#include <stdbool.h>

bool balanced(const char *s)
{
    char st[64]; int top = 0;
    for (; *s; s++) {
        if (*s == '(' || *s == '[' || *s == '{') { if (top == 64) return false; st[top++] = *s; }
        else if (*s == ')' || *s == ']' || *s == '}') {
            char open = (*s == ')') ? '(' : (*s == ']') ? '[' : '{';
            if (top == 0 || st[--top] != open) return false;
        }
    }
    return top == 0;                  /* leftover openers mean unbalanced */
}
```

### Implement a queue using an array (circular queue) and using a linked list. {E}
**Short answer:** A queue is first-in, first-out. With an **array**, use a circular buffer: `head` is where you dequeue, `tail` where you enqueue, both wrap around with modulo (or a mask for power-of-two sizes), and a `count` (or one empty slot) distinguishes full from empty. With a **linked list**, keep both a head and a tail pointer: enqueue appends at the tail and dequeue removes from the head. Both are O(1).

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

**Why "circular":** a plain array queue that only moves `head` forward wastes the space before `head` and eventually runs out even if it is nearly empty. Wrapping the indices reuses that space.

**Dry run (capacity 3)**

| operation | head | tail | count | contents |
|---|---|---|---|---|
| enq 1 | 0 | 1 | 1 | [1 _ _] |
| enq 2 | 0 | 2 | 2 | [1 2 _] |
| deq → 1 | 1 | 2 | 1 | [_ 2 _] |
| enq 3 | 1 | 0 | 2 | [_ 2 3] |
| enq 4 | 1 | 1 | 3 | [4 2 3] (wrapped) |
| enq 5 | — | — | 3 | full → error |

**Full vs empty without a count:** `head == tail` means empty; reserve one slot so full is `(tail + 1) % N == head` (wastes one element), or use free-running indices with a power-of-two size (`tail - head == N` means full).

**Linked-list queue pitfall:** when dequeuing the last element, set `tail = NULL` as well; otherwise the next enqueue writes through a dangling tail pointer.

**Embedded use:** UART RX/TX buffers, event queues between ISRs and the main loop, command queues. When one side runs in an ISR, see the lock-free SPSC ring buffer in the Embedded Drivers coding topic.

**Deque:** allow insert/remove at both ends with the same circular array (decrement `head` with wrap for push-front).

### Implement two stacks in one array. {E}
**Short answer:** Grow the first stack from the left end (index 0 upwards) and the second from the right end (index n − 1 downwards). The array is full only when the two tops meet, so neither stack overflows while there is free space anywhere in the array. Push and pop are O(1).

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

**Layout**

```
index:  0   1   2   3   4   5   6   7
       [a1][a2][a3][ ][ ][ ][b2][b1]
            top1 = 3 →      ← top2 = 6
full when top1 == top2 + 1 (or top1 > top2 with inclusive indices)
```

**Dry run (n = 5):** push1 A, push1 B (top1 = 2), push2 X, push2 Y (top2 = 2 going down from 4 → 3 → 2)… one more push to either stack fails because the free region is empty.

**Why not split the array in half?** A fixed split wastes space: stack 1 could overflow while stack 2's half is empty. Growing towards each other uses the whole array.

**Extension — k stacks in one array:** keep `top[k]` and a `next[]` array that links free slots and stacked elements (each slot is either in a stack or in the free list): O(1) push/pop with full sharing.

**Real-world analogy:** a classic process memory layout uses the same idea — the heap grows upward and the stack grows downward towards each other, with a collision meaning out of memory.

### Implement a queue using two stacks. {M}
**Short answer:** Use an **in** stack for enqueue and an **out** stack for dequeue. Enqueue pushes onto `in`. Dequeue pops from `out`; if `out` is empty, first move every element from `in` to `out`, which reverses their order so the oldest element ends up on top. Each element is moved at most once, so operations are O(1) amortised.

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

**Dry run**

| operation | in (bottom→top) | out (bottom→top) | result |
|---|---|---|---|
| enq 1, 2, 3 | 1 2 3 | — | |
| deq | — | 3 2 1 (moved) | 1 |
| enq 4 | 4 | 3 2 | |
| deq | 4 | 3 | 2 |
| deq | 4 | — | 3 |
| deq | — | 4 (moved) | 4 |

**Why amortised O(1):** a single dequeue can cost O(n) when it moves everything, but every element is pushed onto `in` once, moved once, and popped from `out` once — at most 3 operations per element over its lifetime.

**Common mistake:** moving elements back and forth on every operation (O(n) each time), or moving from `in` to `out` when `out` is **not** empty (breaks FIFO order).

**Reverse problem — stack using queues:** push into a queue, then rotate the earlier elements behind it (n − 1 dequeue/enqueue operations) so the newest element is at the front: push O(n), pop O(1).

**Why interviewers ask:** to test amortised analysis and thinking in terms of invariants ("the front of the queue is always the top of `out` when `out` is non-empty").

### Implement a min stack (getMin in O(1)). {M}
**Short answer:** Keep a second stack that stores, at each level, the minimum of all elements at or below that level. On push, push `min(value, current minimum)` onto the min stack; on pop, pop both stacks. `getMin` simply reads the top of the min stack. Every operation is O(1).

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

**Dry run**

| operation | stack | min stack | getMin |
|---|---|---|---|
| push 5 | 5 | 5 | 5 |
| push 3 | 5 3 | 5 3 | 3 |
| push 7 | 5 3 7 | 5 3 3 | 3 |
| push 2 | 5 3 7 2 | 5 3 3 2 | 2 |
| pop | 5 3 7 | 5 3 3 | 3 |
| pop | 5 3 | 5 3 | 3 |

**Why it works:** the minimum of the stack only changes when the top changes; storing "the minimum so far" at each level means popping automatically restores the previous minimum.

**Memory optimisation:** push onto the min stack only when the new value is `<=` the current minimum, and pop from it only when the popped value equals its top (the `<=` keeps duplicates of the minimum correct).

**One-stack trick (O(1) extra space):** store `2 * value - min` when a new minimum is pushed and recover the old minimum on pop — clever but overflow-prone; mention it, do not rely on it.

**Related:** max stack (same idea), sliding-window maximum (monotonic deque: O(n) for all windows), and queue with getMin using two min stacks.

### Convert an infix expression to postfix (shunting-yard). {M}
**Short answer:** Use Dijkstra's shunting-yard algorithm: read tokens left to right; send operands straight to the output; push `(` onto an operator stack; on `)` pop operators to the output until the matching `(`; for an operator, first pop operators of higher precedence (or equal precedence for left-associative operators) to the output, then push it. At the end, pop the remaining operators. O(n) time.

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

**Dry run: `a + b * (c - d)`**

| token | action | output | stack |
|---|---|---|---|
| a | output | a | |
| + | push | a | + |
| b | output | a b | + |
| * | `*` > `+`, push | a b | + * |
| ( | push | a b | + * ( |
| c | output | a b c | + * ( |
| - | push (inside parentheses) | a b c | + * ( - |
| d | output | a b c d | + * ( - |
| ) | pop until ( | a b c d - | + * |
| end | pop all | a b c d - * + | |

Result: `a b c d - * +`.

**Precedence and associativity rules**

| Operator | Precedence | Associativity |
|---|---|---|
| `^` | 3 | right (`2^3^2` = `2^(3^2)`) |
| `*` `/` `%` | 2 | left |
| `+` `-` | 1 | left |

For a left-associative operator, pop while the stack top has precedence **≥**; for right-associative, pop while **>**.

**Why postfix:** it needs no parentheses or precedence rules to evaluate — a single left-to-right pass with a stack (next question). Calculators, compilers and expression evaluators in configuration languages use this.

**Error handling to mention:** mismatched parentheses (stack empty when `)` arrives, or `(` left at the end), unary minus (treat as a separate operator), and multi-digit numbers (tokenise first).

### Evaluate a postfix expression. {E}
**Short answer:** Read tokens left to right with a value stack: push each number; for an operator, pop the right operand first, then the left operand, apply the operator and push the result. At the end exactly one value must remain — that is the answer. O(n) time, O(n) stack space.

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

**Dry run: `2 3 4 * + 5 -`** (= 2 + 3 × 4 − 5)

| token | stack after |
|---|---|
| 2 | 2 |
| 3 | 2 3 |
| 4 | 2 3 4 |
| * | 2 12 |
| + | 14 |
| 5 | 14 5 |
| - | 9 |

**Order matters:** for `8 2 -`, pop `b = 2` then `a = 8` and compute `a - b = 6`. Swapping them gives −6 — the most common bug.

**Errors to detect:** an operator with fewer than two values on the stack (malformed expression), more than one value left at the end, division by zero, stack overflow for a fixed-size stack, and integer overflow.

**Prefix (Polish) notation:** evaluate right to left with the same stack method.

**Where it appears in embedded work:** RPN calculators, Forth-like scripting and bytecode interpreters (stack machines such as the JVM or WebAssembly), and configurable formulas for sensor scaling stored as postfix tokens in EEPROM.

### Implement an LRU cache. {H}
**Short answer:** Combine a **hash map** (key → node, for O(1) lookup) with a **doubly linked list** ordered by recency (most recently used at the front). `get` finds the node, moves it to the front and returns its value. `put` updates an existing node and moves it to the front, or, for a new key, evicts the node at the back if the cache is full, then inserts the new node at the front. Both operations are O(1).

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

**Dry run (capacity 2)**

| operation | list (front → back) | result |
|---|---|---|
| put(1, A) | 1 | |
| put(2, B) | 2 1 | |
| get(1) | 1 2 | A |
| put(3, C) | 3 1 (evict 2, the least recently used) | |
| get(2) | 3 1 | miss |
| get(3) | 3 1 | C |

**Why both structures:** the list alone needs O(n) to find a key; the hash map alone does not know which entry is the oldest. The map points into the list, and the list's nodes store their key so the evicted node's map entry can be removed.

**Embedded implementation notes**

- Use a fixed array of nodes (no `malloc`) and an open-addressing hash table of indices; the "linked list" can use 16-bit indices instead of pointers to save RAM.
- For very small caches (e.g. 4–8 entries), a linear search with a timestamp or age counter per entry is simpler and fast enough.
- In hardware, caches use "pseudo-LRU" (tree bits) because exact LRU is expensive for many ways.

**Where LRU is used:** CPU caches and TLBs (approximations), page replacement in operating systems (clock algorithm approximates LRU), DNS caches, flash translation layers (which logical block to keep mapped), and file system buffer caches.

**Follow-ups:** thread safety (one lock around the whole cache, or sharding), LFU (least frequently used) as an alternative, and TTL-based expiry.
