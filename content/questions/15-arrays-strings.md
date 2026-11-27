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
Anagrams have equal multiplicities of each character. For an 8-bit-byte system, count each possible byte.

```c
bool anagram(const char *a, const char *b)
{
    size_t count[256] = {0};
    while (*a) ++count[(unsigned char)*a++];
    while (*b) {
        unsigned char c = (unsigned char)*b++;
        if (!count[c]) return false;
        --count[c];
    }
    for (size_t i = 0; i < 256; ++i)
        if (count[i]) return false;
    return true;
}
```
"listen" and "silent" are anagrams. This is bytewise and case-sensitive; Unicode needs different handling. Cast char to unsigned char before indexing.

**Complexity:** O(n+m) time and O(256) fixed storage.

### How do you reverse a string in place? {E}
Find the NUL terminator, then swap mirrored bytes without moving the terminator.

```c
void reverse_string(char *s)
{
    size_t n = strlen(s);
    for (size_t i = 0; i < n/2; ++i) {
        char t = s[i];
        s[i] = s[n-1-i];
        s[n-1-i] = t;
    }
}
```
Use a writable array such as char s[] = "hello"; the result is "olleh". Modifying a string literal is undefined behavior.

**Complexity:** O(n) time, O(1) space. Byte reversal does not preserve UTF-8 characters.

### How do you reverse the order of words in a string? {M}
For space-separated words, reverse the entire string, then reverse each word individually.

```text
one two three
eerht owt eno
three two one
```
```c
static void rev(char *s, size_t n)
{
    for (size_t i=0; i<n/2; ++i) {
        char t=s[i]; s[i]=s[n-1-i]; s[n-1-i]=t;
    }
}
void reverse_words(char *s)
{
    rev(s, strlen(s));
    char *p=s;
    while (*p) {
        while (*p==' ') ++p;
        char *start=p;
        while (*p && *p!=' ') ++p;
        rev(start,(size_t)(p-start));
    }
}
```
This preserves space runs but reverses their positions; normalize whitespace separately if required.

**Complexity:** O(n) time, O(1) space.

### How do you search for a pattern in a string (naive and KMP)? {M}
Naive matching tries the pattern at each possible starting position, costing O(nm) worst-case time. KMP avoids rechecking characters by preprocessing the pattern's longest proper prefix that is also a suffix (LPS).

```c
/* Caller provides lps[m]; m > 0. */
void build_lps(const char *p, size_t m, size_t *lps)
{
    lps[0]=0;
    for (size_t i=1,j=0; i<m;) {
        if (p[i]==p[j]) lps[i++]=++j;
        else if (j) j=lps[j-1];
        else lps[i++]=0;
    }
}
size_t kmp(const char *s, size_t n, const char *p,
           size_t m, const size_t *lps)
{
    if (!m) return 0;
    for (size_t i=0,j=0; i<n;) {
        if (s[i]==p[j]) {
            ++i; ++j;
            if (j==m) return i-m;
        } else if (j) j=lps[j-1];
        else ++i;
    }
    return SIZE_MAX;
}
```
For "ababaca", LPS is [0,0,1,2,3,0,1]. On mismatch, KMP retains the reusable prefix rather than restarting.

**Complexity:** O(n+m) time and O(m) auxiliary space.

### How does bubble sort work, and how is it different from binary search? {E}
Bubble sort repeatedly swaps adjacent inversions until the array is sorted. Binary search instead locates a key in an already sorted array.

```c
void bubble(int a[], size_t n)
{
    for (size_t end=n; end>1; --end) {
        bool changed=false;
        for (size_t i=1; i<end; ++i) {
            if (a[i-1]>a[i]) {
                int t=a[i-1]; a[i-1]=a[i]; a[i]=t;
                changed=true;
            }
        }
        if (!changed) break;
    }
}
```
[3,1,2] → [1,3,2] → [1,2,3]. Each pass settles the largest remaining element.

| Algorithm | Purpose | Worst-case time |
|---|---|---|
| Bubble sort | Rearrange elements | O(n²) |
| Binary search | Find a key | O(log n) |

**Interview takeaway:** Bubble sort is stable with strict greater-than swaps, and takes O(1) extra space. It is usually unsuitable for large arrays.

### How do you solve Two Sum (find two numbers that add up to a target)? {E}
Two Sum asks for two distinct indices whose values sum to target. A hash table storing previously seen values and indices gives expected O(n) time and O(n) space. At index i, look up target−a[i] before inserting a[i].

