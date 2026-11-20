---
slug: coding-sorting-arrays
title: "Coding: Sorting & Array Problems"
icon: 📊
level: Intermediate
order: 19
desc: Insertion, selection, quick and merge sort in C, plus largest element, duplicates, Dutch flag (sort 0/1/2), merge intervals, 3Sum, maximum product of three and find-the-duplicate.
---
Sorting and array questions in embedded interviews are usually about writing a correct loop quickly and knowing the trade-offs: time and space complexity, stability, worst case, and stack usage on a microcontroller. Each answer gives compact, tested C and the points to mention.

### Find the largest element in an array. {E}
```c
#include <stddef.h>

int largest(const int *a, size_t n)        /* n >= 1 */
{
    int max = a[0];                        /* start with an element, not 0 */
    for (size_t i = 1; i < n; i++)
        if (a[i] > max) max = a[i];
    return max;
}
```

**Points:** initialise with `a[0]` (or `INT_MIN`) so all-negative arrays work; O(n), one pass; to find min and max together with fewer comparisons, process elements in pairs (about 1.5n comparisons instead of 2n).

### Find duplicate elements in an array. {E}
```c
#include <stdio.h>
#include <stdbool.h>
#include <stddef.h>

/* values known to be in 0..255 (e.g. bytes, sensor IDs): counting table, O(n) */
void print_duplicates_small(const unsigned char *a, size_t n)
{
    unsigned count[256] = {0};
    for (size_t i = 0; i < n; i++)
        if (++count[a[i]] == 2) printf("%u ", a[i]);   /* print each duplicate once */
    printf("\n");
}

/* general values: sort first (in place), then adjacent duplicates are neighbours */
void print_duplicates_sorted(const int *a, size_t n)
{
    for (size_t i = 1; i < n; i++)
        if (a[i] == a[i - 1] && (i == 1 || a[i] != a[i - 2]))
            printf("%d ", a[i]);
    printf("\n");
}
```

**Points:** choose by constraints: small value range → counting table (O(n), O(range) memory); otherwise sort (O(n log n), O(1) extra) or a hash set (O(n) average, O(n) memory); brute force is O(n²). Mention which one fits an MCU (no heap: sort or table).

### Implement insertion sort. {E}
```c
#include <stddef.h>

void insertion_sort(int *a, size_t n)
{
    for (size_t i = 1; i < n; i++) {
        int key = a[i];
        size_t j = i;
        while (j > 0 && a[j - 1] > key) {   /* shift larger elements right */
            a[j] = a[j - 1];
            j--;
        }
        a[j] = key;
    }
}
```

**Points:** O(n²) worst/average, **O(n) on nearly sorted data**, stable, in place, very small code: the best choice for small arrays (< ~20 elements) and data arriving almost sorted (e.g. keeping a short list of readings in order). Library sorts switch to insertion sort for small partitions.

### Implement selection sort. {E}
```c
#include <stddef.h>

void selection_sort(int *a, size_t n)
{
    for (size_t i = 0; i + 1 < n; i++) {
        size_t min = i;
        for (size_t j = i + 1; j < n; j++)
            if (a[j] < a[min]) min = j;
        if (min != i) { int t = a[i]; a[i] = a[min]; a[min] = t; }
    }
}
```

**Points:** always O(n²) comparisons but at most **n − 1 swaps**, which matters when writes are expensive (e.g. sorting records stored in flash or EEPROM). Not stable in this form, in place.

