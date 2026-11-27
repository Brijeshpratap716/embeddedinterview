---
slug: coding-lists-stacks-queues
title: "Coding: Linked Lists, Stacks & Queues"
icon: 🔗
level: Intermediate
order: 20
desc: Every linked-list operation interviewers ask (insert, delete, nth from end, merge, k-group reverse, intersection, loop removal), Linux-style list_head, stacks, queues, min stack, infix to postfix and an LRU cache in C.
---
Linked-list and stack/queue questions check pointer handling under pressure: NULL checks, the empty list, a one-element list, and not losing the rest of the list while rewiring pointers. Each answer is compact C that was compiled and tested, plus what to say about complexity and edge cases. See the Data Structures topic for reversal, loop detection and ring buffers.

### Singly Linked List in C – All Operations for Interview Preparation {E}

A linked list consists of nodes where each node contains data and a pointer to the next node.

`head → 10 → 20 → 30 → NULL`

#### 1. Define structure and create a node

```c
#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

struct Node *head = NULL;

struct Node *createNode(int data)
{
    struct Node *new = malloc(sizeof(struct Node));

    if (new == NULL)
        exit(EXIT_FAILURE);

    new->data = data;
    new->next = NULL;

    return new;
}
```



#### 2. Insert at beginning

```c
void insertBegin(int data)
{
    struct Node *new = createNode(data);

    new->next = head;
    head = new;
}
```

**Time complexity:** O(1)

#### 3. Insert at end

```c
void insertEnd(int data)
{
    struct Node *new = createNode(data);

    if (head == NULL) {
        head = new;
        return;
    }

    struct Node *temp = head;

    while (temp->next != NULL)
        temp = temp->next;

    temp->next = new;
}
```

**Time complexity:** O(n)

#### 4. Insert at any position

```c
void insertPos(int data, int pos)
{
    if (pos < 1)
        return;

    if (pos == 1) {
        insertBegin(data);
        return;
    }

    struct Node *temp = head;

    for (int i = 1; i < pos - 1 && temp; i++)
        temp = temp->next;

    if (temp == NULL)
        return;

    struct Node *new = createNode(data);

    new->next = temp->next;
    temp->next = new;
}
```

Position starts from 1. **Time complexity:** O(n)

#### 5. Delete from beginning

```c
void deleteBegin()
{
    if (head == NULL)
        return;

    struct Node *temp = head;

    head = head->next;
    free(temp);
}
```

**Time complexity:** O(1)

#### 6. Delete from end

```c
void deleteEnd()
{
    if (head == NULL)
        return;

    if (head->next == NULL) {
        free(head);
        head = NULL;
        return;
    }

    struct Node *temp = head;

    while (temp->next->next != NULL)
        temp = temp->next;

    free(temp->next);
    temp->next = NULL;
}
```

**Time complexity:** O(n)

#### 7. Delete from any position

```c
void deletePos(int pos)
{
    if (head == NULL || pos < 1)
        return;

    if (pos == 1) {
        deleteBegin();
        return;
    }

    struct Node *temp = head;

    for (int i = 1; i < pos - 1 && temp; i++)
        temp = temp->next;

    if (temp == NULL || temp->next == NULL)
        return;

    struct Node *del = temp->next;

    temp->next = del->next;
    free(del);
}
```

**Time complexity:** O(n)

#### 8. Delete by value

```c
void deleteValue(int data)
{
    struct Node *temp = head;
    struct Node *prev = NULL;

    while (temp && temp->data != data) {
        prev = temp;
        temp = temp->next;
    }

    if (temp == NULL)
        return;

    if (prev == NULL)
        head = temp->next;
    else
        prev->next = temp->next;

    free(temp);
}
```

Deletes the first occurrence of the given value.

#### 9. Print linked list

```c
void printList()
{
    struct Node *temp = head;

    while (temp != NULL) {
        printf("%d -> ", temp->data);
        temp = temp->next;
    }

    printf("NULL\n");
}
```



#### 10. Search an element

```c
int search(int data)
{
    struct Node *temp = head;
    int pos = 1;

    while (temp) {
        if (temp->data == data)
            return pos;

        temp = temp->next;
        pos++;
    }

    return -1;
}
```

Returns its position or -1 if not found.

#### 11. Count number of nodes

```c
int countNodes()
{
    int count = 0;
    struct Node *temp = head;

    while (temp) {
        count++;
        temp = temp->next;
    }

    return count;
}
```



#### 12. Reverse a linked list (very important)

