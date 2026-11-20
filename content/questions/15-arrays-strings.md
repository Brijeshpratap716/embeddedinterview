---
slug: arrays-strings
title: Arrays & Strings (Coding Round)
icon: 🔤
level: Beginner
order: 13
desc: The classic whiteboard programs in C: second largest, rotate, leaders, Kadane, sliding window, trapping rain water, palindromes, anagrams and reversing words.
---
These are the programs embedded companies ask in the first coding round, usually "write it in C on paper or in a shared editor". The interviewer checks three things: a correct loop with no out-of-bounds access, the edge cases (empty array, one element, all negative, duplicates), and the time and space complexity. Each answer gives working C code, a dry run, the common mistakes, and the follow-up questions. Write functions that take the array and its length instead of hard-coding sizes inside `main`.

### How do you find the missing number in an array containing 1 to n? {E}
**Short answer:** An array holds `n - 1` distinct numbers from 1 to `n` with one missing. Compute the expected sum `n(n+1)/2` and subtract every element; what is left is the missing number. XOR-ing gives the same answer without any risk of overflow.

```c
#include <stddef.h>

/* arr has n-1 elements, values 1..n with one missing */
unsigned missing_sum(const unsigned *arr, unsigned n)
{
    unsigned long long total = (unsigned long long)n * (n + 1) / 2;
    for (unsigned i = 0; i < n - 1; i++)
        total -= arr[i];
    return (unsigned)total;
}

unsigned missing_xor(const unsigned *arr, unsigned n)
{
    unsigned x = 0;
    for (unsigned i = 1; i <= n; i++) x ^= i;        /* XOR of 1..n          */
    for (unsigned i = 0; i < n - 1; i++) x ^= arr[i]; /* cancel present ones  */
    return x;
}
/* {1, 2, 4, 5, 6}, n = 6 -> 3 */
```

**Dry run (sum method):** `n = 6`, expected sum `21`. Elements sum to `1+2+4+5+6 = 18`. `21 - 18 = 3`.

**Watch the length.** A common version is `findMissingNumber(arr, n)` with the loop running `i < n`. That only works if `n` is the **array length** and the range is `1..n+1`. Be explicit about which `n` you mean: "the array has n−1 elements and the numbers run from 1 to n".

**Overflow:** `n * (n + 1)` overflows a 32-bit `int` once `n` passes about 46,000. Widening to 64-bit, subtracting as you go, or using XOR all avoid it. With XOR every value stays in range because XOR never grows the number.

**Complexity:** O(n) time, O(1) extra space. Sorting first would be O(n log n); a "seen" array would use O(n) memory.

**Follow-ups**

- *Two numbers missing:* XOR gives `a ^ b`; split by any set bit (as in "two unique numbers") to separate them. Or use both the sum and the sum of squares.
- *Array not guaranteed valid (duplicates possible):* use the cyclic-sort idea (place each value `v` at index `v-1`) or a bitmap.

### How do you find the second largest element in an array? {E}
**Short answer:** Scan once, keeping `largest` and `second`. When a value beats `largest`, the old largest becomes `second`; when a value is between them (and not equal to `largest`), it becomes `second`. Start both at `INT_MIN`, not 0, so negative arrays work.

```c
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>

/* returns false if there is no distinct second largest */
bool second_largest(const int *arr, size_t n, int *out)
{
    int first = INT_MIN, second = INT_MIN;
    bool found = false;

    for (size_t i = 0; i < n; i++) {
        if (arr[i] > first) {
            second = first;
            first = arr[i];
            if (i > 0) found = true;          /* a previous value now sits in second */
        } else if (arr[i] < first && (arr[i] > second || !found)) {
            second = arr[i];
            found = true;
        }
    }
    if (found) *out = second;
    return found;
}
/* {96, 54, 4, 69, 4, 6, 3, 4, 0} -> 69 */
```

**Dry run for {96, 54, 69}:** 96 → first=96. 54 → between, second=54. 69 → between and > 54, second=69. Answer 69.

**Mistakes interviewers look for**

1. **Initialising to 0.** `int max = 0, sec = 0;` gives the wrong answer for `{-5, -2, -9}` (it returns 0, which is not in the array). Use `INT_MIN` or the first element.
2. **Duplicates of the maximum.** For `{7, 7, 3}` the second largest *distinct* value is 3. The `arr[i] < first` check stops the second 7 from being taken.
3. **No answer exists:** an array of one element or all equal values. Return a status instead of a magic number.

**Complexity:** O(n) time and O(1) space, one pass. Sorting (O(n log n)) and picking the second-from-end is acceptable only if the interviewer allows it, and you still need to skip duplicates.

**Follow-up:** "k-th largest?" Use a min-heap of size k (O(n log k)) or quickselect (average O(n)).

### How do you check whether an array is sorted? {E}
**Short answer:** Compare each element with the one before it, starting at index 1. If any `arr[i] < arr[i-1]`, it is not sorted (for non-decreasing order). Return as soon as you find a violation.

```c
#include <stdbool.h>
#include <stddef.h>

bool is_sorted(const int *arr, size_t n)
{
    for (size_t i = 1; i < n; i++)        /* start at 1: arr[i-1] must exist */
        if (arr[i] < arr[i - 1])
            return false;
    return true;                           /* 0 or 1 element: sorted */
}
```