For sorted input, two pointers give a simpler solution:

```c
bool two_sum_sorted(const int32_t a[], size_t n,
                    int64_t target, size_t *i, size_t *j)
{
    if (n<2) return false;
    size_t l=0,r=n-1;
    while (l<r) {
        int64_t s=(int64_t)a[l]+a[r];
        if (s==target) { *i=l; *j=r; return true; }
        if (s<target) ++l;
        else --r;
    }
    return false;
}
```
[2,7,11,15], target 9 gives indices 0 and 1. Use the hash method if original unsorted indices are required. Widen arithmetic to avoid signed overflow.

**Complexity:** Sorted method O(n) time, O(1) space.

### How do you find the longest common prefix of a set of strings? {E}
Compare each character of the first string against every other string until a mismatch or terminator.

```c
size_t common_prefix(const char *const a[], size_t n)
{
    if (!n) return 0;
    size_t k=0;
    while (a[0][k]) {
        for (size_t i=1; i<n; ++i)
            if (a[i][k]!=a[0][k]) return k;
        ++k;
    }
    return k;
}
```
["flower","flow","flight"] gives length 2 ("fl"). The function returns a length, not an allocated string. All inputs must be valid NUL-terminated strings.

**Complexity:** O(nL) worst-case for n strings with inspected prefix length L, O(1) space.

### How do you check if brackets in a string are balanced (Valid Parentheses)? {E}
Use a stack of opening brackets. For every closing bracket, the top must contain the matching opener.

```c
bool balanced(const char *s, char *stack, size_t cap)
{
    size_t n=0;
    for (; *s; ++s) {
        char c=*s;
        if (c=='(' || c=='[' || c=='{') {
            if (n==cap) return false;
            stack[n++]=c;
        } else if (c==')' || c==']' || c=='}') {
            if (!n) return false;
            char t=stack[--n];
            if ((c==')' && t!='(') ||
                (c==']' && t!='[') ||
                (c=='}' && t!='{')) return false;
        } else return false;
    }
    return n==0;
}
```
"{[()]}" succeeds; "([)]" fails. This version accepts only brackets and uses caller-provided storage; capacity exhaustion is reported as false.

**Complexity:** O(n) time, O(n) worst-case stack space.

### How do you merge two sorted arrays? {E}
Merge by comparing the current elements of two sorted arrays and copying the smaller one into the output.

```c
void merge(const int a[], size_t n, const int b[],
           size_t m, int out[])
{
    size_t i=0,j=0,k=0;
    while (i<n && j<m)
        out[k++]=a[i]<=b[j] ? a[i++] : b[j++];
    while (i<n) out[k++]=a[i++];
    while (j<m) out[k++]=b[j++];
}
```
[1,4,7] and [2,3,8] → [1,2,3,4,7,8]. Caller provides nonoverlapping output with n+m elements.

**Complexity:** O(n+m) time, O(1) auxiliary space excluding output. If the first array has spare capacity, merging from the end can avoid a separate output.

### How do you find the majority element (appearing more than n/2 times)? {M}
Boyer–Moore voting cancels pairs of different values. A strict majority survives these cancellations.

```c
bool majority(const int a[], size_t n, int *out)
{
    int candidate=0;
    size_t votes=0;
    for (size_t i=0;i<n;++i) {
        if (!votes) candidate=a[i];
        if (a[i]==candidate) ++votes;
        else --votes;
    }
    size_t count=0;
    for (size_t i=0;i<n;++i)
        if (a[i]==candidate) ++count;
    if (count<=n/2) return false;
    *out=candidate;
    return true;
}
```
[2,2,1,1,2,2,2] → 2. The second pass is required unless a majority is guaranteed.

**Complexity:** O(n) time, O(1) space.

### How do you search for a value in a rotated sorted array? {M}
A rotated sorted array with distinct elements always has at least one sorted half around its midpoint. Determine whether the key lies inside that half.

```c
size_t rotated_search(const int a[],size_t n,int key)
{
    size_t l=0,r=n;
    while (l<r) {
        size_t m=l+(r-l)/2;
        if (a[m]==key) return m;
        if (a[l]<=a[m]) {
            if (a[l]<=key && key<a[m]) r=m;
            else l=m+1;
        } else {
            if (a[m]<key && key<=a[r-1]) l=m+1;
            else r=m;
        }
    }
    return SIZE_MAX;
}
```
[4,5,6,7,0,1,2], key 0 → index 4. With duplicates, equal endpoints can obscure the sorted half; narrowing ambiguous boundaries may degrade to O(n).