### Implement quicksort. {M}
```c
#include <stddef.h>

static void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }

/* Lomuto partition with median-of-three pivot */
static size_t partition(int *a, size_t lo, size_t hi)        /* inclusive bounds */
{
    size_t mid = lo + (hi - lo) / 2;
    if (a[mid] < a[lo]) swap(&a[mid], &a[lo]);
    if (a[hi]  < a[lo]) swap(&a[hi],  &a[lo]);
    if (a[mid] < a[hi]) swap(&a[mid], &a[hi]);              /* median now at a[hi] */
    int pivot = a[hi];
    size_t i = lo;
    for (size_t j = lo; j < hi; j++)
        if (a[j] < pivot) swap(&a[i++], &a[j]);
    swap(&a[i], &a[hi]);
    return i;
}

void quick_sort(int *a, size_t lo, size_t hi)
{
    while (lo < hi) {
        size_t p = partition(a, lo, hi);
        if (p - lo < hi - p) {                     /* recurse on the smaller side */
            if (p > lo) quick_sort(a, lo, p - 1);
            lo = p + 1;                            /* loop on the larger side */
        } else {
            quick_sort(a, p + 1, hi);
            if (p == 0) break;
            hi = p - 1;
        }
    }
}
/* usage: if (n > 1) quick_sort(a, 0, n - 1); */
```

**Points:** average O(n log n), worst O(n²) (already sorted input with a naive pivot; median-of-three helps), in place, not stable. Recursing only on the smaller part bounds stack depth to O(log n), which matters on a microcontroller. `qsort()` from the C library is usually fine in practice, but its timing is not deterministic.

### Implement merge sort. {M}
```c
#include <stddef.h>
#include <string.h>

static void merge(int *a, int *tmp, size_t lo, size_t mid, size_t hi)   /* [lo,mid) + [mid,hi) */
{
    size_t i = lo, j = mid, k = lo;
    while (i < mid && j < hi) tmp[k++] = (a[j] < a[i]) ? a[j++] : a[i++];   /* <= keeps it stable */
    while (i < mid) tmp[k++] = a[i++];
    while (j < hi)  tmp[k++] = a[j++];
    memcpy(a + lo, tmp + lo, (hi - lo) * sizeof *a);
}

/* bottom-up: no recursion, needs an n-element scratch buffer */
void merge_sort(int *a, int *tmp, size_t n)
{
    for (size_t width = 1; width < n; width *= 2)
        for (size_t lo = 0; lo < n - width; lo += 2 * width) {
            size_t mid = lo + width;
            size_t hi = (mid + width < n) ? mid + width : n;
            merge(a, tmp, lo, mid, hi);
        }
}
```

**Points:** O(n log n) in **all** cases (predictable timing), **stable**, but needs O(n) extra memory for arrays. The bottom-up form avoids recursion (good for small stacks). For linked lists, merge sort needs no extra memory, which makes it the standard way to sort lists.

### Sort an array of 0s, 1s and 2s (Dutch national flag). {M}
```c
#include <stddef.h>

void sort012(int *a, size_t n)
{
    size_t lo = 0, mid = 0, hi = n;          /* [0,lo)=0, [lo,mid)=1, [mid,hi)=unknown, [hi,n)=2 */
    while (mid < hi) {
        if (a[mid] == 0)      { int t = a[lo]; a[lo++] = a[mid]; a[mid++] = t; }
        else if (a[mid] == 1) { mid++; }
        else                  { hi--; int t = a[hi]; a[hi] = a[mid]; a[mid] = t; }   /* don't advance mid */
    }
}
/* {2, 0, 2, 1, 1, 0} -> {0, 0, 1, 1, 2, 2} */
```

**Points:** one pass, O(n), O(1) space, using three regions. After swapping a 2 to the end, do not advance `mid`, because the element swapped in has not been examined yet. Counting sort (count 0s, 1s, 2s, then rewrite) also works in two passes.

### Merge overlapping intervals. {M}
```c
#include <stdlib.h>

typedef struct { int start, end; } interval_t;

static int by_start(const void *a, const void *b)
{
    const interval_t *x = a, *y = b;
    return (x->start > y->start) - (x->start < y->start);
}

/* merges in place; returns the new count */
size_t merge_intervals(interval_t *v, size_t n)
{
    if (n == 0) return 0;
    qsort(v, n, sizeof *v, by_start);
    size_t w = 0;
    for (size_t i = 1; i < n; i++) {
        if (v[i].start <= v[w].end) {                         /* overlaps the current one */
            if (v[i].end > v[w].end) v[w].end = v[i].end;
        } else {
            v[++w] = v[i];
        }
    }
    return w + 1;
}
/* [1,3] [2,6] [8,10] [15,18] -> [1,6] [8,10] [15,18] */
```