**Common bug.** This version reads outside the array:

```c
for (int i = 0; i < 6; i++) {
    if (arr[i] > arr[i - 1]) { }           /* i = 0 reads arr[-1]: undefined behaviour */
    else printf("Not Sorted");             /* also prints once per violation */
}
```

Two problems: `arr[-1]` is out of bounds (it may read a random stack value and print "Not Sorted" for a sorted array), and it prints a message for every violation instead of returning a single answer. Also, `>` makes `{1, 2, 2, 3}` count as unsorted; use `<` in the failing test so that equal neighbours are allowed.

**Decide what "sorted" means:** strictly increasing (`arr[i] <= arr[i-1]` fails), non-decreasing (above), or either direction (check the first unequal pair to find the direction, then check the rest).

**Recursive version** (often asked as a follow-up):

```c
bool is_sorted_rec(const int *a, size_t n)
{
    return n < 2 || (a[n - 1] >= a[n - 2] && is_sorted_rec(a, n - 1));
}
```

It is O(n) deep, so on a microcontroller with a small stack the loop is the right answer.

**Complexity:** O(n) worst case, O(1) best case (first pair fails), O(1) space.

### How do you reverse an array in place? {E}
**Short answer:** Use two indices, `low` at the start and `high` at the end. Swap the elements, move `low` up and `high` down, and stop when they meet. O(n) time, O(1) extra space.

```c
#include <stddef.h>

void reverse_array(int *arr, size_t n)
{
    if (n < 2) return;
    size_t low = 0, high = n - 1;
    while (low < high) {
        int tmp = arr[low];
        arr[low] = arr[high];
        arr[high] = tmp;
        low++;
        high--;
    }
}
/* {1, 3, 5, 7, 8, 9} -> {9, 8, 7, 5, 3, 1} */
```

**Dry run for {1, 3, 5, 7, 8, 9}:** swap (0,5) → 9 3 5 7 8 1; swap (1,4) → 9 8 5 7 3 1; swap (2,3) → 9 8 7 5 3 1; `low = 3`, `high = 2`, stop. Three swaps for six elements: `n/2` swaps.

**Why `n < 2` first:** with `size_t` (unsigned), `n - 1` for an empty array wraps to `SIZE_MAX` and `high` points far outside the array. Hard-coding `high = 5` in `main` hides this problem; pass the length in.

**Why `low < high` and not `low <= high`:** when they are equal (odd length), the middle element would be swapped with itself, which is harmless but wasted work.

**Pointer version:**

```c
void reverse_ptr(int *first, int *last)   /* last points at the final element */
{
    while (first < last) {
        int t = *first; *first++ = *last; *last-- = t;
    }
}
```

**Where reversal is used:** as the building block for rotating an array, reversing words in a string, and converting between byte orders in a buffer.

### How do you remove duplicates from a sorted array in place? {E}
**Short answer:** Because the array is sorted, duplicates are next to each other. Keep a write index `k` pointing at the last unique value; for each new element that differs from `arr[k]`, increment `k` and copy it there. The new length is `k + 1`.

```c
#include <stddef.h>

size_t remove_duplicates(int *arr, size_t n)
{
    if (n == 0) return 0;
    size_t k = 0;                      /* arr[0..k] are the unique values */
    for (size_t i = 1; i < n; i++) {
        if (arr[i] != arr[k]) {
            k++;
            arr[k] = arr[i];
        }
    }
    return k + 1;                      /* new length */
}
/* {1, 3, 3, 5, 5, 6, 9} -> {1, 3, 5, 6, 9}, returns 5 */
```

**Dry run**

| i | arr[i] | arr[k] | action | unique part |
|---|---|---|---|---|
| 1 | 3 | 1 | k=1, copy | 1 3 |
| 2 | 3 | 3 | skip | 1 3 |
| 3 | 5 | 3 | k=2, copy | 1 3 5 |
| 4 | 5 | 5 | skip | 1 3 5 |
| 5 | 6 | 5 | k=3, copy | 1 3 5 6 |
| 6 | 9 | 6 | k=4, copy | 1 3 5 6 9 |

**Report the new length.** A common slip is printing the original `size` after removing duplicates. The caller needs `k + 1`; the values after that index are leftovers and should be ignored.

**Complexity:** O(n) time, O(1) extra space. Each element is read once and written at most once.

**Follow-ups**

- *Unsorted array:* sort first (O(n log n)), or use a hash set / bitmap of seen values (O(n) time, O(n) memory).
- *Allow each value at most twice:* compare with `arr[k-1]` instead of `arr[k]`.
- *Do not change order of first occurrences in an unsorted array:* hash set of seen values while copying.

### How do you move all zeros to the end of an array? {E}
**Short answer:** Keep a write index for the next non-zero position. Walk the array; whenever you see a non-zero value, swap it into the write index and advance it. Zeros end up at the back and the non-zero values keep their original order. O(n) time, O(1) space.

```c
#include <stddef.h>

void move_zeros_to_end(int *arr, size_t n)
{
    size_t nz = 0;                         /* next slot for a non-zero value */
    for (size_t i = 0; i < n; i++) {
        if (arr[i] != 0) {
            int t = arr[i];
            arr[i] = arr[nz];
            arr[nz] = t;
            nz++;
        }
    }
}
/* {0, 8, 0, 1, 11, 0, 10, 0, 1} -> {8, 1, 11, 10, 1, 0, 0, 0, 0} */
```

