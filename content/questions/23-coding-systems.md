---
slug: coding-systems
title: "Coding: Systems, Bitmaps & Virtualization"
icon: 🧭
level: Advanced
order: 23
desc: Bitmap allocators, find-first-zero, count leading zeros, single number II, page-table walk simulation, guest memory lookup, an MMIO device model, a virtqueue parser, dirty-page tracking, graph cycle detection and topological sort for device init order.
---
These questions come from kernel, hypervisor, BSP and silicon-validation interviews (for example GPU, SoC and automotive hypervisor teams). They test whether you can turn OS and hardware concepts into small, correct C programs. Each answer is compact, tested C plus the points to explain.

### Count leading zeros of a 32-bit number. {E}
```c
#include <stdint.h>

unsigned clz32(uint32_t x)
{
    if (x == 0) return 32;
    unsigned n = 0;
    if (!(x & 0xFFFF0000u)) { n += 16; x <<= 16; }    /* binary search on the top bits */
    if (!(x & 0xFF000000u)) { n += 8;  x <<= 8;  }
    if (!(x & 0xF0000000u)) { n += 4;  x <<= 4;  }
    if (!(x & 0xC0000000u)) { n += 2;  x <<= 2;  }
    if (!(x & 0x80000000u)) { n += 1; }
    return n;
}
/* clz32(1) = 31, clz32(0x00F00000) = 8 */
```

**Points:** five steps instead of 32; in production use `__builtin_clz(x)` (undefined for 0) which is one `CLZ` instruction on Armv5+ / Cortex-M3+. Uses: `31 - clz` = index of the highest set bit (floor log2), normalising fixed-point values, finding the highest-priority ready task in a bitmap scheduler.

### Find the element that appears once when all others appear three times. {M}
```c
#include <stddef.h>
#include <stdint.h>

int32_t single_number_thrice(const int32_t *a, size_t n)
{
    uint32_t ones = 0, twos = 0;            /* bits seen 1 time and 2 times (mod 3) */
    for (size_t i = 0; i < n; i++) {
        uint32_t x = (uint32_t)a[i];
        ones = (ones ^ x) & ~twos;
        twos = (twos ^ x) & ~ones;
    }
    return (int32_t)ones;
}
/* {2, 2, 3, 2} -> 3,  {0, 1, 0, 1, 0, 1, 99} -> 99 */
```

**Points:** each bit position counts occurrences modulo 3 using two bitmasks as a 2-bit counter; after the loop, bits of numbers that appeared three times have cancelled. O(n), O(1). A simpler version to explain first: for each of the 32 bit positions, count how many numbers have that bit set and keep it if `count % 3 != 0`.

### Implement a bitmap allocator with find-first-zero. {M}
```c
#include <stdint.h>

#define NBLOCKS 256u
static uint32_t bitmap[NBLOCKS / 32];                 /* 1 = used, 0 = free */

int find_first_zero(void)
{
    for (unsigned w = 0; w < NBLOCKS / 32; w++) {
        if (bitmap[w] != 0xFFFFFFFFu) {               /* skip full words quickly */
            unsigned bit = (unsigned)__builtin_ctz(~bitmap[w]);   /* lowest 0 bit */
            return (int)(w * 32u + bit);
        }
    }
    return -1;                                        /* all used */
}

int bm_alloc(void)
{
    int i = find_first_zero();
    if (i >= 0) bitmap[i / 32] |= 1u << (i % 32);
    return i;
}

void bm_free(int i)
{
    bitmap[i / 32] &= ~(1u << (i % 32));
}

/* allocate n contiguous blocks (simple scan) */
int bm_alloc_range(unsigned n)
{
    unsigned run = 0;
    for (unsigned i = 0; i < NBLOCKS; i++) {
        if (bitmap[i / 32] & (1u << (i % 32))) { run = 0; continue; }
        if (++run == n) {
            unsigned start = i + 1 - n;
            for (unsigned j = start; j <= i; j++) bitmap[j / 32] |= 1u << (j % 32);
            return (int)start;
        }
    }
    return -1;
}
```