```c
void reverse()
{
    struct Node *prev = NULL;
    struct Node *curr = head;
    struct Node *next;

    while (curr) {
        next = curr->next;
        curr->next = prev;
        prev = curr;
        curr = next;
    }

    head = prev;
}
```

**Time:** O(n) | **Space:** O(1)

Original: `10 → 20 → 30 → NULL`. Reverse each link in turn. Result: `30 → 20 → 10 → NULL`.

#### 13. Find middle node

```c
struct Node *findMiddle()
{
    struct Node *slow = head;
    struct Node *fast = head;

    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
    }

    return slow;
}
```

Using slow and fast pointers.

- Slow moves one node at a time.
- Fast moves two nodes at a time.
- When fast reaches the end, slow is at the middle.

For even-length lists, this returns the second middle node.

#### 14. Detect loop (Floyd's algorithm)

```c
int detectLoop()
{
    struct Node *slow = head;
    struct Node *fast = head;

    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;

        if (slow == fast)
            return 1;
    }

    return 0;
}
```

**Time:** O(n) | **Space:** O(1)

#### 15. Find Nth node from end

```c
struct Node *nthFromEnd(int n)
{
    struct Node *fast = head;
    struct Node *slow = head;

    if (n <= 0)
        return NULL;

    while (n--) {
        if (!fast)
            return NULL;

        fast = fast->next;
    }

    while (fast) {
        slow = slow->next;
        fast = fast->next;
    }

    return slow;
}
```



#### 16. Remove duplicates from a sorted linked list

```c
void removeDuplicates()
{
    struct Node *temp = head;

    while (temp && temp->next) {
        if (temp->data == temp->next->data) {
            struct Node *del = temp->next;
            temp->next = del->next;
            free(del);
        }
        else
            temp = temp->next;
    }
}
```



#### 17. Delete entire linked list

```c
void freeList()
{
    while (head)
        deleteBegin();
}
```



#### 18. Main function to test operations

```c
int main()
{
    insertBegin(10);
    insertBegin(5);
    insertEnd(20);
    insertEnd(30);
    insertPos(15, 3);

    printList();

    deleteBegin();
    deleteEnd();
    deletePos(2);

    printList();

    reverse();
    printList();

    printf("Count = %d\n", countNodes());

    freeList();

    return 0;
}
```

Combine the above functions into a single C file.

**Output:**

```text
5 -> 10 -> 15 -> 20 -> 30 -> NULL
10 -> 20 -> NULL
20 -> 10 -> NULL
Count = 2
```

#### Time complexity cheat sheet

| Operation | Time complexity |
|---|---|
| Insert at beginning | O(1) |
| Insert at end | O(n) |
| Insert at position | O(n) |
| Delete beginning | O(1) |
| Delete end | O(n) |
| Delete at position | O(n) |
| Delete by value | O(n) |
| Search | O(n) |
| Traversal | O(n) |
| Reverse | O(n) |
| Find middle | O(n) |
| Detect loop | O(n) |
| Nth node from end | O(n) |
| Remove duplicates (sorted) | O(n) |

#### Most important linked list questions for embedded interviews

For Microsoft, Arm, Cisco and other embedded software interviews, prioritize these:

1. Reverse a linked list.
2. Detect a loop in a linked list.
3. Detect the starting point of a loop.
4. Remove a loop.
5. Find the middle node.
6. Find the Nth node from the end.
7. Merge two sorted linked lists.
8. Find the intersection of two linked lists.
9. Reverse a linked list in groups of K.
10. Check whether a linked list is a palindrome.
11. Implement a doubly linked list.
12. Implement a circular linked list.
13. Implement a linked list without `malloc()` using a static memory pool.
14. Implement an LRU cache using a doubly linked list and hash table.

**Embedded-specific tip:** The above implementation uses a global `head` pointer to keep the code simple for interviews. In production code, prefer passing `struct Node **head` to functions that modify the head. For deterministic embedded systems, also understand static memory pool allocation as an alternative to `malloc()`.

**Note for subsequent questions:** The remaining examples in this topic use a separate type, `typedef struct node { int val; struct node *next; } node_t;`, rather than `struct Node` used above.

### Delete a node with a given value from a singly linked list. {E}
Use the same `struct Node`, global `head` and `createNode()` from Question 1. These examples are separate interview snippets unless stated otherwise.

**Approach:** Find the first matching node while tracking its predecessor. Update the previous node's `next`, or update `head` if deleting the first node. Then free the removed node.