**Why it keeps the order:** non-zero values are placed at `nz = 0, 1, 2, ...` in the order they are met. Everything between `nz` and `i` is zero, so the swap only ever moves a zero backward.

**Fewer writes version:** copy non-zeros forward, then fill the tail with zeros. This does at most `n` writes instead of up to `2n`, which matters when writing to slow memory or flash.

```c
void move_zeros_copy(int *arr, size_t n)
{
    size_t nz = 0;
    for (size_t i = 0; i < n; i++)
        if (arr[i] != 0) arr[nz++] = arr[i];
    while (nz < n) arr[nz++] = 0;
}
```

**Edge cases:** all zeros (nothing moves), no zeros (each element swaps with itself; add `if (i != nz)` to skip self-swaps), empty array.

**Related problems with the same pattern:** remove all occurrences of a value, partition even and odd numbers, and the partition step of quicksort. They are all "two pointers: one reads, one writes".

### How do you rotate an array by d positions? {M}
**Short answer:** Use the reversal algorithm. To rotate left by `d`: reverse the first `d` elements, reverse the rest, then reverse the whole array. It runs in O(n) time with O(1) extra memory. Reduce `d` with `d %= n` first.

```c
#include <stddef.h>

static void reverse_range(int *a, size_t lo, size_t hi)   /* inclusive */
{
    while (lo < hi) {
        int t = a[lo]; a[lo] = a[hi]; a[hi] = t;
        lo++; hi--;
    }
}

void rotate_left(int *a, size_t n, size_t d)
{
    if (n == 0) return;
    d %= n;
    if (d == 0) return;
    reverse_range(a, 0, d - 1);
    reverse_range(a, d, n - 1);
    reverse_range(a, 0, n - 1);
}
/* {1, 2, 3, 4, 5, 6}, d = 2 -> {3, 4, 5, 6, 1, 2} */
```

**Dry run (d = 2):**

```
start          1 2 | 3 4 5 6
reverse [0,1]  2 1 | 3 4 5 6
reverse [2,5]  2 1 | 6 5 4 3
reverse all    3 4 5 6 1 2
```

**Why it works:** write the array as `A B` where `A` is the first `d` elements. We want `B A`. Reversing each part gives `Aʳ Bʳ`, and reversing the whole thing gives `(Aʳ Bʳ)ʳ = B A`.

**Right rotation by d** is left rotation by `n - d`, or reverse the whole array first and then the two parts.

**Other methods**

| Method | Time | Extra space |
|---|---|---|
| Rotate by one, d times | O(n·d) | O(1) |
| Copy to a temp array | O(n) | O(n) or O(d) |
| Juggling (GCD cycles) | O(n) | O(1) |
| **Reversal** | **O(n)** | **O(1)** |

**Forgetting `d %= n`** is the usual bug: with `d = 8` and `n = 6`, `reverse_range(a, 0, 7)` writes past the array.

**Embedded relevance:** the same idea rotates a circular log buffer into chronological order before sending it, without a second buffer.

### How do you find the leaders in an array? {E}
**Short answer:** A leader is an element greater than every element to its right; the last element is always a leader. Scan from right to left, tracking the maximum seen so far, and print an element whenever it is greater than that maximum. O(n) time, O(1) space.

```c
#include <stdio.h>
#include <stddef.h>

void print_leaders(const int *arr, size_t n)
{
    if (n == 0) return;
    int max_right = arr[n - 1];
    printf("%d ", max_right);                 /* last element is a leader */
    for (size_t i = n - 1; i-- > 0; ) {       /* i = n-2 down to 0 */
        if (arr[i] > max_right) {
            max_right = arr[i];
            printf("%d ", arr[i]);
        }
    }
    printf("\n");
}
/* {7, 10, 4, 3, 6, 5, 2} -> prints 2 5 6 10 (right to left) */
```

**Dry run for {7, 10, 4, 3, 6, 5, 2}:** start with 2 (leader). 5 > 2 → leader, max=5. 6 > 5 → leader, max=6. 3, 4 no. 10 > 6 → leader, max=10. 7 no. Leaders: 10, 6, 5, 2.

**Order of output.** Scanning from the right prints leaders in reverse. If the interviewer wants left-to-right order, store them in an array and print it backwards, or use a stack.

**Strict or not:** with `>` an element equal to a later maximum is not a leader; with `>=` it is. Ask which definition they want; it changes the answer for arrays with repeated values.

**The naive solution** checks every element against all elements to its right: O(n²). Mention it, then give the O(n) version.

**Loop detail:** `for (size_t i = n - 1; i-- > 0; )` is a safe way to count down with an unsigned index. Writing `for (size_t i = n - 2; i >= 0; i--)` never ends because `i >= 0` is always true for `size_t`. With `int` indices you can write the obvious loop.

### How do you find the maximum difference arr[j] - arr[i] with j > i? {M}
**Short answer:** Scan left to right, keeping the minimum value seen so far. At each element compute `arr[j] - min_so_far` and keep the largest. One pass, O(n) time, O(1) space. This is the same as "best time to buy and sell a stock once".