**Points:** sort by start (O(n log n)), then one pass extending the last merged interval. Decide whether touching intervals (`[1,2]` and `[2,3]`) merge (`<=`) or not (`<`). Embedded uses: merging free regions in an allocator, combining flash erase ranges, coalescing time windows in a scheduler.

### Find the maximum product of three numbers. {M}
```c
#include <limits.h>
#include <stddef.h>

long long max_product3(const int *a, size_t n)               /* n >= 3 */
{
    int max1 = INT_MIN, max2 = INT_MIN, max3 = INT_MIN;      /* three largest */
    int min1 = INT_MAX, min2 = INT_MAX;                      /* two smallest */
    for (size_t i = 0; i < n; i++) {
        int x = a[i];
        if (x > max1) { max3 = max2; max2 = max1; max1 = x; }
        else if (x > max2) { max3 = max2; max2 = x; }
        else if (x > max3) { max3 = x; }
        if (x < min1) { min2 = min1; min1 = x; }
        else if (x < min2) { min2 = x; }
    }
    long long p1 = (long long)max1 * max2 * max3;
    long long p2 = (long long)min1 * min2 * max1;             /* two negatives make a positive */
    return p1 > p2 ? p1 : p2;
}
/* {-10, -10, 1, 3, 2} -> 300 */
```

**Points:** the answer is either the three largest numbers or the two most negative times the largest; one pass, O(n), no sorting; use a 64-bit product to avoid overflow.

### Solve 3Sum: find all unique triplets that sum to zero. {M}
```c
#include <stdio.h>
#include <stdlib.h>

static int cmp_int(const void *a, const void *b)
{
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

void three_sum(int *a, size_t n)
{
    qsort(a, n, sizeof *a, cmp_int);
    for (size_t i = 0; i + 2 < n; i++) {
        if (i > 0 && a[i] == a[i - 1]) continue;           /* skip duplicate first values */
        size_t l = i + 1, r = n - 1;
        while (l < r) {
            long sum = (long)a[i] + a[l] + a[r];
            if (sum < 0) l++;
            else if (sum > 0) r--;
            else {
                printf("[%d, %d, %d]\n", a[i], a[l], a[r]);
                while (l < r && a[l] == a[l + 1]) l++;     /* skip duplicates */
                while (l < r && a[r] == a[r - 1]) r--;
                l++; r--;
            }
        }
    }
}
/* {-1, 0, 1, 2, -1, -4} -> [-1, -1, 2] and [-1, 0, 1] */
```

**Points:** sort, fix the first element, then two pointers on the rest: O(n²) time, O(1) extra space; skip equal values to avoid duplicate triplets.

### Find the duplicate number in an array of n+1 integers in the range 1..n. {M}
```c
#include <stddef.h>

/* Floyd's cycle detection: O(n) time, O(1) space, array not modified */
int find_duplicate(const int *a, size_t n_plus_1)
{
    (void)n_plus_1;
    int slow = a[0], fast = a[a[0]];
    while (slow != fast) {                 /* phase 1: meet inside the cycle */
        slow = a[slow];
        fast = a[a[fast]];
    }
    slow = 0;                              /* phase 2: find the cycle entrance */
    while (slow != fast) {
        slow = a[slow];
        fast = a[fast];
    }
    return slow;
}
/* {1, 3, 4, 2, 2} -> 2 */
```

**Points:** treat values as "next" pointers (`i → a[i]`); a duplicate value means two indexes point to the same node, which creates a cycle whose entrance is the duplicate. This is the linked-list loop algorithm on an array. Simpler alternatives: a seen-bitmap (O(n) memory), sorting (modifies the array), or marking visited indexes by negating values (modifies the array).