```c
void deleteValue(int data)
{
    struct Node *temp = head;
    struct Node *prev = NULL;

    while (temp && temp->data != data) {
        prev = temp;
        temp = temp->next;
    }

    if (temp == NULL)
        return;

    if (prev == NULL)
        head = temp->next;
    else
        prev->next = temp->next;

    free(temp);
}
```

**Example:** 10 → 20 → 30 → NULL. After `deleteValue(20)`: 10 → 30 → NULL.

**Time:** O(n) | **Space:** O(1). Handles an empty list, missing value and deletion at the head.

### Delete a node when you are given only a pointer to that node (no head). {M}
Use the same `struct Node`, global `head` and `createNode()` from Question 1. These examples are separate interview snippets unless stated otherwise.

**Approach:** If only a pointer to the node is given, copy the next node's data into it, bypass the next node and free that next node.

```c
int deleteGivenNode(struct Node *node)
{
    if (node == NULL || node->next == NULL)
        return 0;

    struct Node *temp = node->next;

    node->data = temp->data;
    node->next = temp->next;
    free(temp);

    return 1;
}
```

**Example:** Given the node containing 20 in 10 → 20 → 30, copy 30 into it and free the original 30 node. The list becomes 10 → 30.

**Time:** O(1) | **Space:** O(1). Cannot delete the last node this way. The physical node identity changes logically, and external references to the freed successor become invalid.

### Find the nth node from the end of a linked list (and remove it). {E}
Use the same `struct Node`, global `head` and `createNode()` from Question 1. These examples are separate interview snippets unless stated otherwise.

**Approach:** Move `fast` n nodes ahead, then move `fast` and `slow` together. When `fast` reaches NULL, `slow` points to the nth node from the end (n=1 means last node).

```c
struct Node *nthFromEnd(int n)
{
    struct Node *fast = head;
    struct Node *slow = head;

    if (n <= 0)
        return NULL;

    while (n--) {
        if (!fast)
            return NULL;

        fast = fast->next;
    }

    while (fast) {
        slow = slow->next;
        fast = fast->next;
    }

    return slow;
}
```

#### Remove the Nth node from the end

Use the same two-pointer approach, tracking the previous node so we can unlink the exact target even when values repeat.

```c
void removeNthFromEnd(int n)
{
    struct Node *fast = head;
    struct Node *slow = head;
    struct Node *prev = NULL;

    if (n <= 0)
        return;

    while (n--) {
        if (!fast)
            return;

        fast = fast->next;
    }

    while (fast) {
        prev = slow;
        slow = slow->next;
        fast = fast->next;
    }

    if (prev == NULL)
        head = slow->next;
    else
        prev->next = slow->next;

    free(slow);
}
```

**Example:** 10 → 20 → 30 → 40 → 50, n=2. The target is 40. After removal: 10 → 20 → 30 → 50.

**Time:** O(n) | **Space:** O(1). Handles n equal to the length, invalid n and empty lists.

### Merge two sorted linked lists. {E}
Use the same `struct Node`, global `head` and `createNode()` from Question 1. These examples are separate interview snippets unless stated otherwise.

**Approach:** Compare the first nodes of both sorted lists and attach the smaller node to the result. Use a temporary dummy node to simplify the first insertion.

```c
struct Node *mergeSorted(struct Node *a, struct Node *b)
{
    struct Node dummy = {0, NULL};
    struct Node *temp = &dummy;

    while (a && b) {
        if (a->data <= b->data) {
            temp->next = a;
            a = a->next;
        }
        else {
            temp->next = b;
            b = b->next;
        }

        temp = temp->next;
    }

    temp->next = a ? a : b;

    return dummy.next;
}
```

**Example:** 1 → 3 → 5 and 2 → 4 → 6 become 1 → 2 → 3 → 4 → 5 → 6.

**Time:** O(n+m) | **Space:** O(1). No allocation; existing nodes are relinked. Input lists must be disjoint and acyclic. The original lists are consumed by the merge.

### Remove duplicates from a sorted linked list. {E}
Use the same `struct Node`, global `head` and `createNode()` from Question 1. These examples are separate interview snippets unless stated otherwise.

**Approach:** In a sorted list, duplicates are adjacent. If two consecutive nodes have equal data, unlink and free the second node. Otherwise move forward.

```c
void removeDuplicates()
{
    struct Node *temp = head;

    while (temp && temp->next) {
        if (temp->data == temp->next->data) {
            struct Node *del = temp->next;
            temp->next = del->next;
            free(del);
        }
        else
            temp = temp->next;
    }
}
```

**Example:** 10 → 10 → 20 → 30 → 30 becomes 10 → 20 → 30.