```c
#include <stddef.h>

/* n >= 2 */
int max_difference(const int *arr, size_t n)
{
    int min_so_far = arr[0];
    int best = arr[1] - arr[0];
    for (size_t j = 1; j < n; j++) {
        if (arr[j] - min_so_far > best)
            best = arr[j] - min_so_far;
        if (arr[j] < min_so_far)
            min_so_far = arr[j];
    }
    return best;
}
/* {2, 3, 10, 6, 4, 8, 1} -> 8  (10 - 2) */
```

**Dry run**

| j | arr[j] | min before | arr[j]-min | best |
|---|---|---|---|---|
| 1 | 3 | 2 | 1 | 1 |
| 2 | 10 | 2 | 8 | 8 |
| 3 | 6 | 2 | 4 | 8 |
| 4 | 4 | 2 | 2 | 8 |
| 5 | 8 | 2 | 6 | 8 |
| 6 | 1 | 2 | -1 | 8 |

**Why the order of the two `if`s matters:** compute the difference before updating the minimum, so `j > i` holds. Starting the loop at `j = 1` avoids comparing an element with itself.

**Why initialise `best = arr[1] - arr[0]` and not 0:** for a strictly decreasing array such as `{9, 7, 4}`, the correct answer is `-2`. Starting at 0 would report a difference that does not exist. (If the question is "maximum profit", where not trading is allowed, 0 is correct; clarify.)

**Naive version:** two nested loops over all pairs, O(n²).

**Follow-up:** "Return the indices too": store the index whenever `min_so_far` changes and record `(min_index, j)` whenever `best` improves.

### How do you find the longest subarray of alternating even and odd numbers? {M}
**Short answer:** Walk the array once with a running count. If the current element has a different parity from the previous one, extend the run (`count++`); otherwise restart it at 1. Track the maximum. O(n) time, O(1) space.

```c
#include <stddef.h>

size_t longest_even_odd(const int *arr, size_t n)
{
    if (n == 0) return 0;
    size_t best = 1, count = 1;
    for (size_t i = 1; i < n; i++) {
        if ((arr[i] % 2 == 0) != (arr[i - 1] % 2 == 0)) {   /* parity changed */
            count++;
            if (count > best) best = count;
        } else {
            count = 1;
        }
    }
    return best;
}
/* {5, 10, 20, 6, 3, 8} -> 3  (6, 3, 8) */
/* {10, 12, 8, 4}       -> 1 */
```

**Simplifying the condition.** The long form `((a%2==0) && (b%2!=0)) || ((a%2!=0) && (b%2==0))` is "exactly one of them is even", which is a single inequality of two booleans: `(a % 2 == 0) != (b % 2 == 0)`. A bitwise version is `((a ^ b) & 1) != 0`: the lowest bits differ exactly when the parities differ, and it works for negative numbers in two's complement.

**Negative numbers:** `-3 % 2` is `-1` in C, so a test like `a % 2 == 1` treats -3 as even. Comparing with `== 0` (or using `& 1`) avoids this.

**Dry run for {5, 10, 20, 6, 3, 8}:** 5→10 change (2), 10→20 same (reset 1), 20→6 same (1), 6→3 change (2), 3→8 change (3). Answer 3.

**Pattern:** this is the "longest run satisfying a condition between neighbours" template. The same loop solves "longest increasing contiguous run", "max consecutive ones" and "longest run of equal values".

### How do you count the frequency of each element in a sorted array? {E}
**Short answer:** Equal values are adjacent in a sorted array, so walk once with a counter: increment while the value stays the same, and print the value and count when it changes. Print the final run after the loop. O(n) time, O(1) space.

```c
#include <stdio.h>
#include <stddef.h>

void print_frequencies(const int *arr, size_t n)
{
    if (n == 0) return;
    size_t count = 1;
    for (size_t i = 1; i < n; i++) {
        if (arr[i] == arr[i - 1]) {
            count++;
        } else {
            printf("%d occurs %zu times\n", arr[i - 1], count);
            count = 1;
        }
    }
    printf("%d occurs %zu times\n", arr[n - 1], count);   /* last run */
}
/* {10, 10, 10, 10, 30, 30} -> 10 occurs 4 times, 30 occurs 2 times */
```

**The last group is the classic slip.** The loop only prints when the value *changes*, so the final run never triggers it. You must print it after the loop, using `arr[n - 1]`, not a hard-coded index like `arr[5]`, which breaks for any other length.

**Unsorted arrays**

- Small known range (e.g. ADC codes 0–255, characters): a count array `count[256]`, O(n + range).
- Arbitrary values: sort first (O(n log n)), or a hash map.

**Follow-up: count of one value in a sorted array in O(log n).** Binary search for the first and the last occurrence; the count is `last - first + 1`.

```c
/* first index with a[i] >= key */
size_t lower_bound(const int *a, size_t n, int key)
{
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (a[mid] < key) lo = mid + 1; else hi = mid;
    }
    return lo;
}
/* count = lower_bound(a, n, key + 1) - lower_bound(a, n, key)  (if key < INT_MAX) */
```

### How do you calculate the maximum profit from buying and selling a stock? {M}
**Short answer:** If you may make as many buy-sell trades as you like (holding at most one share at a time), add up every positive day-to-day increase: `profit += max(0, price[i] - price[i-1])`. If only one trade is allowed, track the minimum price so far and the best `price - min` (the maximum-difference problem).

