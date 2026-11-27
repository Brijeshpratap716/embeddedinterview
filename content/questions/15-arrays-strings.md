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
When an array contains n−1 distinct numbers from 1 to n, XOR the expected numbers and actual elements. Equal values cancel.

```c
unsigned missing(const unsigned a[], size_t len)
{
    unsigned x = 0;
    for (size_t i = 0; i < len; ++i)
        x ^= (unsigned)(i + 1) ^ a[i];
    return x ^ (unsigned)(len + 1);
}
```
Assume len+1 fits unsigned and exactly one number is missing.

Example: [1, 2, 4, 5] → 3. The sum formula n(n+1)/2 also works but can overflow.

**Complexity:** O(n) time, O(1) space. XOR does not validate malformed input.

### How do you find the second largest element in an array? {E}
Track the largest and second-largest distinct values during one scan. Use flags rather than INT_MIN as a sentinel, because INT_MIN can be a valid result.

```c
bool second_largest(const int a[], size_t n, int *out)
{
    int first = 0, second = 0;
    bool f = false, s = false;
    for (size_t i = 0; i < n; ++i) {
        int x = a[i];
        if (!f || x > first) {
            if (f) { second = first; s = true; }
            first = x; f = true;
        } else if (x < first && (!s || x > second)) {
            second = x; s = true;
        }
    }
    if (s) *out = second;
    return s;
}
```

[4, 9, 9, 3] returns 4. [9, 9] returns false.

**Complexity:** O(n) time and O(1) space.

### How do you check whether an array is sorted? {E}
An array is nondecreasing if every element is at least its predecessor.

```c
bool sorted(const int a[], size_t n)
{
    for (size_t i = 1; i < n; ++i)
        if (a[i] < a[i-1])
            return false;
    return true;
}
```

[1, 2, 2, 5] is sorted; [1, 4, 3] is not. Empty and single-element arrays are sorted by convention. Change the comparison to <= for strictly increasing order.

**Complexity:** O(n) time, O(1) space; exits early on the first inversion.

### How do you reverse an array in place? {E}
Swap elements from the two ends and move toward the middle.

```c
void reverse(int a[], size_t n)
{
    for (size_t i = 0; i < n / 2; ++i) {
        int t = a[i];
        a[i] = a[n - 1 - i];
        a[n - 1 - i] = t;
    }
}
```

```text
1 2 3 4 5
5 2 3 4 1   swap ends
5 4 3 2 1   swap inner pair
```

**Complexity:** O(n) time, O(1) space. No unsigned underflow for n=0.

### How do you remove duplicates from a sorted array in place? {E}
Since equal values are adjacent in a sorted array, use a read index and a write index.

```c
size_t unique(int a[], size_t n)
{
    size_t w = 0;
    for (size_t r = 0; r < n; ++r)
        if (w == 0 || a[r] != a[w-1])
            a[w++] = a[r];
    return w;
}
```

[1, 1, 2, 2, 4] becomes [1, 2, 4, ...] with returned length 3. Elements after that length are unspecified for the caller's logical array.

**Complexity:** O(n) time, O(1) space. Sorted input is essential.

### How do you move all zeros to the end of an array? {E}
Preserve nonzero order by compacting nonzero elements, then fill the remainder with zeros.

```c
void move_zeros(int a[], size_t n)
{
    size_t w = 0;
    for (size_t r = 0; r < n; ++r)
        if (a[r] != 0)
            a[w++] = a[r];
    while (w < n)
        a[w++] = 0;
}
```

[0, 3, 0, 1, 8] → [3, 1, 8, 0, 0]. The write index never exceeds the read index during compaction, so unread data is safe.

**Complexity:** O(n) time, O(1) space; stable for nonzero values.

### How do you rotate an array by d positions? {M}
A left rotation by d can be performed using three reversals.

```text
1 2 | 3 4 5     d=2
2 1 | 3 4 5     reverse first part
2 1 | 5 4 3     reverse rest
3 4 5 1 2       reverse all
```
```c
static void rev(int *a, size_t n)
{
    for (size_t i = 0; i < n/2; ++i) {
        int t = a[i]; a[i] = a[n-1-i]; a[n-1-i] = t;
    }
}
void rotate_left(int *a, size_t n, size_t d)
{
    if (!n) return;
    d %= n;
    if (!d) return;
    rev(a,d); rev(a+d,n-d); rev(a,n);
}
```