**Time:** O(n) | **Space:** O(1). Do not advance after deleting a duplicate, because the next node may also contain the same value. For unsorted lists, use a hash set or nested loops.

### Reverse a linked list in groups of k. {H}
**Short answer:** Process the list one block of k nodes at a time: first check that k nodes remain (otherwise leave the tail as it is), reverse the links inside the block, then connect the node before the block to the block's new first node and the block's new last node to the next block. A dummy node in front of the head removes the special case for the first block. O(n) time, O(1) space.

```c
/* reverses each block of k nodes; a final block shorter than k is left as is */
node_t *reverse_k_group(node_t *head, int k)
{
    if (k <= 1) return head;
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

#### Group boundaries

```text
prev -> A -> B -> C -> D -> E
k=3:   C -> B -> A -> D -> E
                  ^     ^
              group tail remaining
```

Find the kth node before reversing; if absent, preserve the final partial group. Set prev to the node after the group, so the original first node automatically links to the remaining list when reversed. Require k>=1; k=1 is a no-op. The code must reject zero or negative k before attempting traversal.

### Find the intersection point of two linked lists. {M}
Use the same `struct Node`, global `head` and `createNode()` from Question 1. These examples are separate interview snippets unless stated otherwise.

**Approach:** Use two pointers. When either pointer reaches NULL, move it to the other list's head. Both pointers then travel the same total distance and meet at the intersection or at NULL.

```c
struct Node *intersection(struct Node *a, struct Node *b)
{
    struct Node *p = a;
    struct Node *q = b;

    while (p != q) {
        p = p ? p->next : b;
        q = q ? q->next : a;
    }