```c
#include <stddef.h>

/* unlimited transactions */
int max_profit_many(const int *price, size_t n)
{
    int profit = 0;
    for (size_t i = 1; i < n; i++)
        if (price[i] > price[i - 1])
            profit += price[i] - price[i - 1];
    return profit;
}
/* {1, 5, 3, 1, 2, 8} -> (5-1) + (2-1) + (8-2) = 4 + 1 + 6 = 11 */

/* one transaction (0 if prices only fall) */
int max_profit_one(const int *price, size_t n)
{
    if (n == 0) return 0;
    int min_price = price[0], best = 0;
    for (size_t i = 1; i < n; i++) {
        if (price[i] - min_price > best) best = price[i] - min_price;
        if (price[i] < min_price) min_price = price[i];
    }
    return best;
}
/* {1, 5, 3, 1, 2, 8} -> 7 (buy at 1, sell at 8) */
```

**Why summing the rises is optimal:** any profitable trade from day `a` to day `b` equals the sum of the daily changes between them. Taking only the positive changes is at least as good as any combination of trades, and it can be achieved by buying before each rise and selling after it.

**Use the length you are given.** A version that declares `n = 5` but loops to a hard-coded 6 works by accident; pass `n` and loop `i < n`.

**Dry run, unlimited:** 1→5 (+4), 5→3 (skip), 3→1 (skip), 1→2 (+1), 2→8 (+6). Total 11.

**Follow-ups:** at most two transactions (track four states: first buy, first sell, second buy, second sell), a transaction fee (subtract the fee on each sell), or a cooldown day. These become small dynamic-programming state machines.

### How do you solve the trapping rain water problem? {H}
**Short answer:** Water above bar `i` is `min(max height to the left, max height to the right) - height[i]`, if positive. Precompute left-max and right-max arrays (O(n) time, O(n) space), or use two pointers to do it in O(1) space.

```c
#include <stddef.h>

/* two-pointer version: O(n) time, O(1) space */
int trap_water(const int *h, size_t n)
{
    if (n < 3) return 0;
    size_t lo = 0, hi = n - 1;
    int left_max = 0, right_max = 0, water = 0;

    while (lo < hi) {
        if (h[lo] < h[hi]) {               /* left side is the limit */
            if (h[lo] >= left_max) left_max = h[lo];
            else water += left_max - h[lo];
            lo++;
        } else {                           /* right side is the limit */
            if (h[hi] >= right_max) right_max = h[hi];
            else water += right_max - h[hi];
            hi--;
        }
    }
    return water;
}
/* {3, 0, 6, 2, 5} -> 3 + 3 = 6 */
```

**Prefix-max version (easier to explain first):**

```c
int trap_water_arrays(const int *h, size_t n)
{
    if (n < 3) return 0;
    int left[n], right[n], water = 0;          /* VLA: fine on a PC, avoid on an MCU */
    left[0] = h[0];
    for (size_t i = 1; i < n; i++) left[i] = h[i] > left[i - 1] ? h[i] : left[i - 1];
    right[n - 1] = h[n - 1];
    for (size_t i = n - 1; i-- > 0; ) right[i] = h[i] > right[i + 1] ? h[i] : right[i + 1];
    for (size_t i = 1; i + 1 < n; i++) {
        int level = left[i] < right[i] ? left[i] : right[i];
        if (level > h[i]) water += level - h[i];
    }
    return water;
}
```

**Dry run for {3, 0, 6, 2, 5}:**

| i | h | left max | right max | level | water |
|---|---|---|---|---|---|
| 1 | 0 | 3 | 6 | 3 | 3 |
| 2 | 6 | 6 | 6 | 6 | 0 |
| 3 | 2 | 6 | 5 | 5 | 3 |

Total 6.

**Why two pointers work:** if `h[lo] < h[hi]`, there is a bar on the right at least as tall as `h[lo]`, so the water at `lo` depends only on `left_max`. We can settle position `lo` and move on, and likewise for the right side.

**Embedded note:** the array version allocates two `n`-sized arrays; on a microcontroller that is a lot of stack (and VLAs are best avoided there). The two-pointer version uses three integers.

### How do you find the maximum number of consecutive 1s in a binary array? {E}
**Short answer:** Keep a running count of 1s, reset it to 0 on every 0, and remember the largest count seen. One pass, O(n) time, O(1) space.

```c
#include <stddef.h>

size_t max_consecutive_ones(const int *arr, size_t n)
{
    size_t count = 0, best = 0;
    for (size_t i = 0; i < n; i++) {
        if (arr[i] == 1) {
            count++;
            if (count > best) best = count;
        } else {
            count = 0;
        }
    }
    return best;
}
/* {0,1,1,1,1,0,1,1,1,1,1,1,0,0,1,0} -> 6 */
```

**Why update `best` inside the 1 branch:** if the array ends with a run of 1s, there is no 0 afterwards to trigger a final comparison. Updating as you go avoids a separate check after the loop.

**Bit-level version** (popular in firmware interviews: longest run of 1s in a 32-bit register):

