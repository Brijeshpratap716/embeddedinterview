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
**Short answer:** Start with the first element as the current maximum, then scan the rest of the array once and replace the maximum whenever a larger element appears. Time O(n), space O(1). Initialising with `a[0]` (not 0) makes it correct for arrays of negative numbers.

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

**Dry run:** `{-7, -3, -9, -1}` → max starts at −7, becomes −3, stays, becomes −1. Starting from 0 would wrongly return 0.

**Second largest (common follow-up)**

```c
#include <limits.h>
#include <stdio.h>

int main(void)
{
    int a[] = { 12, 35, 1, 10, 34, 35 };
    int first = INT_MIN, second = INT_MIN;
    for (int i = 0; i < 6; i++) {
        if (a[i] > first)                        { second = first; first = a[i]; }
        else if (a[i] > second && a[i] != first) { second = a[i]; }   /* distinct second */
    }
    printf("%d %d\n", first, second);           /* 35 34 */
    return 0;
}
```

**Other points interviewers check**

- Empty array: decide the contract (require `n >= 1`, or return an error flag).
- Returning the **index** instead of the value is often more useful (e.g. which ADC channel had the peak).
- Min and max together: compare elements in pairs (smaller with min, larger with max) — about 1.5n comparisons instead of 2n.
- For a fixed small array on a DSP, CMSIS-DSP has `arm_max_q15` etc., which use SIMD.

#### A checked interface

```c
bool largest_checked(const int *a, size_t n, int *out)
{
    if (!a || !n || !out) return false;
    int max = a[0];
    for (size_t i=1; i<n; ++i)
        if (a[i] > max) max = a[i];
    *out = max;
    return true;
}
```

At the start of each iteration, max is the maximum of the already inspected prefix. The loop requires exactly n−1 comparisons for nonempty input. The status return distinguishes an empty array from a legitimate maximum such as INT_MIN.

### Find duplicate elements in an array. {E}
**Short answer:** The best method depends on the constraints. If values come from a small known range (bytes, IDs 0–255), count occurrences in a table and report each value when its count reaches 2: O(n) time. Otherwise sort the array (O(n log n), no extra memory) so duplicates become neighbours, or use a hash set (O(n) average, O(n) memory). The brute-force double loop is O(n²).

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

**Comparison**

| Method | Time | Extra memory | Modifies array | Good for |
|---|---|---|---|---|
| Nested loops | O(n²) | O(1) | no | tiny arrays |
| Sort + scan neighbours | O(n log n) | O(1) (heap sort) | yes | general values, no heap |
| Counting table / bitmap | O(n + range) | O(range) | no | small value range |
| Hash set | O(n) average | O(n) | no | large ranges with RAM available |

**Dry run (counting table) for `{4, 2, 4, 7, 2, 4}`:** counts become 4→1, 2→1, 4→2 (print 4), 7→1, 2→2 (print 2), 4→3 (no print). Output `4 2` — each duplicate printed once.

**Why the sorted version checks `a[i-2]`:** in `{3, 3, 3}` the pairs at i=1 and i=2 are both equal; checking that `a[i] != a[i-2]` prints 3 only once.

**Related questions**

- **Remove duplicates from a sorted array in place** (keep a write index, copy when `a[i] != a[w-1]`) — O(n).
- **Find the missing number from 1..n:** expected sum `n(n+1)/2` minus the actual sum, or XOR of all indices and values (no overflow).
- **Find the one duplicate in 1..n with n+1 elements:** Floyd's cycle method (last question in this topic).
- A **bitmap** (1 bit per possible value) cuts the table memory 8–32× — 512 bytes for 4096 possible IDs.

#### Duplicate detection with a fixed bitmap

For byte values, use two 256-bit bitmaps: seen and reported. On the first occurrence set seen; on the second, print the value and set reported; further occurrences need no output. This uses 64 bytes, avoids count overflow and preserves order of second occurrence. For [4,2,4,4,2], the output is 4,2. For unrestricted integers, use a hash table or sorting; if preserving original indices matters, retain index metadata.