    return p;
}
```

**Example:** A: 10 → 20 → 30 → 40; B: 5 → 30 → 40, where nodes 30 and 40 are physically shared. Returns the pointer to node 30.

**Time:** O(n+m) | **Space:** O(1). Compare node addresses, not data. Assumes acyclic lists.

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

#### Restore even when comparison fails

For 1→2→3→2→1, reverse from the middle 3; the second traversal is 1→2→3, matching the first three values of the original prefix. For 1→2→2→1, compare two values. Restoration must execute regardless of mismatch; an early return inside the comparison would leave the list altered. Require exclusive access during reversal because other readers may see temporarily broken links.

### Detect and remove a loop in a linked list. {M}
Use the same `struct Node`, global `head` and `createNode()` from Question 1. These examples are separate interview snippets unless stated otherwise.

#### Detect a loop (Floyd's algorithm)

Slow moves one node at a time and fast moves two. If they meet, there is a loop.

```c
int detectLoop()
{
    struct Node *slow = head;
    struct Node *fast = head;

    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;

        if (slow == fast)
            return 1;
    }

    return 0;
}
```

#### Find the starting point and remove the loop

After the pointers meet, reset slow to head and move both one step at a time. Their next meeting point is the loop entry. Walk around the loop to locate its last node and set its next pointer to NULL.

```c
void removeLoop()
{
    struct Node *slow = head;
    struct Node *fast = head;

    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;

        if (slow == fast)
            break;
    }

    if (!fast || !fast->next)
        return;

    slow = head;

    while (slow != fast) {
        slow = slow->next;
        fast = fast->next;
    }

    while (fast->next != slow)
        fast = fast->next;

    fast->next = NULL;
}
```

**Example:** 10 → 20 → 30 → 40, with 40 pointing back to 20. The loop entry is 20. Set 40's next pointer to NULL.

**Time:** O(n) | **Space:** O(1). Handles a loop starting at head and a single node pointing to itself.

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

#### Insert and delete invariants

For each interior node n, n->next->prev == n and n->prev->next == n. The head has prev=NULL and tail has next=NULL. Removing the only node must set both head and tail to NULL. A pointer passed to remove must belong to this list; arbitrary or stale pointers are not valid inputs. Add push_front symmetrically by linking the new node to the old head and updating the old head's prev, or setting tail when the list was empty.

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

#### Remove the first node in O(1)

```c
bool cl_pop_front(node_t **tail, int *out)
{
    if (!*tail) return false;
    node_t *head = (*tail)->next;
    *out = head->val;
    if (head == *tail) *tail = NULL;
    else (*tail)->next = head->next;
    free(head);
    return true;
}
```

For 10→20→30→10, tail points to 30 and head is tail->next. Removing 10 connects 30 to 20. Unlike a conventional singly linked list, iteration stops upon returning to the start rather than finding NULL.

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

#### Why use a sentinel?

An empty intrusive list has head.next=head and head.prev=head. Inserting the first node uses the same four pointer assignments as an interior insertion. Deleting the last node restores the self-links. The containing object is not allocated or freed by list_add/list_del. One list_head can belong to only one list at a time; separate members permit multiple memberships. Use safe iteration when removing the current entry, and locks/RCU appropriate to concurrent access.

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

#### Stack boundary test

For capacity 3, push 10,20,30; a fourth push must fail without changing the stack. Pop returns 30, then 20, then 10, and the next pop fails. The array top is a count, so the last valid value is at top−1. A linked stack instead stores its top in a pointer and can grow until memory is exhausted (not literally unbounded). For deterministic firmware, use a fixed array or preallocated node pool.

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

#### Queue wraparound example

With capacity 4, enqueue A,B,C,D; head=0,count=4. Pop A,B; head=2,count=2. Enqueue E,F; they occupy slots 0,1. Logical order is C,D,E,F although physical slots are E,F,C,D. With explicit count, all slots are usable. The linked version must clear tail when removing the last node. Both examples assume one execution context; shared count needs synchronization.

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

#### Shared capacity invariant

Stack 1 grows from index 0 upward; stack 2 grows from CAP−1 downward. The free space is top2−top1−1. For CAP=4, push1(A),push2(B),push1(C),push2(D) occupies all four slots. Neither can push again until either pops. This is more flexible than splitting storage into two fixed halves, but does not reserve a minimum capacity for each client. Add quotas if a client must always have room.

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

#### Amortized versus worst-case cost

Push 1,2,3 onto the input stack. First pop transfers all three to output, reversing their order, and returns 1. The next two pops return 2 and 3 without transferring. Each item is pushed and popped at most once per stack, so amortized time is O(1), but a single pop can take O(n). In a hard real-time system, a circular array gives a simpler constant worst-case operation count.

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

#### Duplicate minima

Push 5,2,2,7. The minimum array becomes 5,2,2,2. Pop 7: minimum remains 2. Pop one 2: minimum remains 2 because the earlier 2 still exists. Pop the other 2: minimum becomes 5. Storing the minimum at each depth avoids a rescan; an alternative is a second stack of minima with counts for repeated values. Arithmetic encoding tricks need explicit overflow handling.

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

#### Trace and validation

For a+b*c, emit a, push +, emit b, push *, emit c, then pop * and + to obtain abc*+. Multiplication has greater precedence; operators of equal precedence in the example are left-associative. A robust parser must reject mismatched parentheses, invalid tokens, adjacent operands without an operator and missing operands, and check stack/output capacity before each write. The compact example assumes valid single-character expressions whose nesting fits its fixed stack; multi-digit numbers need tokenization.

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
        if (isdigit((unsigned char)*s)) {
            if (top == 64) { *ok = 0; return 0; }
            st[top++] = *s - '0'; continue;
        }
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

#### Operand ordering and arithmetic safety

For postfix 82-, push 8, push 2, pop right operand 2 then left operand 8 and push 6. For 82/, the result is 4, not 0. A valid binary expression has sufficient operands at each operator and exactly one value remaining at the end. Reject stack overflow, division by zero and signed arithmetic overflow (including LONG_MIN divided by -1). The compact example assumes representable intermediate arithmetic; for untrusted expressions use checked addition, subtraction and multiplication. Multi-digit and negative literals require tokenization.

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

void lru_init(lru_t *c) { for (int k = 0; k < MAX_KEY; ++k) c->where[k] = -1; c->head = c->tail = -1; c->used = 0; }

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
    if (key < 0 || key >= MAX_KEY || !val) return false;
    int i = c->where[key];
    if (i < 0) return false;
    unlink_e(c, i); push_front_e(c, i);                    /* mark as most recently used */
    *val = c->e[i].val;
    return true;
}

void lru_put(lru_t *c, int key, int val)
{
    if (key < 0 || key >= MAX_KEY) return;
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

#### LRU eviction worked example

Capacity 3, front = most recently used:

| Operation | MRU → LRU |
|---|---|
| put(1,10) | 1 |
| put(2,20) | 2,1 |
| put(3,30) | 3,2,1 |
| get(1) | 1,3,2 |
| put(4,40) | 4,1,3 |

Key 2 is evicted, and its lookup-table entry must be cleared before its slot is reused. Updating an existing key does not allocate another slot. A general-purpose implementation combines a hash table and doubly linked list, yielding expected O(1) access; the fixed direct-index example gives bounded O(1) operations for its supported key domain. It is not thread-safe without serialization, because get modifies recency as well as reading the value.