Right rotation by d is left rotation by (n−d%n)%n for nonempty input.

**Complexity:** O(n) time, O(1) space.

### How do you find the leaders in an array? {E}
A leader is an element greater than or equal to every element to its right (some formulations require strictly greater). Scan from right to left and maintain the suffix maximum.

```c
void leaders(const int a[], size_t n)
{
    if (!n) return;
    int max = a[n-1];
    printf("%d ",max);
    for (size_t i = n-1; i > 0;) {
        --i;
        if (a[i] >= max) {
            max = a[i];
            printf("%d ",max);
        }
    }
}
```

[16, 17, 4, 3, 5, 2] has leaders 17, 5, 2. This prints them in reverse order; buffer and reverse if original order is needed.

**Complexity:** O(n) time, O(1) auxiliary space without output storage.

### How do you find the maximum difference arr[j] - arr[i] with j > i? {M}
Track the minimum value before the current position and maximize the difference against it.

```c
bool max_difference(const int32_t a[], size_t n, int64_t *out)
{
    if (n < 2) return false;
    int32_t min = a[0];
    int64_t best = (int64_t)a[1] - min;
    for (size_t j = 1; j < n; ++j) {
        int64_t diff = (int64_t)a[j] - min;
        if (diff > best) best = diff;
        if (a[j] < min) min = a[j];
    }
    *out = best;
    return true;
}
```

[7, 1, 5, 3, 6] gives 5 (6−1). A decreasing array gives a negative answer because i must precede j. Casting before subtraction avoids int32_t overflow.

**Complexity:** O(n) time, O(1) space.

### How do you find the longest subarray of alternating even and odd numbers? {M}
Maintain the length of the current alternating-parity run. If two adjacent numbers share parity, restart at length one.

```c
size_t longest_alternating(const int a[], size_t n)
{
    if (!n) return 0;
    size_t cur = 1, best = 1;
    for (size_t i = 1; i < n; ++i) {
        bool odd1 = a[i-1] % 2 != 0;
        bool odd2 = a[i] % 2 != 0;
        cur = odd1 != odd2 ? cur + 1 : 1;
        if (cur > best) best = cur;
    }
    return best;
}
```

[2, 3, 4, 7, 8, 10] → 5. Checking nonzero remainder handles negative odd values correctly.

**Complexity:** O(n) time, O(1) space.

### How do you count the frequency of each element in a sorted array? {E}
For sorted input, each distinct value occupies a contiguous run. Count its length and move to the next run.

```c
void frequencies(const int a[], size_t n)
{
    size_t i = 0;
    while (i < n) {
        size_t j = i + 1;
        while (j < n && a[j] == a[i]) ++j;
        printf("%d: %zu\n", a[i], j-i);
        i = j;
    }
}
```

[1, 1, 3, 3, 3, 8] gives 1:2, 3:3, 8:1. Every element participates in at most a constant number of comparisons.

**Complexity:** O(n) time, O(1) auxiliary space. For unsorted input use sorting or a hash table.

### How do you calculate the maximum profit from buying and selling a stock? {M}
For at most one buy and one later sell, track the lowest price seen and the best nonnegative profit.

```c
int64_t max_profit(const int32_t p[], size_t n)
{
    if (!n) return 0;
    int32_t min = p[0];
    int64_t best = 0;
    for (size_t i = 1; i < n; ++i) {
        int64_t profit = (int64_t)p[i] - min;
        if (profit > best) best = profit;
        if (p[i] < min) min = p[i];
    }
    return best;
}
```

[7, 1, 5, 3, 6, 4] → 5. A declining market returns 0 (no trade). This is different from allowing multiple transactions.

**Complexity:** O(n) time, O(1) space.

### How do you solve the trapping rain water problem? {H}
Water above index i equals min(max height to left, max height to right) − height[i]. Two pointers avoid allocating prefix and suffix arrays.

```c
uint64_t trapped(const uint32_t h[], size_t n)
{
    if (n < 3) return 0;
    size_t l = 0, r = n-1;
    uint32_t lm = 0, rm = 0;
    uint64_t total = 0;
    while (l < r) {
        if (h[l] <= h[r]) {
            if (h[l] > lm) lm = h[l];
            total += lm - h[l++];
        } else {
            if (h[r] > rm) rm = h[r];
            total += rm - h[r--];
        }
    }
    return total;
}
```