**Points:** one bit per block makes the metadata tiny (256 blocks → 32 bytes); scan word by word and use `ctz(~word)` to find the first free bit in O(1) per word; add a "next search position" hint to avoid rescanning full words; protect with a lock in concurrent code (or use atomic bit operations). Used for flash sector maps, file-system block allocation, PID and IRQ number allocation (Linux `ida`/`bitmap_find_next_zero_area`), and page-frame allocation in simple kernels.

### Simulate a two-level page-table walk. {H}
```c
#include <stdint.h>
#include <stdbool.h>

/* 32-bit VA: [31:22] L1 index, [21:12] L2 index, [11:0] page offset; 4-byte entries */
#define PTE_VALID (1u << 0)
#define PTE_WRITE (1u << 1)
#define PTE_USER  (1u << 2)
#define PTE_ADDR(e) ((e) & 0xFFFFF000u)

typedef enum { XLATE_OK, FAULT_L1, FAULT_L2, FAULT_PERM } xlate_t;

/* phys_read32 simulates reading physical memory where the tables live */
uint32_t phys_read32(uint32_t pa);

xlate_t translate(uint32_t l1_base, uint32_t va, bool write, bool user, uint32_t *pa)
{
    uint32_t l1e = phys_read32(l1_base + ((va >> 22) & 0x3FFu) * 4u);
    if (!(l1e & PTE_VALID)) return FAULT_L1;

    uint32_t l2e = phys_read32(PTE_ADDR(l1e) + ((va >> 12) & 0x3FFu) * 4u);
    if (!(l2e & PTE_VALID)) return FAULT_L2;

    if ((write && !(l2e & PTE_WRITE)) || (user && !(l2e & PTE_USER))) return FAULT_PERM;

    *pa = PTE_ADDR(l2e) | (va & 0xFFFu);              /* frame + offset */
    return XLATE_OK;
}
```

**Points:** split the VA into indexes and offset; each level's entry gives the physical address of the next table; check valid and permission bits and return a precise fault type (the OS needs it to decide between demand paging, copy-on-write and SIGSEGV); combine the final frame with the unchanged offset. Follow-ups: add a small TLB cache in front (array indexed by VPN with tags), large pages (an L1 entry that maps 4 MB directly), accessed/dirty bit updates, and the 4-level 9-9-9-9-12 split of ARM64.

### Look up which guest memory region contains a guest physical address. {M}
```c
#include <stdint.h>
#include <stddef.h>

typedef struct {
    uint64_t gpa_start;      /* guest physical start */
    uint64_t size;
    uint8_t *hva;            /* host virtual address where it is mapped */
} mem_region_t;

/* regions sorted by gpa_start and non-overlapping */
uint8_t *gpa_to_hva(const mem_region_t *r, size_t n, uint64_t gpa, uint64_t len)
{
    size_t lo = 0, hi = n;
    while (lo < hi) {                                 /* binary search for the last start <= gpa */
        size_t mid = lo + (hi - lo) / 2;
        if (r[mid].gpa_start <= gpa) lo = mid + 1; else hi = mid;
    }
    if (lo == 0) return NULL;
    const mem_region_t *m = &r[lo - 1];
    uint64_t off = gpa - m->gpa_start;
    if (off >= m->size || len > m->size - off) return NULL;   /* outside, or crosses the end */
    return m->hva + off;
}
```