**Complexity:** O(log n) time for distinct input, O(1) space.

### How do you add two binary strings or add one to a number stored as digits? {E}
Both problems use digit-wise addition from the least-significant end and propagate carry.

#### Binary addition
```c
/* out has max(strlen(a),strlen(b))+2 bytes.
   Inputs contain only 0/1; out does not overlap them. */
void add_binary(const char *a,const char *b,char *out)
{
    size_t i=strlen(a),j=strlen(b),k=0;
    unsigned carry=0;
    while (i || j || carry) {
        unsigned s=carry;
        if (i) s+=(unsigned)(a[--i]-'0');
        if (j) s+=(unsigned)(b[--j]-'0');
        out[k++]=(char)('0'+s%2);
        carry=s/2;
    }
    if (!k) out[k++]='0';
    out[k]='\0';
    for(size_t x=0;x<k/2;++x) {
        char t=out[x];out[x]=out[k-1-x];out[k-1-x]=t;
    }
}
```
1011 + 11 = 1110.

#### Add one to decimal digits
Starting at the last digit, change trailing 9s to 0 and increment the first non-9. If all digits are 9, prepend 1 (extra output capacity required). Example: [1,9,9] → [2,0,0]; [9,9] → [1,0,0].

**Complexity:** Linear time; output storage proportional to result length.

### How do you implement atoi() and itoa() in C? {M}
atoi converts decimal text to int but lacks useful error reporting. itoa is a common nonstandard extension. For robust code prefer strtol and snprintf.

```c
bool parse_int(const char *s,int *out)
{
    char *end;
    errno=0;
    long x=strtol(s,&end,10);
    if(end==s || *end || errno==ERANGE ||
       x<INT_MIN || x>INT_MAX) return false;
    *out=(int)x;
    return true;
}
bool format_int(int x,char *buf,size_t cap)
{
    int n=snprintf(buf,cap,"%d",x);
    return n>=0 && (size_t)n<cap;
}
```
Headers: stdlib.h, errno.h, limits.h, stdio.h, stdbool.h. strtol accepts leading whitespace and optional sign; this wrapper rejects trailing characters.

#### Manual implementation
Skip whitespace, parse sign, accumulate digits with value = value×10+digit, checking range before each step. For output, extract digits from an unsigned magnitude, reverse them and prepend a minus sign. Avoid directly negating INT_MIN.

**Interview takeaway:** Define overflow, invalid-input and output-capacity behavior explicitly.

### How do you implement read(n) using a read4() API that returns 4 bytes at a time? {M}
If read4 returns up to four bytes, preserve unused bytes across successive read(n) calls in reader state.

```c
struct reader {
    char cache[4];
    size_t pos, end;
};
/* read4 returns 0 at EOF, 1..4 on success.
   Initialize reader to zero; assume no I/O errors. */
size_t read_n(struct reader *r,char *dst,size_t n)
{
    size_t k=0;
    while(k<n) {
        if(r->pos==r->end) {
            r->end=read4(r->cache);
            r->pos=0;
            if(!r->end) break;
        }
        dst[k++]=r->cache[r->pos++];
    }
    return k;
}
```
For source "abcdef", read(3) returns "abc" and retains 'd'; next read(3) returns "def". Output is raw bytes, not necessarily NUL-terminated.

**Complexity:** O(n) time, O(1) persistent cache. A production API should separately report errors.

### How do you find the product of an array except self without division? {M}
Use a prefix product pass followed by a suffix product pass. The product except index i is the product of all elements before i times the product of all elements after i.

```c
/* Assume all intermediate products fit int64_t.
   Output must not overlap input. */
void product_except(const int32_t a[],size_t n,int64_t out[])
{
    int64_t p=1;
    for(size_t i=0;i<n;++i) {
        out[i]=p;
        if(i+1<n) p*=a[i];
    }
    p=1;
    for(size_t i=n;i>0;) {
        --i;
        out[i]*=p;
        if(i) p*=a[i];
    }
}
```
[1,2,3,4] → [24,12,8,6]. Zero values need no special handling: one zero gives a nonzero result only at its position, two zeros give all zeros (assuming other products are representable). A single element returns the empty product 1.

**Complexity:** O(n) time, O(1) auxiliary space excluding output.