```c
unsigned longest_run_of_ones(uint32_t x)
{
    unsigned n = 0;
    while (x) {
        x &= x << 1;      /* each step shortens every run by one */
        n++;
    }
    return n;
}
/* 0b0111_1011 -> 4 */
```

Each `x &= x << 1` removes the lowest 1 of every run, so the number of iterations equals the length of the longest run.

**Follow-ups**

- *Flip at most one 0 to maximise the run:* sliding window that allows at most one 0 inside; when a second 0 enters, move the left edge past the first 0.
- *At most k zeros:* the same window with a zero counter.
- Real use: finding the longest free block in an allocation bitmap.

### How do you find the maximum sum of k consecutive elements (sliding window)? {M}
**Short answer:** Sum the first `k` elements; that is the first window and the first candidate for the maximum. Then slide: add the element entering the window and subtract the one leaving (`sum += a[i] - a[i-k]`), updating the maximum each time. O(n) instead of O(n·k).

```c
#include <stddef.h>

/* 1 <= k <= n */
long max_window_sum(const int *a, size_t n, size_t k)
{
    long sum = 0;
    for (size_t i = 0; i < k; i++)
        sum += a[i];
    long best = sum;                       /* the first window counts too */
    for (size_t i = k; i < n; i++) {
        sum += a[i] - a[i - k];
        if (sum > best) best = sum;
    }
    return best;
}
/* {1, 8, 30, -5, 20, 7}, k = 3 -> 45  (30 - 5 + 20) */
```

**Dry run (k = 3):** first window 1+8+30 = 39 (best 39). Slide: +(-5) -1 = 33. +20 -8 = 45 (best 45). +7 -30 = 22. Answer 45.

**The bug to avoid.** Initialising `maxSum = 0` and only comparing inside the sliding loop has two problems: the first window is never considered (wrong if it is the biggest), and if every window sum is negative the function returns 0. Set `best` to the first window's sum.

**Overflow:** the running sum of many `int` values can overflow; use a wider accumulator (`long` or `int64_t`).

**Embedded uses of the same idea**

- **Moving-average filter:** keep a ring buffer of the last `k` samples and a running sum; each new sample adds one value and subtracts the oldest. Dividing by `k` gives the average. With `k` a power of two, the division is a shift.
- **Rate limiting:** count events in the last `k` milliseconds.

**Follow-ups:** variable-size window ("smallest subarray with sum ≥ S": grow the right edge, shrink the left edge while the condition holds), and "maximum in every window of size k" (deque of indices, O(n)).

### How do you check if a string is a palindrome? {E}
**Short answer:** Compare characters from both ends moving inward: `s[low]` with `s[high]`. If any pair differs, it is not a palindrome. O(n) time, O(1) space.

```c
#include <stdbool.h>
#include <string.h>

bool is_palindrome(const char *s)
{
    size_t len = strlen(s);
    if (len < 2) return true;
    size_t low = 0, high = len - 1;
    while (low < high) {
        if (s[low] != s[high])
            return false;
        low++;
        high--;
    }
    return true;
}
/* "ABCKCBA" -> true, "ABCA" -> false */
```

**Finding the length.** Counting with `while (str[count] != '\0') count++;` is fine and is exactly what `strlen` does. Use `high = len - 1`, not `len`: index `len` is the terminating `'\0'`.

**Edge cases:** empty string and one character are palindromes. With `size_t`, guard `len < 2` before `len - 1`.

**Variant: ignore case and non-letters** ("A man, a plan, a canal: Panama"):

```c
#include <ctype.h>

bool is_palindrome_alnum(const char *s)
{
    size_t lo = 0, hi = strlen(s);
    while (lo < hi) {
        while (lo < hi && !isalnum((unsigned char)s[lo])) lo++;
        while (lo < hi && !isalnum((unsigned char)s[hi - 1])) hi--;
        if (lo < hi && tolower((unsigned char)s[lo]) != tolower((unsigned char)s[hi - 1]))
            return false;
        lo++; hi--;
    }
    return true;
}
```

The `(unsigned char)` cast matters: passing a negative `char` (bytes ≥ 0x80 on platforms where `char` is signed) to `isalnum` is undefined behaviour.

**Follow-ups:** palindrome number without converting to a string (reverse half the digits), and "is a linked list a palindrome" (find the middle, reverse the second half, compare).

### How do you check whether one string is a subsequence of another? {E}
**Short answer:** Walk through the long string with one index and the short string with another. Each time the characters match, advance the short-string index. If you reach the end of the short string, it is a subsequence. O(n) time, O(1) space.

```c
#include <stdbool.h>

/* is 'sub' a subsequence of 's'? */
bool is_subsequence(const char *s, const char *sub)
{
    while (*s && *sub) {
        if (*s == *sub)
            sub++;                 /* matched one character of sub */
        s++;
    }
    return *sub == '\0';           /* consumed all of sub */
}
/* is_subsequence("ABCD", "AC") -> true
   is_subsequence("ABCD", "CA") -> false (order matters) */
```

**Subsequence vs substring:** a subsequence keeps the order but may skip characters ("AC" in "ABCD"); a substring must be contiguous ("BC" in "ABCD").