[3, 0, 2, 0, 4] traps 7 units. Process the lower endpoint because a sufficient boundary exists on the other side. Assume total fits uint64_t.

**Complexity:** O(n) time, O(1) space.

### How do you find the maximum number of consecutive 1s in a binary array? {E}
Track the current run of ones and the longest run seen.

```c
size_t max_ones(const int a[], size_t n)
{
    size_t cur = 0, best = 0;
    for (size_t i = 0; i < n; ++i) {
        cur = a[i] == 1 ? cur + 1 : 0;
        if (cur > best) best = cur;
    }
    return best;
}
```

[1, 1, 0, 1, 1, 1, 0] → 3. Empty or all-zero input returns 0.

**Complexity:** O(n) time, O(1) space. Allowing flips of up to k zeros requires a variable-size sliding window.

### How do you find the maximum sum of k consecutive elements (sliding window)? {M}
Instead of recalculating each k-element sum, subtract the outgoing element and add the incoming element.

```c
bool max_window(const int32_t a[], size_t n, size_t k,
                int64_t *out)
{
    if (!k || k > n) return false;
    int64_t sum = 0;
    for (size_t i = 0; i < k; ++i) sum += a[i];
    int64_t best = sum;
    for (size_t i = k; i < n; ++i) {
        sum += (int64_t)a[i] - a[i-k];
        if (sum > best) best = sum;
    }
    *out = best;
    return true;
}
```

For [2, 1, 5, 1, 3, 2], k=3, sums are 8, 7, 9, 6; answer 9. Assume intermediate sums fit int64_t. Initialize best from the first window, not zero, for negative input.

**Complexity:** O(n) time, O(1) space.

### How do you check if a string is a palindrome? {E}
A palindrome reads the same forward and backward. Compare mirrored characters.

```c
bool palindrome(const char *s)
{
    size_t n = strlen(s);
    for (size_t i = 0; i < n/2; ++i)
        if (s[i] != s[n-1-i]) return false;
    return true;
}
```

"level" is a palindrome, "hello" is not. This is a bytewise, case-sensitive comparison of a valid NUL-terminated string. If punctuation or case must be ignored, define those rules first.

**Complexity:** O(n) time, O(1) space.

### How do you check whether one string is a subsequence of another? {E}
A subsequence preserves order but need not be contiguous. Advance a pointer through the candidate only when a matching character is found in the source.

```c
bool subsequence(const char *small, const char *large)
{
    while (*small && *large) {
        if (*small == *large) ++small;
        ++large;
    }
    return *small == '\0';
}
```
"ace" is a subsequence of "abcde"; "aec" is not. An empty string is a subsequence of every string.

**Complexity:** O(n) time for source length n, O(1) space.

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

### How do you solve Two Sum (find two numbers that add up to a target)? {E}
**Short answer:** For an unsorted array, the brute-force check of every pair is O(n²). If the array is **sorted** (or you can sort a copy with indices), use two pointers from both ends: if the sum is too small move the left pointer up, if too large move the right pointer down, O(n). With a hash table of values already seen, it is O(n) on unsorted input.

```c
#include <stdbool.h>
#include <stddef.h>

/* sorted input: two pointers, O(n) time, O(1) space */
bool two_sum_sorted(const int *a, size_t n, int target, size_t *i_out, size_t *j_out)
{
    if (n < 2) return false;
    size_t i = 0, j = n - 1;
    while (i < j) {
        long sum = (long)a[i] + a[j];          /* avoid int overflow */
        if (sum == target) { *i_out = i; *j_out = j; return true; }
        if (sum < target) i++;
        else              j--;
    }
    return false;
}
/* {1, 3, 4, 6, 9}, target 10 -> indices 0 and 4 (1 + 9) */
```

**Why moving the pointers is safe:** if `a[i] + a[j]` is too small, `a[i]` cannot pair with any element left of `j` either (they are all ≤ `a[j]`), so `i` can be discarded. The symmetric argument discards `j` when the sum is too big.

**Unsorted input options**