**Points:** this is what a VMM (QEMU, Firecracker, KVM's memslots) does to turn a guest physical address from a device or exit into a host pointer. Keep regions sorted for O(log n) lookup (KVM caches the last-used slot too); check that the whole access fits inside one region (an access crossing two regions must be split); return NULL for MMIO holes so the caller emulates a device instead. Never trust guest-supplied addresses and lengths: overflow-safe checks (`len > size - off`) matter here because the guest is untrusted.

### Write a simple MMIO device model (register read/write callbacks). {H}
```c
#include <stdint.h>
#include <stdbool.h>

/* a timer device: CTRL @0x00 (bit0 enable, bit1 irq_en), COUNT @0x04 (ro), LOAD @0x08, STATUS @0x0C (w1c) */
typedef struct {
    uint32_t ctrl, count, load, status;
    void (*set_irq)(int level);
} timer_dev_t;

static void update_irq(timer_dev_t *d)
{
    d->set_irq((d->ctrl & 2u) && (d->status & 1u));
}

uint32_t timer_mmio_read(timer_dev_t *d, uint64_t off)
{
    switch (off) {
    case 0x00: return d->ctrl;
    case 0x04: return d->count;
    case 0x08: return d->load;
    case 0x0C: return d->status;
    default:   return 0;                               /* log "guest error: bad offset" */
    }
}

void timer_mmio_write(timer_dev_t *d, uint64_t off, uint32_t val)
{
    switch (off) {
    case 0x00: d->ctrl = val & 3u; if (val & 1u) d->count = d->load; break;
    case 0x08: d->load = val; break;
    case 0x0C: d->status &= ~val; break;              /* write-1-to-clear */
    default:   break;                                  /* COUNT is read-only: ignore writes */
    }
    update_irq(d);
}

void timer_tick(timer_dev_t *d)                        /* called by the emulator's clock */
{
    if (!(d->ctrl & 1u)) return;
    if (d->count && --d->count == 0) {
        d->status |= 1u;                               /* expired */
        d->count = d->load;                            /* auto-reload */
        update_irq(d);
    }
}
```

**Points:** a device model is a state struct plus read/write handlers keyed by register offset, exactly like QEMU's `MemoryRegionOps`; implement access semantics faithfully (read-only, write-1-to-clear, side effects on write); recompute the interrupt line after every state change; ignore or log invalid offsets and sizes instead of crashing (the guest can be malicious); a reset function should restore documented reset values. In QEMU you would also add migration state (`VMStateDescription`).

### Parse a virtqueue descriptor chain. {H}
```c
#include <stdint.h>
#include <stddef.h>

#define VRING_DESC_F_NEXT  1
#define VRING_DESC_F_WRITE 2       /* device writes into this buffer */

struct vring_desc { uint64_t addr; uint32_t len; uint16_t flags; uint16_t next; };

typedef struct { uint8_t *ptr; uint32_t len; int device_writable; } iov_t;

uint8_t *gpa_to_hva_simple(uint64_t gpa, uint32_t len);   /* NULL if invalid */

/* walk the chain starting at `head`; returns number of buffers, or -1 if malformed */
int parse_chain(const struct vring_desc *desc, uint16_t qsize, uint16_t head,
                iov_t *iov, int max_iov)
{
    int n = 0;
    uint16_t i = head;
    for (int hops = 0; ; hops++) {
        if (i >= qsize || hops >= qsize || n >= max_iov) return -1;   /* bad index, loop, too long */
        const struct vring_desc *d = &desc[i];                        /* copy fields once in real code */
        uint8_t *p = gpa_to_hva_simple(d->addr, d->len);
        if (!p) return -1;                                            /* buffer outside guest RAM */
        iov[n].ptr = p;
        iov[n].len = d->len;
        iov[n].device_writable = (d->flags & VRING_DESC_F_WRITE) != 0;
        n++;
        if (!(d->flags & VRING_DESC_F_NEXT)) break;
        i = d->next;
    }
    return n;
}
```

**Points:** a request (e.g. a virtio-blk read) is a chain of descriptors linked by `next`: device-readable buffers (header, data to write) followed by device-writable ones (data to read, status byte). The device takes chain heads from the **available** ring, processes them, and puts `(head, bytes written)` into the **used** ring, then notifies the guest. Security checks are the core of the question: index range, loop detection (a chain can be at most `qsize` long), address translation with length checks, and reading each descriptor once (the guest can change shared memory while you read it: "double fetch" bugs). Indirect descriptors and the packed ring layout are follow-ups.

### Track dirty pages with a bitmap (for live migration). {M}
```c
#include <stdint.h>
#include <string.h>

#define PAGE_SHIFT 12
#define GUEST_PAGES 4096u                          /* 16 MB guest */
static uint64_t dirty[GUEST_PAGES / 64];

static inline void mark_dirty(uint64_t gpa)
{
    uint64_t pfn = gpa >> PAGE_SHIFT;
    if (pfn < GUEST_PAGES) dirty[pfn / 64] |= 1ull << (pfn % 64);   /* atomic OR if called concurrently */
}

/* migration loop: send every dirty page once, then clear the bitmap for the next round */
unsigned sync_dirty(void (*send_page)(uint64_t pfn))
{
    unsigned sent = 0;
    for (unsigned w = 0; w < GUEST_PAGES / 64; w++) {
        uint64_t bits = dirty[w];
        dirty[w] = 0;                                /* real code: atomic exchange */
        while (bits) {
            unsigned b = (unsigned)__builtin_ctzll(bits);
            send_page((uint64_t)w * 64 + b);
            bits &= bits - 1;                        /* clear lowest set bit */
            sent++;
        }
    }
    return sent;
}
```

**Points:** one bit per guest page; pages are marked dirty when the guest writes them (KVM write-protects pages in stage-2 or uses hardware dirty tracking/PML, and reports a bitmap with `KVM_GET_DIRTY_LOG`; device emulation marks pages it DMAs into); migration repeatedly sends dirty pages while the guest runs, until the remaining set is small, then pauses the guest for the final copy. Read-and-clear must be atomic per word, or writes between the read and the clear are lost. Iterating set bits with `ctz` and `bits &= bits - 1` skips clean pages quickly.

### Detect a cycle in a directed graph. {M}
```c
#include <stdbool.h>

#define MAXN 16
static int adj[MAXN][MAXN], deg[MAXN];       /* adjacency lists */
static int color[MAXN];                      /* 0 = white (unvisited), 1 = grey (on stack), 2 = black (done) */

static bool dfs_cycle(int u)
{
    color[u] = 1;
    for (int k = 0; k < deg[u]; k++) {
        int v = adj[u][k];
        if (color[v] == 1) return true;                 /* back edge to a node on the current path */
        if (color[v] == 0 && dfs_cycle(v)) return true;
    }
    color[u] = 2;
    return false;
}

bool has_cycle(int n)
{
    for (int i = 0; i < n; i++) color[i] = 0;
    for (int i = 0; i < n; i++)
        if (color[i] == 0 && dfs_cycle(i)) return true;
    return false;
}
```

**Points:** three-colour DFS: reaching a **grey** node (still on the recursion stack) means a back edge, i.e. a cycle; black nodes are finished and safe. O(V + E). For undirected graphs, track the parent instead. Embedded and systems uses: lock-order validation (Linux lockdep builds a graph of lock dependencies and reports cycles = potential deadlocks), detecting circular dependencies between drivers or build targets. Recursion depth equals the path length, so use an explicit stack on small MCUs.

### Order device initialisation with a topological sort. {M}
```c
#include <stdio.h>

/* edge u -> v means "u must be initialised before v" (e.g. clock -> i2c -> pmic -> display) */
#define MAXN 16
static int adj[MAXN][MAXN], deg[MAXN], indeg[MAXN];

void add_dep(int before, int after) { adj[before][deg[before]++] = after; indeg[after]++; }

/* Kahn's algorithm: returns number of devices ordered; less than n means a cycle */
int init_order(int n, int *order)
{
    int queue[MAXN], qh = 0, qt = 0, cnt = 0;
    int in[MAXN];
    for (int i = 0; i < n; i++) { in[i] = indeg[i]; if (in[i] == 0) queue[qt++] = i; }
    while (qh < qt) {
        int u = queue[qh++];
        order[cnt++] = u;
        for (int k = 0; k < deg[u]; k++)
            if (--in[adj[u][k]] == 0) queue[qt++] = adj[u][k];
    }
    return cnt;
}
```

**Points:** start with devices that depend on nothing, "initialise" them, and remove their outgoing edges; any device whose remaining dependency count reaches zero becomes ready. If fewer than `n` devices come out, there is a dependency cycle (report it). O(V + E). Real systems: the Linux driver core handles probe ordering with **deferred probing** (a driver returns `-EPROBE_DEFER` when a supplier such as a clock or regulator is not ready) and **fw_devlink**, which builds supplier/consumer links from the device tree; systemd orders units with the same idea; Zephyr uses initialisation levels and priorities.