**Problems with a hard-coded version.** Code that uses `size1 = 4, size2 = 2` and tests `j == 2` only works for those two strings. It also keeps comparing after all of `sub` has matched: then `str2[j]` is `'\0'`, which never equals a character, so it happens to be harmless here, but if the index goes past the terminator it reads out of bounds. Use the string terminators (or lengths passed in) and stop when `sub` is finished.

**Dry run "ABCD" / "AC":** A=A (sub→C), B≠C, C=C (sub→end). Return true.

**Greedy is optimal:** matching each character of `sub` as early as possible never hurts, because it leaves the most of `s` for the remaining characters.

**Follow-ups**

- *Many queries against the same long string:* precompute, for each character, the sorted list of its positions, then binary search the next position after the current one: O(m log n) per query.
- *Longest common subsequence:* dynamic programming, O(n·m).

### How do you check if two strings are anagrams? {E}
**Short answer:** Two strings are anagrams if they contain the same characters with the same counts. Count each character of the first string up and each character of the second down in a 256-entry table; they are anagrams if every count ends at zero. O(n) time, O(1) space (fixed table).

```c
#include <stdbool.h>
#include <string.h>

bool is_anagram(const char *s1, const char *s2)
{
    if (strlen(s1) != strlen(s2)) return false;   /* quick reject */
    int freq[256] = {0};
    for (const char *p = s1; *p; p++) freq[(unsigned char)*p]++;
    for (const char *p = s2; *p; p++) freq[(unsigned char)*p]--;
    for (int i = 0; i < 256; i++)
        if (freq[i] != 0) return false;
    return true;
}
/* "listen", "silent" -> true */
```

**The `(unsigned char)` cast is important.** On most Arm Linux compilers `char` is unsigned, but on x86 and many others it is signed. A byte such as `0xE9` ('é' in Latin-1) is then `-23`, and `freq[s1[i]]` writes to `freq[-23]`, outside the array. Casting to `unsigned char` keeps the index in 0..255.

**Why check lengths first:** it rejects most non-anagrams immediately. It is not required for correctness, because the counts would not all be zero anyway.

**Alternatives**

| Method | Time | Space |
|---|---|---|
| Sort both, compare | O(n log n) | O(1)–O(n) |
| Count table | O(n) | O(256) |
| Product of primes | O(n) | O(1), but overflows quickly |

**Variants:** ignore case and spaces (`tolower`, skip `' '`), or only lowercase letters (`int freq[26]`, index `c - 'a'`). "Group words that are anagrams of each other" uses the sorted word or the count signature as a hash key.

### How do you reverse a string in place? {E}
**Short answer:** Find the length, then swap characters from both ends moving inward, stopping when the indices meet. Do not swap the `'\0'` terminator. O(n) time, O(1) space.

```c
#include <string.h>

void reverse_string(char *s)
{
    size_t len = strlen(s);
    if (len < 2) return;
    size_t low = 0, high = len - 1;         /* last real character, not '\0' */
    while (low < high) {
        char t = s[low];
        s[low] = s[high];
        s[high] = t;
        low++;
        high--;
    }
}
/* "hello world" -> "dlrow olleh" */
```

**Do not hard-code `high = 10`.** It works only for an 11-character string. Compute it from the length.

**It must be writable memory.**

```c
char a[] = "hello";   /* array copy on the stack: reversing is fine */
char *p  = "hello";   /* points to a string literal: writing is undefined behaviour */
```

On a desktop the second one usually crashes (literals are in a read-only section). On a microcontroller the literal is in flash and the write silently does nothing or raises a fault.

**Recursive version** (a common follow-up), O(n) stack depth:

```c
void reverse_rec(char *s, size_t lo, size_t hi)
{
    if (lo >= hi) return;
    char t = s[lo]; s[lo] = s[hi]; s[hi] = t;
    reverse_rec(s, lo + 1, hi - 1);
}
```

**UTF-8 caveat:** reversing bytes breaks multi-byte characters such as "é" (two bytes). Reversing by code point requires decoding first. Mention it if the interviewer asks about real-world text.

### How do you reverse the order of words in a string? {M}
**Short answer:** Reverse the whole string, then reverse each word in place. "hello world" → "dlrow olleh" → "world hello". O(n) time, O(1) extra space.

```c
#include <string.h>

static void reverse_range(char *s, size_t lo, size_t hi)   /* inclusive */
{
    while (lo < hi) {
        char t = s[lo]; s[lo] = s[hi]; s[hi] = t;
        lo++; hi--;
    }
}

void reverse_words(char *s)
{
    size_t len = strlen(s);
    if (len == 0) return;
    reverse_range(s, 0, len - 1);           /* step 1: whole string */

    size_t start = 0;
    for (size_t i = 0; i <= len; i++) {     /* <= len: also handle the last word */
        if (s[i] == ' ' || s[i] == '\0') {
            if (i > start)
                reverse_range(s, start, i - 1);   /* step 2: each word */
            start = i + 1;
        }
    }
}
/* "hello world" -> "world hello" */
```

**Dry run:** `"hello world"` → whole reverse → `"dlrow olleh"` → reverse "dlrow" → "world", reverse "olleh" → "hello" → `"world hello"`.

**Details that catch people out**