| Method | Time | Extra memory | Embedded suitability |
|---|---|---|---|
| Nested loops | O(n²) | O(1) | fine for n < ~100 |
| Sort a copy of (value, index) pairs + two pointers | O(n log n) | O(n) | good, deterministic |
| Hash set of seen values | O(n) average | O(n) | needs a hash table; avoid dynamic allocation on MCUs |
| Lookup table (small value range, e.g. 0..255) | O(n) | O(range) | excellent when values are small |

**Watch for:** using the same element twice (target 8 with a single 4), duplicate values, and overflow when adding two large `int`s.

**Follow-ups:** count all pairs, closest sum to the target (track the minimum |sum − target| while moving the pointers), and 3Sum (fix one element, run two pointers on the rest: O(n²)).

### How do you find the longest common prefix of a set of strings? {E}
**Short answer:** Compare the strings column by column: take character `i` of the first string and check that every other string has the same character at `i`. Stop at the first mismatch or at the end of any string; the prefix is the first `i` characters. O(total characters) time, O(1) extra space.

```c
#include <stddef.h>

/* returns the length of the common prefix; strs[0..n-1] are C strings, n >= 1 */
size_t common_prefix_len(const char *const *strs, size_t n)
{
    size_t i = 0;
    for (;; i++) {
        char c = strs[0][i];
        if (c == '\0') return i;
        for (size_t k = 1; k < n; k++)
            if (strs[k][i] != c)          /* also stops at a shorter string's '\0' */
                return i;
    }
}
/* {"flower", "flow", "flight"} -> 2 ("fl") */
```

**Why the `'\0'` check works for shorter strings:** if another string ends at position `i`, its character there is `'\0'`, which differs from `c` (non-zero), so the loop stops without reading past its end.

**Alternatives:** horizontal scanning (prefix of the first two, then shrink against each next string), sorting and comparing only the first and last strings (they differ the most), or divide and conquer. All are O(total characters); the vertical scan stops earliest.

**Embedded relevance:** matching command prefixes in a CLI parser (e.g. accept "sta" for "status" if unique), or grouping file paths/topics by common prefix in an MQTT broker.

### How do you check if brackets in a string are balanced (Valid Parentheses)? {E}
**Short answer:** Use a stack. Push every opening bracket; on a closing bracket, the stack must be non-empty and its top must be the matching opener, which you pop. At the end, the stack must be empty. O(n) time, O(n) space (bounded by the string length).

```c
#include <stdbool.h>
#include <string.h>

bool valid_brackets(const char *s)
{
    size_t len = strlen(s);
    char stack[256];                       /* fixed size: reject inputs that would overflow */
    size_t top = 0;
    for (size_t i = 0; i < len; i++) {
        char c = s[i];
        if (c == '(' || c == '[' || c == '{') {
            if (top == sizeof stack) return false;      /* too deep */
            stack[top++] = c;
        } else if (c == ')' || c == ']' || c == '}') {
            char want = (c == ')') ? '(' : (c == ']') ? '[' : '{';
            if (top == 0 || stack[top - 1] != want) return false;
            top--;
        }
    }
    return top == 0;
}
/* "{[()]}" -> true, "([)]" -> false, "((" -> false */
```

**Three ways to fail:** a closer with an empty stack (`")("`), a closer that does not match the top (`"([)]"`), and openers left over at the end (`"(("`).

**Only one bracket type?** You do not need a stack, just a counter: increment on `(`, decrement on `)`, fail if it ever goes negative, and require 0 at the end.

**Embedded notes:** use a fixed-size array as the stack and handle overflow explicitly instead of recursing or allocating. The same pattern validates nesting in a JSON or configuration parser on a device with no heap.

**Follow-ups:** minimum number of insertions to balance (count unmatched openers and closers), and the longest valid parentheses substring (stack of indices).

### How do you merge two sorted arrays? {E}
**Short answer:** Walk both arrays with one index each and copy the smaller current element to the output, then copy whatever remains. O(n + m). To merge **in place** when the first array has room at its end (LeetCode "Merge Sorted Array"), fill from the **back** so nothing is overwritten before it is read.