### Implement insertion sort. {E}
**Short answer:** Build a sorted prefix one element at a time: take the next element (`key`), shift every larger element of the sorted part one place to the right, and drop the key into the gap. It is stable, in place, tiny, and runs in O(n) on nearly sorted data, but O(n²) in the worst case.

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

**Dry run for `{5, 2, 4, 6, 1}`**

| i | key | array after inserting |
|---|---|---|
| 1 | 2 | 2 5 4 6 1 |
| 2 | 4 | 2 4 5 6 1 |
| 3 | 6 | 2 4 5 6 1 (no shift) |
| 4 | 1 | 1 2 4 5 6 |

**Why `j` counts down with `j > 0` first:** using `size_t`, `j - 1` must not be evaluated when `j == 0`; the `&&` short-circuit guarantees that.

**Why it is stable:** the loop only shifts elements that are strictly greater (`>`), so equal keys keep their original order.

**Complexity**

| Case | Comparisons | Example |
|---|---|---|
| Best | n − 1 | already sorted |
| Worst | n(n − 1)/2 | reverse sorted |
| Memory | O(1) | |

**Embedded uses:** sorting 5–15 samples for a median filter, keeping a small "top N" list ordered as values arrive (insert each new value into place), and as the final stage of hybrid sorts (introsort and Timsort switch to insertion sort for partitions below ~16–32 elements).

**Follow-up — binary insertion sort:** find the insert position with binary search (fewer comparisons), but shifting still costs O(n) per element.

#### Dry run with the sorted prefix

| Iteration | Key | Array after insertion |
|---|---:|---|
| Initial | — | 5, 2, 4, 1 |
| 1 | 2 | 2, 5, 4, 1 |
| 2 | 4 | 2, 4, 5, 1 |
| 3 | 1 | 1, 2, 4, 5 |

The loop invariant is that a[0..i) is sorted before each insertion. Shifting rather than repeatedly swapping reduces writes. Using greater-than rather than greater-than-or-equal preserves the relative order of equal-key records. Sorted data requires only n−1 key comparisons.

### Implement selection sort. {E}
**Short answer:** For each position from left to right, find the smallest element in the unsorted remainder and swap it into that position. It always does about n²/2 comparisons but at most n − 1 swaps, which is its only real advantage: it minimises writes.

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

**Dry run for `{64, 25, 12, 22, 11}`**

| i | minimum found | array after swap |
|---|---|---|
| 0 | 11 | 11 25 12 22 64 |
| 1 | 12 | 11 12 25 22 64 |
| 2 | 22 | 11 12 22 25 64 |
| 3 | 25 | unchanged |

**Properties**

- Time: O(n²) in all cases (no early exit on sorted input).
- Swaps: ≤ n − 1 → good when writing is expensive (EEPROM/flash cells, large records moved by value).
- Not stable: the long-distance swap can move an equal element past another (e.g. `{4a, 4b, 1}` → `{1, 4b, 4a}`). A stable variant shifts instead of swapping, losing the write advantage.

**Comparison with bubble sort (also often asked)**

```c
void bubble_sort(int *a, int n)
{
    for (int pass = 0; pass < n - 1; pass++) {
        int swapped = 0;
        for (int j = 0; j < n - 1 - pass; j++)
            if (a[j] > a[j + 1]) { int t = a[j]; a[j] = a[j + 1]; a[j + 1] = t; swapped = 1; }
        if (!swapped) break;              /* already sorted: O(n) best case */
    }
}
```

Bubble sort is stable and has an O(n) best case with the early exit, but does many more swaps. In practice insertion sort beats both; know them for the interview.

#### When writes are more expensive than comparisons