- **The last word** is not followed by a space. Looping to `i <= len` and treating `'\0'` as a separator handles it.
- **Consecutive spaces:** `if (i > start)` skips empty "words", so `"a  b"` does not call reverse with `hi < lo`. With `size_t`, `i - 1` when `i == 0` would wrap to a huge number.
- **Leading, trailing or multiple spaces** that must be collapsed to one: do an extra compaction pass (two pointers, copy a single space between words).

**Why reverse twice?** Reversing the whole string puts the words in the right order but each word is backwards; the second pass fixes each word. It avoids a second buffer, which matters on a small MCU.

**Alternative with extra memory:** split into words (`strtok` or manual), then print them in reverse. Note that `strtok` modifies the string and is not reentrant (`strtok_r` is).

### How do you search for a pattern in a string (naive and KMP)? {M}
**Short answer:** The naive method tries every starting position `i` and compares the pattern character by character: O(n·m) in the worst case. KMP precomputes, for each prefix of the pattern, how far it can fall back after a mismatch, so the text is never rescanned: O(n + m).

```c
#include <stdio.h>
#include <string.h>

void search_naive(const char *text, const char *pat)
{
    size_t n = strlen(text), m = strlen(pat);
    if (m == 0 || m > n) return;            /* n - m would underflow with size_t */
    for (size_t i = 0; i <= n - m; i++) {
        size_t j = 0;
        while (j < m && text[i + j] == pat[j]) j++;
        if (j == m) printf("Pattern found at index %zu\n", i);
    }
}
/* text "geeksforgeeks", pattern "eks" -> indices 2 and 10 */
```

**The `size_t` trap:** `strlen` returns `size_t`. If the pattern is longer than the text, `n - m` wraps to a huge value and the loop reads far past the end. Check `m > n` first (or use signed `int` lengths as in many textbook versions).

**KMP (Knuth–Morris–Pratt)**

```c
void search_kmp(const char *text, const char *pat)
{
    size_t n = strlen(text), m = strlen(pat);
    if (m == 0) return;
    size_t lps[m];                           /* longest proper prefix that is also a suffix */
    lps[0] = 0;
    for (size_t i = 1, len = 0; i < m; ) {
        if (pat[i] == pat[len])      lps[i++] = ++len;
        else if (len)                len = lps[len - 1];
        else                         lps[i++] = 0;
    }
    for (size_t i = 0, j = 0; i < n; ) {
        if (text[i] == pat[j]) {
            i++; j++;
            if (j == m) { printf("found at %zu\n", i - m); j = lps[j - 1]; }
        } else if (j) {
            j = lps[j - 1];                  /* fall back in the pattern, not the text */
        } else {
            i++;
        }
    }
}
```

**When the naive method is worst:** text `"AAAAAAAAAB"` with pattern `"AAAB"` compares almost the whole pattern at every position.

**In practice:** `strstr()` finds the first occurrence and libraries use fast algorithms. In firmware, the common case is matching short tokens in a UART stream (e.g. waiting for `"OK\r\n"` from a modem); a small KMP-style state machine processes one byte at a time as it arrives, with no buffering.

**Other algorithms to name:** Rabin–Karp (rolling hash, good for many patterns), Boyer–Moore (skips ahead, fast on long patterns).

### How does bubble sort work, and how is it different from binary search? {E}
**Short answer:** Bubble sort repeatedly walks the array and swaps neighbouring elements that are in the wrong order, so the largest remaining value "bubbles" to the end on each pass. It is O(n²). Binary search is a different thing: it **finds** a key in an already sorted array by halving the search range, in O(log n).

```c
#include <stdbool.h>
#include <stddef.h>

void bubble_sort(int *a, size_t n)
{
    for (size_t pass = 0; pass + 1 < n; pass++) {
        bool swapped = false;
        for (size_t i = 0; i + 1 < n - pass; i++) {    /* last 'pass' items are done */
            if (a[i] > a[i + 1]) {
                int t = a[i]; a[i] = a[i + 1]; a[i + 1] = t;
                swapped = true;
            }
        }
        if (!swapped) break;           /* already sorted: best case O(n) */
    }
}

/* binary search: returns index or -1 */
long binary_search(const int *a, size_t n, int key)
{
    size_t lo = 0, hi = n;             /* search in [lo, hi) */
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;   /* avoids (lo + hi) overflow */
        if (a[mid] == key) return (long)mid;
        if (a[mid] < key) lo = mid + 1;
        else              hi = mid;
    }
    return -1;
}
/* {1, 2, 3, 5, 7, 11, 44, 234}, key 7 -> 4 */
```

**Name your functions for what they do.** A function called `bubbleshort` that actually performs a binary search confuses a reviewer immediately; interviewers notice.

**Bubble sort dry run, {5, 1, 4, 2}:** pass 1: 1 5 4 2 → 1 4 5 2 → 1 4 2 5. Pass 2: 1 4 2 5 → 1 2 4 5. Pass 3: no swaps, stop.

**Properties of bubble sort:** stable (equal values keep their order), in place (O(1) memory), O(n²) average and worst case, O(n) best case with the `swapped` flag. It is only reasonable for very small or nearly sorted arrays. Insertion sort has the same complexity but is usually faster in practice.

**Binary search notes:** the array must be sorted; `mid = lo + (hi - lo) / 2` avoids overflow of `lo + hi`; the half-open range `[lo, hi)` with `size_t` avoids the `high = mid - 1` underflow when `mid` is 0.