```c
#include <stddef.h>

/* a has capacity n + m: first n elements valid, b has m elements; result sorted in a */
void merge_into(int *a, size_t n, const int *b, size_t m)
{
    size_t i = n, j = m, k = n + m;       /* one past the last of each */
    while (j > 0) {
        if (i > 0 && a[i - 1] > b[j - 1])
            a[--k] = a[--i];
        else
            a[--k] = b[--j];
    }
    /* remaining a[0..i-1] are already in place */
}
/* a = {1, 2, 3, _, _, _}, b = {2, 5, 6} -> {1, 2, 2, 3, 5, 6} */
```

**Why from the back:** the free space is at the end of `a`. Writing the largest elements first into that space never overwrites an element of `a` that has not been read yet. Merging from the front would require shifting or a temporary buffer.

**Stability:** when equal, taking from `b` here places `b`'s element after `a`'s in the final array, keeping `a`'s first. Use `>=` vs `>` deliberately if stability matters.

**Loop with unsigned indices:** counting down with `size_t` uses the `i > 0` / `--i` pattern to avoid wrapping below zero.

**This is the merge step of merge sort**, which is O(n log n) worst case and stable, a good choice when you need predictable time (unlike quicksort's O(n²) worst case), at the cost of O(n) extra memory for arrays. Merging two sorted linked lists needs no extra memory.

### How do you find the majority element (appearing more than n/2 times)? {M}
**Short answer:** Use the **Boyer–Moore voting algorithm**: keep a candidate and a counter. For each element, if the counter is 0, take it as the new candidate; then increment the counter if the element equals the candidate, otherwise decrement it. If a majority exists, it is the final candidate. O(n) time, O(1) space. If a majority is not guaranteed, verify with a second pass.

```c
#include <stdbool.h>
#include <stddef.h>

bool majority(const int *a, size_t n, int *out)
{
    int cand = 0;
    size_t count = 0;
    for (size_t i = 0; i < n; i++) {
        if (count == 0) cand = a[i];
        count += (a[i] == cand) ? 1 : (size_t)-1;   /* +1 or -1 */
    }
    size_t c = 0;                                    /* verification pass */
    for (size_t i = 0; i < n; i++) c += (a[i] == cand);
    if (c > n / 2) { *out = cand; return true; }
    return false;
}
/* {2, 2, 1, 1, 1, 2, 2} -> 2 */
```

**Why it works:** each decrement pairs one occurrence of the candidate with one different element and "cancels" both. A majority element has more occurrences than all other elements combined, so it cannot be fully cancelled and survives as the candidate.

**Dry run {2, 2, 1, 1, 1, 2, 2}:** cand 2 (1), 2 (2), 1 → 1, 1 → 0, 1 becomes cand (1), 2 → 0, 2 becomes cand (1). Final candidate 2; verification count 4 > 3.

**Alternatives:** sort and take the middle element (O(n log n)); hash counts (O(n) memory); bit-by-bit majority (for each of 32 bit positions, count ones; the majority element has the majority bit in every position).

**Embedded use:** **majority voting** of redundant sensor readings or triple modular redundancy (TMR) uses the same idea for 3 values: `(a & b) | (a & c) | (b & c)` gives the bitwise majority of three words, which corrects a single corrupted copy.

**Follow-up:** elements appearing more than n/3 times (at most two): Boyer–Moore with two candidates and two counters.

### How do you search for a value in a rotated sorted array? {M}
**Short answer:** A sorted array rotated at an unknown point (e.g. `{4, 5, 6, 7, 0, 1, 2}`) can still be searched in O(log n). At each binary-search step, at least one half is properly sorted. Check whether the target lies inside that sorted half's range; if so, search it, otherwise search the other half.

```c
#include <stddef.h>

long search_rotated(const int *a, size_t n, int target)   /* distinct values */
{
    size_t lo = 0, hi = n;                     /* [lo, hi) */
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return (long)mid;
        if (a[lo] <= a[mid]) {                 /* left half [lo, mid] is sorted */
            if (a[lo] <= target && target < a[mid]) hi = mid;
            else                                     lo = mid + 1;
        } else {                               /* right half [mid, hi-1] is sorted */
            if (a[mid] < target && target <= a[hi - 1]) lo = mid + 1;
            else                                          hi = mid;
        }
    }
    return -1;
}
/* {4, 5, 6, 7, 0, 1, 2}, target 0 -> 4 */
```

**Dry run (target 0):** lo 0, hi 7, mid 3 (7). Left half 4..7 sorted, 0 not in [4, 7) → lo 4. mid 5 (1). `a[4]=0 <= a[5]=1`: left half sorted, 0 in [0, 1) → hi 5. mid 4 (0) → found at 4.

**Duplicates** (e.g. `{1, 1, 1, 3, 1}`) break the "which half is sorted" test when `a[lo] == a[mid] == a[hi-1]`; then you can only shrink by one (`lo++`), and the worst case becomes O(n).

**Related:** find the rotation point (the minimum) with binary search comparing `a[mid]` with `a[hi-1]`.

**Embedded relevance:** a circular log or ring buffer of timestamped records written in order and wrapped around is exactly a rotated sorted array; this search finds a record by timestamp without unrolling the buffer.

### How do you add two binary strings or add one to a number stored as digits? {E}
**Short answer:** Work from the least significant end (the right) with a carry, exactly like addition on paper: sum the two digits plus the carry, write `sum % base`, carry `sum / base`. If a carry is left at the end, the result is one digit longer.

```c
#include <string.h>

/* out must have room for max(len a, len b) + 2 bytes */
void add_binary(const char *a, const char *b, char *out)
{
    size_t i = strlen(a), j = strlen(b);
    size_t k = (i > j ? i : j) + 1;           /* room for a final carry */
    out[k] = '\0';
    int carry = 0;
    while (k > 0) {
        int sum = carry;
        if (i > 0) sum += a[--i] - '0';
        if (j > 0) sum += b[--j] - '0';
        out[--k] = (char)('0' + (sum & 1));
        carry = sum >> 1;
    }
    if (out[0] == '0' && out[1] != '\0')      /* drop the unused leading digit */
        memmove(out, out + 1, strlen(out));
}
/* "1011" + "11" -> "1110" */

/* digits[0] is the most significant decimal digit; returns new length */
size_t plus_one(unsigned char *digits, size_t n)   /* capacity n + 1 */
{
    for (size_t i = n; i-- > 0; ) {
        if (digits[i] < 9) { digits[i]++; return n; }
        digits[i] = 0;                         /* 9 + 1 = 10: write 0, carry on */
    }
    memmove(digits + 1, digits, n);            /* all nines: 999 -> 1000 */
    digits[0] = 1;
    return n + 1;
}
```

**Why this matters in embedded work:** arbitrary-precision arithmetic, BCD counters (RTC chips store time in BCD; adding to a BCD value needs a decimal carry at 10, not 16), and multi-word counters (a 64-bit counter built from two 32-bit hardware registers, where the carry must be handled when the low word wraps).

**Check your carry logic on:** "1" + "1" = "10", "0" + "0" = "0", {9, 9} + 1 = {1, 0, 0}.

### How do you implement atoi() and itoa() in C? {M}
**Short answer:** **atoi:** skip leading spaces, read an optional sign, then for each digit compute `value = value * 10 + (c - '0')`, checking for overflow **before** multiplying; stop at the first non-digit. **itoa:** repeatedly take `value % base` as the next digit (from the least significant end) and divide by the base, then reverse the digits; handle zero and negative numbers (including `INT_MIN`) carefully.

```c
#include <ctype.h>
#include <limits.h>
#include <stdbool.h>

/* returns false on overflow or if there are no digits */
bool my_atoi(const char *s, int *out)
{
    while (isspace((unsigned char)*s)) s++;
    bool neg = false;
    if (*s == '+' || *s == '-') neg = (*s++ == '-');
    if (!isdigit((unsigned char)*s)) return false;

    unsigned limit = neg ? (unsigned)INT_MAX + 1u : (unsigned)INT_MAX;
    unsigned v = 0;
    while (isdigit((unsigned char)*s)) {
        unsigned d = (unsigned)(*s++ - '0');
        if (v > (limit - d) / 10u) return false;     /* v * 10 + d would exceed limit */
        v = v * 10u + d;
    }
    *out = neg ? (int)(0u - v) : (int)v;             /* well-defined for INT_MIN on two's complement */
    return true;
}

/* buf needs at least 34 bytes for base 2; base 2..16 */
char *my_itoa(int value, char *buf, unsigned base)
{
    static const char digits[] = "0123456789abcdef";
    unsigned u = (value < 0 && base == 10) ? 0u - (unsigned)value : (unsigned)value;
    char *p = buf;
    do {                                   /* do-while: value 0 still prints "0" */
        *p++ = digits[u % base];
        u /= base;
    } while (u);
    if (value < 0 && base == 10) *p++ = '-';
    *p = '\0';
    for (char *l = buf, *r = p - 1; l < r; l++, r--) {   /* reverse in place */
        char t = *l; *l = *r; *r = t;
    }
    return buf;
}
/* my_atoi("  -42abc") -> -42, my_itoa(-2147483648, buf, 10) -> "-2147483648" */
```

**Edge cases interviewers test:** leading spaces, `"+"` or `"-"` alone, `"42abc"` (stop at the first non-digit), overflow (`"99999999999"`), `INT_MIN` (its absolute value does not fit in `int`, which is why the conversion uses `unsigned`), and `0`.

**Why not the standard functions?** `atoi()` has no error reporting (overflow is undefined behaviour); use `strtol()` and check `errno` and the end pointer. `itoa()` is not standard C at all; use `snprintf()`. On small MCUs, `printf`-family code can cost several KB of flash, which is why hand-written conversion routines are common.

**Embedded follow-up:** converting a 32-bit value to decimal on a Cortex-M0 (no divide instruction) — the repeated `/ 10` becomes a library call. A multiply-by-reciprocal trick (`(x * 0xCCCCCCCDull) >> 35` for division by 10) is what compilers generate on cores with a fast multiplier.

### How do you implement read(n) using a read4() API that returns 4 bytes at a time? {M}
**Short answer:** Call `read4()` into a small 4-byte temporary buffer and copy into the caller's buffer until you have `n` bytes or `read4()` returns fewer than 4 (end of file). If the function is called several times, keep the **leftover** bytes from the last `read4()` between calls, so data is not lost when the last chunk was larger than needed.

```c
#include <string.h>

int read4(char *buf4);          /* provided: reads up to 4 bytes, returns count (0 at EOF) */

static char  cache[4];          /* leftovers between calls */
static int   cache_pos, cache_len;

int read_n(char *buf, int n)
{
    int total = 0;
    while (total < n) {
        if (cache_pos == cache_len) {          /* cache empty: refill */
            cache_len = read4(cache);
            cache_pos = 0;
            if (cache_len == 0) break;         /* end of data */
        }
        int take = cache_len - cache_pos;
        if (take > n - total) take = n - total;
        memcpy(buf + total, cache + cache_pos, (size_t)take);
        cache_pos += take;
        total += take;
    }
    return total;
}
```

**The bug in the one-call version:** without the cache, a call `read(3)` consumes 4 bytes from `read4()` and throws one away, so the next `read()` misses a byte.

**Why embedded interviewers like this question:** it is exactly how drivers sit on top of hardware that delivers fixed-size chunks: a flash device with 4- or 16-byte read granularity, a UART FIFO, a USB endpoint with 64-byte packets, or an SPI sensor with a fixed frame. The caller wants arbitrary lengths; the driver keeps a staging buffer.

**Discuss:** making the static state per-instance (a struct passed in) so it is reentrant and supports several files, thread safety (a mutex if shared), and reading directly into the caller's buffer when 4 or more bytes remain, avoiding the extra copy.

### How do you find the product of an array except self without division? {M}
**Short answer:** Compute the product of elements to the left and right of each index. Multiply these products; division is unnecessary, including when the input contains zeros.

```c
#include <stddef.h>
/* n elements; out must not overlap a. All products must fit long long. */
void product_except(const int *a, long long *out, size_t n)
{
    long long p = 1;
    for (size_t i = 0; i < n; ++i) {
        out[i] = p;
        p *= a[i];
    }
    p = 1;
    for (size_t i = n; i > 0; --i) {
        out[i-1] *= p;
        p *= a[i-1];
    }
}
```

| Input | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|
| Prefix | 1 | 1 | 2 | 6 |
| Suffix | 24 | 12 | 4 | 1 |
| Result | 24 | 12 | 8 | 6 |

**Complexity:** O(n) time and O(1) auxiliary space excluding output. An empty array produces no output; one element produces 1. Handle arithmetic overflow in production.

**Interview takeaway:** Two directional passes replace division and handle zeros naturally.