Selection sort always performs n(n−1)/2 key comparisons, but at most n−1 swaps. On a small fixed array where minimizing moves matters more than comparisons, that may be desirable. It is generally unstable: sorting tagged records [2A,2B,1] swaps 1 with 2A, reversing the equal keys. A stable version shifts the selected minimum into place at the expense of more writes.

### Implement quicksort. {M}
**Short answer:** Pick a pivot, partition the array so that smaller elements are on its left and larger ones on its right, then sort the two parts the same way. Average O(n log n), in place, not stable. For embedded use, choose the pivot by median-of-three and recurse only into the smaller part (looping over the larger one) so the stack depth stays O(log n) even in bad cases.

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

**Lomuto partition step by step (pivot = last element)**

`i` marks the end of the "less than pivot" region. For each `j`, if `a[j] < pivot`, swap it into the region and grow it. Finally swap the pivot into position `i`; it is now in its final sorted place.

**Dry run of one partition on `{7, 2, 9, 4, 5}` (pivot 5)**

| j | a[j] | < 5? | array | i |
|---|---|---|---|---|
| 0 | 7 | no | 7 2 9 4 5 | 0 |
| 1 | 2 | yes, swap a[0],a[1] | 2 7 9 4 5 | 1 |
| 2 | 9 | no | 2 7 9 4 5 | 1 |
| 3 | 4 | yes, swap a[1],a[3] | 2 4 9 7 5 | 2 |
| end | | swap a[2], pivot | 2 4 **5** 7 9 | |

**Why worst case is O(n²):** if the pivot is always the smallest or largest element (sorted input with a first/last pivot), each partition removes only one element — n levels of n work. Median-of-three, random pivots, or introsort (switch to heap sort when recursion gets too deep) avoid this.

**Stack safety:** naive recursion on sorted data can reach depth n (thousands of frames → stack overflow on a 2 KB task stack). Recursing on the smaller side guarantees each recursive call handles at most half the elements → depth ≤ log₂ n.

**Hoare partition** (two pointers moving inward) does about three times fewer swaps than Lomuto and handles many equal keys better; three-way partitioning (`<`, `=`, `>`) is best when there are many duplicates.

**Points to mention:** not stable; C's `qsort` is often (not necessarily) a quicksort/introsort; for hard real-time code prefer heap sort or merge sort for their guaranteed O(n log n).

#### Partition invariant

Before processing index j, elements in [lo,i) are less than pivot, [i,j) are greater than or equal to pivot, and [j,hi) are unexamined. After placing the pivot at i, its final position is established. For [4,1,3,2] with pivot 2, partition produces [1,2,3,4]. Median-of-three is a heuristic, not a worst-case guarantee. Equal-heavy data can cause quadratic comparisons; a three-way partition groups values less than, equal to and greater than pivot. Recursing on the smaller side bounds stack depth independently of bad pivot choices.

### Implement merge sort. {M}
**Short answer:** Split the array into halves, sort each half, and merge the two sorted halves by repeatedly taking the smaller front element. It runs in O(n log n) in every case and is stable, but needs an O(n) scratch buffer for arrays. The bottom-up version merges runs of width 1, 2, 4 … without recursion.

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

**Bottom-up dry run for `{5, 1, 4, 2, 3}`**

| width | merges | array |
|---|---|---|
| 1 | [5]+[1], [4]+[2], [3] | 1 5 2 4 3 |
| 2 | [1 5]+[2 4], [3] | 1 2 4 5 3 |
| 4 | [1 2 4 5]+[3] | 1 2 3 4 5 |

**Merge step:** two indices `i` (left run) and `j` (right run); copy the smaller into `tmp`; when one run is exhausted, copy the rest of the other; then copy `tmp` back. Taking from the **left** run when elements are equal (the code takes `a[j]` only if strictly smaller) is what makes it stable.

**Why choose merge sort**

- Guaranteed O(n log n): predictable timing for real-time systems.
- Stable: needed when sorting records by one key after another (e.g. by time, then by priority).
- Sequential access: suits linked lists, external storage (sorting data larger than RAM in chunks from flash/SD), and DMA streams.

**Linked-list merge sort:** split with slow/fast pointers, sort both halves, merge by relinking nodes — O(1) extra memory (apart from recursion depth log n). This is the standard way to sort lists (Linux `list_sort()` uses a bottom-up merge sort).

**Memory note for MCUs:** the scratch buffer can be static (`static int tmp[MAX_N]`) instead of heap-allocated; if RAM is too tight, use heap sort instead.

#### Bottom-up merge passes

```text
[7 2 5 1 4]
width=1: [2 7] [1 5] [4]
width=2: [1 2 5 7] [4]
width=4: [1 2 4 5 7]
```

Provide a distinct scratch array of n integers. For embedded real-time use, allocate it in advance rather than on every call. Ensure size computations fit size_t; a robust width-doubling loop stops once width >= n-width. Merging is stable when ties select the left run first. A linked-list merge sort can avoid the n-element array by relinking nodes.

### Sort an array of 0s, 1s and 2s (Dutch national flag). {M}
**Short answer:** Use three pointers in one pass (Dijkstra's Dutch national flag algorithm): `lo` marks the end of the 0s, `hi` the start of the 2s, and `mid` scans the unknown region. A 0 is swapped to `lo` (both advance), a 1 just advances `mid`, and a 2 is swapped to `hi - 1` (only `hi` moves, because the swapped-in element is still unexamined). O(n) time, O(1) space.

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

**Invariant during the loop**

```
[0, lo)    all 0
[lo, mid)  all 1
[mid, hi)  not yet examined
[hi, n)    all 2
```

**Dry run for `{2, 0, 2, 1, 1, 0}`**

| step | a[mid] | action | array | lo mid hi |
|---|---|---|---|---|
| 1 | 2 | swap with a[5] | 0 0 2 1 1 2 | 0 0 5 |
| 2 | 0 | swap a[0], advance | 0 0 2 1 1 2 | 1 1 5 |
| 3 | 0 | swap a[1], advance | 0 0 2 1 1 2 | 2 2 5 |
| 4 | 2 | swap with a[4] | 0 0 1 1 2 2 | 2 2 4 |
| 5 | 1 | advance | | 2 3 4 |
| 6 | 1 | advance | 0 0 1 1 2 2 | 2 4 4 → stop |

**Why `mid` advances after swapping a 0:** the element coming from `lo` is a 1 (or `lo == mid`), which is already examined.

**Alternative: counting sort** — count zeros, ones and twos in one pass, then overwrite the array. Two passes but simpler; it does not work if the elements carry other data (records with a priority 0/1/2 field), whereas the three-pointer method moves whole elements.

**Generalisations:** three-way partitioning in quicksort (elements less than, equal to, greater than the pivot), segregating even/odd numbers or negative/positive numbers (two-pointer version).

#### Why the middle pointer must not advance after moving a 2

For [2,1,0], swap the first 2 with the last unknown element, giving [0,1,2]. The new value at mid is 0 and still needs classification. Advancing mid immediately would skip it. Every iteration decreases the unknown region by one, so there are exactly n classifications. The precondition is that all values are 0,1,2; reject other values explicitly if the input is untrusted.

### Merge overlapping intervals. {M}
**Short answer:** Sort the intervals by start time, then walk through them keeping the last merged interval: if the next interval starts at or before its end, extend the end if needed; otherwise start a new merged interval. Sorting dominates: O(n log n) time, and merging in place needs O(1) extra space.

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

**Dry run for `[1,3] [2,6] [8,10] [15,18]` (already sorted)**

| next | current merged | overlap? | result list |
|---|---|---|---|
| [2,6] | [1,3] | 2 ≤ 3 yes → end = 6 | [1,6] |
| [8,10] | [1,6] | 8 > 6 no → new | [1,6] [8,10] |
| [15,18] | [8,10] | no → new | [1,6] [8,10] [15,18] |

**Why sorting is required:** without it, `[8,10] [1,3] [2,9]` would never notice that `[2,9]` overlaps `[8,10]`.

**Edge cases**

- Contained intervals: `[1,10]` and `[2,3]` → keep end 10 (that is why the code checks `v[i].end > v[w].end`).
- Touching intervals `[1,2]` and `[2,3]`: merge with `<=`, keep separate with `<`; state your choice.
- Comparator must avoid overflow: `(a > b) - (a < b)` instead of `a - b`.

**Related problems:** insert a new interval into a sorted list; meeting rooms (can one person attend all? → check overlaps after sorting); minimum number of rooms (sort start and end times separately, sweep); free-list coalescing in a memory allocator (adjacent free blocks merged on `free`).

#### Closed versus half-open intervals

For closed ranges [1,3] and [3,5], the point 3 belongs to both, so merging is natural. For half-open ranges [1,3) and [3,5), they do not overlap, although adjacent ranges may be intentionally coalesced. Choose <= or < to match that policy. Validate start <= end before sorting. In a driver resource allocator, avoid end+1 arithmetic that can overflow and distinguish adjacency from actual address overlap.

### Find the maximum product of three numbers. {M}
**Short answer:** The largest product of three numbers is either the product of the three largest values, or the product of the two smallest (most negative) values and the largest value, because two negatives multiply to a positive. Track the three largest and two smallest values in one pass and return the larger of the two candidate products, computed in 64 bits. O(n) time, O(1) space.

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

**Dry run for `{-10, -10, 1, 3, 2}`**

- Three largest: 3, 2, 1 → product 6.
- Two smallest: −10, −10; largest: 3 → product 300.
- Answer: 300.

**Cases to check out loud**

| Input | Answer | Comes from |
|---|---|---|
| `{1, 2, 3, 4}` | 24 | three largest |
| `{-10, -10, 1, 3, 2}` | 300 | two negatives × largest |
| `{-5, -4, -3, -2}` | −24 | three largest (least negative) |
| `{0, -1, 3, 100, -70, -50}` | 350000 | (−70)(−50)(100) |

**Why the `else if` chain:** when a new maximum arrives, the old max1 and max2 slide down to max2 and max3; checking in that order keeps all three correct with at most three comparisons per element.

**Simpler alternative:** sort and compare `a[n-1]*a[n-2]*a[n-3]` with `a[0]*a[1]*a[n-1]` — O(n log n), easy to explain, fine if speed is not critical.

**Overflow:** three 32-bit ints can need about 96 bits in the worst case; `long long` (64 bits) is enough for the typical interview range (values up to ~2 million), so mention the limit or use wider types.

**Variant — maximum product of two numbers:** the same idea with the two largest and the two smallest.

#### Why only two candidate products?

For an ordered sequence, a maximum positive product either uses three large positive values or the two most negative values with the largest positive value. If all values are negative, selecting the three largest (closest to zero) gives the least negative product. For [-10,-8,2,3,4], compare 4×3×2=24 with (-10)×(-8)×4=320. Repeated values occupy distinct positions and are allowed. Even int64_t may overflow for three arbitrary int32_t operands; require representable products or use checked/wider multiplication.

### Solve 3Sum: find all unique triplets that sum to zero. {M}
**Short answer:** Sort the array, then for each index `i` look for two numbers in the rest of the array that sum to `-a[i]` using two pointers moving inwards: move the left pointer right when the sum is too small and the right pointer left when it is too large. Skip equal values to avoid duplicate triplets. O(n²) time, O(1) extra space (besides sorting).

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

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
            int64_t sum = (int64_t)a[i] + a[l] + a[r];
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

**Dry run for `{-1, 0, 1, 2, -1, -4}` → sorted `{-4, -1, -1, 0, 1, 2}`**

| i (value) | l, r | sum | action |
|---|---|---|---|
| 0 (−4) | −1, 2 | −3 | l++ … never reaches 0 → none |
| 1 (−1) | −1, 2 | 0 | print [−1, −1, 2]; move both |
| | 0, 1 | 0 | print [−1, 0, 1]; move both |
| 2 (−1) | | | skipped (same as previous i) |
| 3 (0) | 1, 2 | 3 | r-- → l == r stop |

**Why two pointers work:** with a sorted array, increasing `l` can only increase the sum and decreasing `r` can only decrease it, so each pair is considered once per `i`: O(n) per `i`.

**Building up from Two Sum**

| Problem | Method | Time |
|---|---|---|
| Two Sum (indices, unsorted) | hash map of value → index | O(n) |
| Two Sum (sorted array) | two pointers | O(n) |
| 3Sum | sort + two pointers per element | O(n²) |
| 3Sum closest | same, track the smallest |sum − target| | O(n²) |
| 4Sum | two nested loops + two pointers | O(n³) |

**Pitfalls:** duplicate triplets (the skips), overflow when adding three large ints (use `long`), and the early exit `if (a[i] > 0) break;` (all later values are positive).

#### Two-pointer trace

Sorted input: [-4,-1,-1,0,1,2]. Fix the first -1. With left=-1 and right=2 the sum is zero; output [-1,-1,2]. Move both endpoints and skip duplicates, then left=0 and right=1 also sum to zero. A negative sum requires increasing the left value; a positive sum requires decreasing the right value. Sorting changes the original array. If original indices are required, sort value/index pairs and specify how duplicate index combinations should be reported. The O(n²) scan dominates an O(n log n) sorting implementation.

### Find the duplicate number in an array of n+1 integers in the range 1..n. {M}
**Short answer:** Because every value is between 1 and n, treat each value as a pointer to the index with that number: `i → a[i]`. Starting from index 0 this forms a linked list that must contain a cycle, and the duplicate value is exactly where two pointers enter the same node — the cycle entrance. Floyd's tortoise-and-hare finds it in O(n) time with O(1) space, without modifying the array.

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

**Dry run for `{1, 3, 4, 2, 2}`**

Following `x = a[x]` from 0: 0 → 1 → 3 → 2 → 4 → 2 → 4 → … The cycle is 2 → 4 → 2, entered at node 2.

- Phase 1: slow moves 1 step, fast 2 steps, until they meet inside the cycle (here at 4 or 2).
- Phase 2: reset slow to 0, move both 1 step at a time: they meet at **2**, the duplicate.

**Why the entrance is the duplicate:** the entrance node has two incoming "pointers" (two different indices with the same value). Only a repeated value can give a node two predecessors.

**Why phase 2 works:** if the distance from the start to the entrance is μ and the cycle length is λ, at the meeting point the fast pointer has gone an extra multiple of λ, which makes μ steps from the meeting point land on the entrance — the same μ steps the reset pointer needs from the start.

**Alternatives and their trade-offs**

| Method | Time | Space | Array changed |
|---|---|---|---|
| Nested loops | O(n²) | O(1) | no |
| Sort then scan | O(n log n) | O(1) | yes |
| Seen bitmap | O(n) | O(n) bits | no |
| Negate `a[abs(x)]` as a visited mark | O(n) | O(1) | yes (temporarily) |
| Binary search on value counts | O(n log n) | O(1) | no |
| Floyd | O(n) | O(1) | no |

**Related:** missing number from 1..n (sum or XOR formula), find all duplicates where values are in range (index-marking trick).

#### Interpreting array values as links

For [1,3,4,2,2], index 0 leads to 1, then 3, then 2, then 4, then back to 2. The cycle entry is the duplicate value 2. Because index 0 is never a value, traversal begins outside the cycle. Floyd's two phases find a meeting point and then the cycle entry without modifying the array. The input must contain n+1 values in [1,n] and one distinct repeated value. Out-of-range values can cause illegal indexing, so validate the domain if not guaranteed by the question.

