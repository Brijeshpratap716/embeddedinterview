---
slug: linux-system-programming
title: Linux System Programming
icon: 🐚
level: Intermediate
order: 11
desc: Signals, fork bombs and resource limits, pthread_exit, /proc /sys /dev, permissions, inodes and links, file system layouts, mmap and mprotect, the page cache, sockets, epoll and the networking stack.
---
Linux system programming questions test whether you can write and debug real programs on embedded Linux: how processes get signals, how files and permissions work, how memory mapping and the page cache behave, and how network servers handle many clients. Each answer gives the short version first, then working code or commands, and the follow-ups interviewers usually ask.

### What are signals, and how are they delivered and handled? {M}
Signals are asynchronous notifications delivered to a process or thread. They can originate from the kernel, another permitted process or the program itself.

#### Delivery
A signal becomes pending, then is delivered to an eligible thread when unblocked. The kernel applies the default action or arranges execution of an installed handler in userspace. On return, the saved context is restored.

```c
static volatile sig_atomic_t stop;
static void handler(int sig)
{
    (void)sig;
    stop = 1;
}
/* In main, check errors: */
struct sigaction sa = {0};
sa.sa_handler = handler;
sigemptyset(&sa.sa_mask);
sigaction(SIGINT, &sa, NULL);
```

Use sigaction rather than relying on historical signal() semantics. Standard signals can coalesce; real-time signals can queue. SIGKILL and SIGSTOP cannot be caught or blocked.

**Interview takeaway:** A handler is not a normal thread. Call only async-signal-safe functions there; use a flag, self-pipe or signalfd-based design to defer work.

### What happens when a program executes an illegal instruction or accesses invalid memory? {M}
Invalid instructions and invalid memory accesses typically cause synchronous CPU exceptions. The kernel examines the cause and either resolves it or delivers a signal.

```text
User instruction -> CPU exception -> kernel handler
   | valid demand-page / COW fault -> repair mapping -> retry
   + invalid access -> SIGSEGV or SIGBUS
   + illegal instruction -> SIGILL
```

For example, writing to an unmapped address may produce SIGSEGV with si_code indicating an unmapped address or protection violation. Some bus/alignment or file-backed mapping failures produce SIGBUS. An unsupported instruction may result in SIGILL.

#### Debug
```bash
gdb ./app core
# bt; info registers; x/i $pc
```
Core-dump generation depends on limits and system policy.

**Interview takeaway:** A page fault is not always a programming error; demand paging is normal. Do not attempt to blindly resume a faulting instruction from a signal handler.

### What is a fork bomb, and how do ulimit and cgroups protect against it? {M}
A fork bomb is a process-creation denial of service: uncontrolled creation of child processes can exhaust task slots, memory and CPU resources.

#### Protection
- RLIMIT_NPROC limits process/thread creation for a real user ID, with privilege-related exceptions.
- The cgroup v2 pids controller restricts the number of tasks in a workload hierarchy using pids.max.
- Service managers can set TasksMax and memory/CPU limits.

For example, a dedicated test service can have TasksMax=64 so a defective worker cannot create unlimited tasks. Monitor pids.current and pids.events. Creation beyond a task limit normally fails with EAGAIN.

**Interview takeaway:** Limit tasks at workload boundaries; user-level limits alone may be insufficient. Never test uncontrolled process creation on a shared or production system.

### How do you limit the CPU and memory used by processes on Linux? {M}
Linux uses resource limits and cgroups to restrict process or workload resource consumption.

| Mechanism | Example |
|---|---|
| RLIMIT_AS | Limit virtual address space per process |
| RLIMIT_CPU | Limit accumulated CPU time |
| cgroup v2 cpu.max | CPU bandwidth quota and period |
| cgroup v2 memory.max | Hard memory limit for a workload |
| cgroup v2 pids.max | Maximum task count |

#### Example
A service can use CPUQuota=50% and MemoryMax=256M with systemd resource controls. CPU quotas throttle usage over periods, rather than setting the CPU clock speed. A memory cgroup may reclaim memory and invoke its OOM policy if it cannot satisfy allocations.

**Interview takeaway:** RLIMIT_AS is not the same as resident memory; nice affects relative scheduling weight rather than imposing a hard CPU cap. Prefer cgroups for a complete process tree.

### When should you call pthread_exit() instead of exit()? {M}
pthread_exit() terminates only the calling thread. exit() terminates the whole process, including its other threads.

```c
void *worker(void *arg)
{
    (void)arg;
    return NULL; /* equivalent to pthread_exit(NULL) */
}
int main(void)
{
    pthread_t t;
    if (pthread_create(&t,NULL,worker,NULL)!=0)
        return 1;
    pthread_join(t,NULL);
    return 0;
}
```

Returning from main is equivalent to exit, so other threads terminate. If the initial thread calls pthread_exit(NULL), other threads may continue until they terminate. A joinable thread's resources are reclaimed with pthread_join; detached threads are reclaimed automatically.

**Interview takeaway:** Do not return pointers to a terminating thread's stack. Prefer explicit joins and orderly shutdown over leaving background threads unmanaged.

### What are /proc, /sys and /dev used for? {E}
/proc, /sys and /dev expose different interfaces to the running kernel.

| Interface | Purpose | Examples |
|---|---|---|
| /proc | Process and kernel information | /proc/self/maps, /proc/interrupts |
| /sys | Kernel device/object attributes | /sys/bus/i2c/devices, /sys/class |
| /dev | Device nodes and special files | /dev/i2c-0, /dev/ttyS0 |

```bash
cat /proc/meminfo
cat /proc/interrupts
ls /sys/bus/platform/devices
ls -l /dev
```

Device nodes identify character/block devices using major/minor numbers; open/read/write/ioctl operations dispatch through the relevant kernel subsystem or driver. Sysfs attributes are often small textual configuration/status values.

**Interview takeaway:** These are kernel interfaces, not ordinary stored configuration files. Use documented ABI attributes and do not assume every sysfs file is writable.

### How do Linux file permissions work? {E}
Traditional Unix permissions specify read, write and execute rights for owner, group and others.

```text
-rwxr-x---  owner:rwx  group:r-x  others:---
             7          5          0
```

```bash
chmod 750 app
chmod u+x script.sh
chown user:group file
```

For directories, read lists entries, write permits changes to entries (subject to other checks), and execute permits traversal. A file can be deleted based on parent directory permissions, not merely its own write bit. Sticky bit, setuid/setgid, ACLs, capabilities and security modules can alter the effective access policy.

**Interview takeaway:** umask removes permission bits from requested creation modes. Avoid chmod 777 as a debugging shortcut; grant only required access.

### What is an inode? What is the difference between a hard link and a symbolic link? {E}
An inode holds filesystem metadata such as ownership, mode, timestamps, size and references to file data. Directory entries associate names with inode numbers.

```text
name A ----+
           +--> inode 123 -> file blocks
name B ----+   (hard link)
name C --> symlink inode -> "name A"
```

```bash
ln original hardlink
ln -s original symlink
ls -li original hardlink symlink
```

Hard links refer to the same inode and normally cannot cross filesystem boundaries. A symbolic link has its own inode containing a target pathname and can become dangling. Removing one hard link does not destroy the data while another link or open reference remains.

**Interview takeaway:** A filename is not the inode. An open file can remain usable after unlink removes its name.

### How do file systems store file data: contiguous, linked (FAT), indexed and extents? {M}
File allocation methods determine how logical file offsets map to storage blocks.

| Method | Mechanism | Trade-off |
|---|---|---|
| Contiguous | Consecutive blocks | Fast access, difficult growth |
| Linked/FAT | Each block points to next via metadata | Flexible growth, random access overhead |
| Indexed | Metadata references block addresses | Efficient lookup, index overhead |
| Extents | Runs described by start and length | Compact for contiguous ranges |

For a file occupying logical blocks 0–7, an extent might map 0–3 to physical blocks 100–103 and 4–7 to 220–223. Modern filesystems often use extent trees with additional allocation and caching logic.

**Interview takeaway:** Filesystem fragmentation affects metadata and access patterns. SSDs reduce seek latency but do not eliminate allocation, write-amplification or metadata concerns.

### What is mmap, and what is mprotect used for? {M}
mmap maps a file, device or anonymous memory into a process's virtual address space. mprotect changes access permissions on mapped pages.

```c
size_t len=4096;
void *p=mmap(NULL,len,PROT_READ|PROT_WRITE,
             MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
if(p==MAP_FAILED) return -1;
memset(p,0,len);
if(mprotect(p,len,PROT_READ)<0) {
    munmap(p,len);
    return -1;
}
/* Writes are now prohibited. */
munmap(p,len);
```

MAP_SHARED permits shared visibility and file-backed updates; MAP_PRIVATE uses private copy-on-write behavior. mprotect requires a page-aligned starting address; mmap supplies an aligned address.

**Interview takeaway:** A mapping may allocate physical pages lazily. Device-driver mmap requires explicit mapping support and appropriate permissions/cache attributes. Never assume a virtual address is a physical address.

### What is the page cache, and how do you write a file safely so it survives a power loss? {M}
Linux caches file contents in RAM through the page cache. A successful buffered write can mean bytes reached RAM, not persistent storage.

#### Durable replacement pattern
1. Create a temporary file in the same directory/filesystem.
2. Write all bytes, handling partial writes and EINTR.
3. fsync the temporary file and check errors.
4. Close it and atomically rename it over the destination.
5. fsync the parent directory to persist the name change.

```text
write -> dirty page cache -> filesystem writeback -> storage
fsync -> request required data/metadata durability
```

Use fdatasync where its metadata guarantees suffice. fflush only flushes C-library buffers into the OS; close alone does not guarantee durability.

**Interview takeaway:** Atomic rename and durable rename are distinct. Actual power-loss guarantees also depend on the filesystem, device firmware and whether storage honors flushes.

### What is the sequence of socket calls for a TCP server and client? {E}
**Short answer:** **Server:** `socket()` → `bind()` (choose IP and port) → `listen()` → `accept()` (blocks until a client connects, returns a new socket for that connection) → `read()`/`write()` (or `recv`/`send`) → `close()`. **Client:** `socket()` → `connect()` (TCP three-way handshake) → `write()`/`read()` → `close()`.

```
Server                                  Client
socket()                                socket()
bind(port 8080)
listen()
accept()  ◄──── SYN / SYN-ACK / ACK ──── connect()
recv()    ◄──────── request ─────────── send()
send()    ───────── response ─────────► recv()
close()   ◄──────── FIN/ACK ──────────► close()
```

**Minimal TCP echo server**

```c
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void)
{
    int ls = socket(AF_INET, SOCK_STREAM, 0);
    int on = 1;
    setsockopt(ls, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);

    struct sockaddr_in a = { .sin_family = AF_INET, .sin_port = htons(8080),
                             .sin_addr.s_addr = htonl(INADDR_ANY) };
    if (bind(ls, (struct sockaddr *)&a, sizeof a) < 0) { perror("bind"); return 1; }
    listen(ls, 16);                               /* backlog of pending connections */

    for (;;) {
        int c = accept(ls, NULL, NULL);           /* blocks */
        if (c < 0) continue;
        char buf[512];
        ssize_t n;
        while ((n = recv(c, buf, sizeof buf, 0)) > 0)
            send(c, buf, (size_t)n, 0);
        close(c);
    }
}
```

**Details interviewers check**

- **Byte order:** ports and addresses are in network byte order (big-endian): `htons`, `htonl`, `ntohs`.
- **`SO_REUSEADDR`** lets the server restart immediately instead of failing with "Address already in use" while old connections are in `TIME_WAIT`.
- **TCP is a byte stream:** one `send()` of 1000 bytes may arrive as several `recv()` calls, and several sends may arrive together. Applications need framing (length prefix or delimiter).
- **Partial writes:** `send()` may send fewer bytes than requested; loop until all are sent.
- **`SIGPIPE`:** writing to a connection the peer closed kills the process unless you ignore `SIGPIPE` or use `MSG_NOSIGNAL`.
- **UDP** is different: `socket(AF_INET, SOCK_DGRAM, 0)`, no `listen`/`accept`/`connect` needed, `sendto`/`recvfrom` with addresses; each datagram is delivered whole or not at all.

**Handling many clients:** one process per client (`fork()` after `accept`), one thread per client, or one thread with `select`/`poll`/`epoll` (see the next question).

### Which socket calls block, and how do select, poll and epoll handle many connections? {M}
**Short answer:** By default `accept()` (until a client connects), `connect()` (until the handshake completes), `recv()`/`read()` (until data arrives), and `send()`/`write()` (until there is room in the send buffer) can all block. To handle many connections in one thread, make the sockets non-blocking and use an I/O multiplexer: `select()` and `poll()` scan a list of descriptors on every call (O(n)), while **`epoll`** registers descriptors once and returns only the ready ones (O(ready)), which scales to tens of thousands of connections.

**Why they block:** each call waits for something outside the program's control: a remote peer, the network, or buffer space. Blocking is efficient (the thread sleeps), but a thread blocked on one socket cannot serve others.

**Options for concurrency**

| Approach | Pros | Cons |
|---|---|---|
| fork per client | simple, isolated | heavy; one process per connection |
| thread per client | simple code | memory per thread (stack), context switches, locking |
| `select` | portable | limited to `FD_SETSIZE` (1024) descriptors, O(n) scan, fd sets rebuilt every call |
| `poll` | no fd limit | still O(n) per call |
| `epoll` (Linux) | O(1) per event, edge or level triggered | Linux-specific |
| `io_uring` | async I/O with few syscalls | newer, more complex |

**epoll event loop sketch**

```c
#include <sys/epoll.h>

int ep = epoll_create1(0);
struct epoll_event ev = { .events = EPOLLIN, .data.fd = listen_fd };
epoll_ctl(ep, EPOLL_CTL_ADD, listen_fd, &ev);

struct epoll_event events[64];
for (;;) {
    int n = epoll_wait(ep, events, 64, -1);       /* sleeps until something is ready */
    for (int i = 0; i < n; i++) {
        int fd = events[i].data.fd;
        if (fd == listen_fd) {
            int c = accept4(listen_fd, NULL, NULL, SOCK_NONBLOCK);
            struct epoll_event cev = { .events = EPOLLIN, .data.fd = c };
            epoll_ctl(ep, EPOLL_CTL_ADD, c, &cev);
        } else {
            handle_client(fd);                    /* non-blocking recv/send */
        }
    }
}
```

**Level vs edge triggered:** level-triggered (default) reports a descriptor as long as it is readable; edge-triggered (`EPOLLET`) reports only when new data arrives, so you must read until `EAGAIN` or you miss data.

**Timeouts without blocking forever:** `SO_RCVTIMEO`/`SO_SNDTIMEO`, a timeout argument to `poll`/`epoll_wait`, or non-blocking `connect()` followed by waiting for writability.

**Embedded relevance:** a gateway with a UART, a CAN socket, a few TCP connections and a timer can run everything in one `epoll` loop (using `timerfd`, `signalfd`, `eventfd`), which avoids threads and locks entirely. Event libraries such as libevent, libuv and Boost.Asio wrap this pattern.

### Why does Linux have a separate socket API instead of using only open/read/write? {M}
**Short answer:** Sockets **are** file descriptors, so `read()`, `write()`, `close()`, `poll()` and `epoll` work on them. But networking needs things a file path cannot express: choosing a protocol family and type (TCP vs UDP vs raw, IPv4 vs IPv6 vs Unix vs CAN), binding to local addresses and ports, connecting to or accepting from remote endpoints that may not exist yet, per-message addresses for datagrams, and many options. The socket API (`socket`, `bind`, `listen`, `accept`, `connect`, `sendto`, `recvfrom`, `setsockopt`, `shutdown`) adds exactly those operations.

**What the file API cannot express**

- **Creation without a name:** `socket(AF_INET6, SOCK_STREAM, 0)` creates an endpoint; there is nothing in the file system to `open()`.
- **Addresses:** a network peer is identified by an address and port (or a CAN ID, or a Bluetooth address), not a path. `bind()`/`connect()` take a generic `struct sockaddr`.
- **Connection set-up:** `listen()`/`accept()` create a **new** descriptor for each incoming connection, a concept files do not have.
- **Datagram semantics:** for UDP, each `sendto()` is one message with its own destination, and `recvfrom()` reports who sent each one. Message boundaries are preserved.
- **Options and control data:** `setsockopt()` (buffer sizes, `TCP_NODELAY`, keepalive, multicast membership, timestamps) and ancillary data with `sendmsg()`/`recvmsg()` (passing file descriptors over Unix sockets, packet info).
- **Half-close:** `shutdown(fd, SHUT_WR)` sends FIN but keeps reading.

**The design choice still unifies a lot:** because sockets are descriptors, they can be inherited across `fork()`, redirected by shells, passed to `poll()`/`epoll()` together with pipes, serial ports and timers, and closed with `close()`.

**Historical note:** the API came from 4.2BSD (1983) and became the POSIX standard. Plan 9 took the opposite approach and represented network connections as files (`/net/tcp/clone`), showing it is possible; it never became mainstream.

**Linux-specific families worth knowing in embedded work:** `AF_CAN` (SocketCAN for CAN bus), `AF_PACKET` (raw Ethernet frames), `AF_NETLINK` (configuring the kernel: routes, interfaces), `AF_UNIX` (local IPC), `AF_VSOCK` (host ↔ VM communication).

### How is the Linux networking stack structured, what is an sk_buff, and how does it compare with the OSI model? {H}
**Short answer:** In Linux, the socket layer and the protocols (TCP, UDP, IP) run in the kernel, network device drivers sit at the bottom, and the application layer is in user space. Packets travel through the layers in a **`struct sk_buff`** (socket buffer), which holds the packet data plus metadata (device, protocol, header offsets, timestamps). Headers are added or removed by moving pointers within the buffer rather than copying data. Linux follows the practical TCP/IP 4-layer model rather than the 7-layer OSI model.

**Layers (receive path, bottom to top)**

```
NIC hardware → DMA into ring buffer → IRQ → NAPI poll (driver)
  → netif_receive_skb()                 link layer (Ethernet, VLAN, bridge)
  → ip_rcv() → routing, netfilter       network layer (IPv4/IPv6)
  → tcp_v4_rcv() / udp_rcv()            transport layer
  → socket receive queue
  → recv() in the application           (copy to user space)
```

Transmit goes the other way: `send()` → TCP segments → IP routing/neighbour lookup → queueing discipline (qdisc, traffic shaping) → driver `ndo_start_xmit()` → DMA to the NIC.

**`sk_buff` essentials**

| Field | Purpose |
|---|---|
| `head`, `data`, `tail`, `end` | buffer boundaries; `data`..`tail` is the current packet |
| `skb_push()` / `skb_pull()` | add/remove a header by moving `data` (no copy) |
| `skb_reserve()` | leave headroom so lower layers can prepend headers |
| `dev`, `protocol`, `mark`, `tstamp` | metadata |
| `transport_header`, `network_header`, `mac_header` | offsets of each header |
| fragments / `skb_shinfo` | scatter-gather pages for large packets (GSO/GRO) |

**OSI vs Linux (TCP/IP)**

| OSI | Linux / TCP/IP | Where |
|---|---|---|
| 7 Application, 6 Presentation, 5 Session | Application (HTTP, MQTT, TLS) | user space |
| 4 Transport | TCP, UDP, SCTP | kernel |
| 3 Network | IPv4, IPv6, ICMP, routing, netfilter | kernel |
| 2 Data link | Ethernet, Wi-Fi (mac80211), bridge, VLAN | kernel + driver |
| 1 Physical | PHY, cable, radio | hardware (PHY driver configures it) |

OSI's presentation and session layers have no separate kernel layer; their functions (encryption, encoding, session management) are in applications or libraries (kernel TLS, `kTLS`, is a partial exception).

**Performance features:** NAPI (polling under load), GRO/GSO (combine or split large packets to reduce per-packet work), checksum and segmentation offload to the NIC, RSS/RPS (spread flows across cores), XDP (eBPF programs at the driver level), and AF_XDP or DPDK for user-space packet processing when the kernel stack is too slow.

**Why networking is treated differently from other I/O:** data arrives unsolicited and at unpredictable times, must be demultiplexed to the right socket by protocol and port, may be lost or reordered (TCP must handle retransmission and flow control), and rates can reach millions of packets per second, so per-packet overhead dominates.

### How do you find out why a Linux program is slow or stuck? {M}
**Short answer:** First look at what the process is doing and waiting for: `top`/`htop` (CPU, state), `ps -o stat,wchan` (where it sleeps), `strace -p PID` (system calls), `cat /proc/PID/stack` (kernel stack, as root), and `gdb -p PID` / `thread apply all bt` (user stacks). Then measure the right resource: `perf top`/`perf record` for CPU, `vmstat`/`iostat` for memory and I/O, `ss` for sockets, and PSI files for contention.

**Step by step**

1. **Is it using CPU?** `top -H -p PID` (per thread). High CPU → profile with `perf record -g -p PID` then `perf report`, or `perf top`.
2. **If not, what is it waiting for?** State `S` or `D` in `ps`. `strace -f -p PID` shows the blocking call (`read` on a socket, `futex` = waiting on a lock, `poll` with a timeout). `/proc/PID/wchan` names the kernel function it sleeps in.
3. **Deadlock?** `gdb -p PID`, `thread apply all bt`: look for threads waiting in `pthread_mutex_lock` on each other's locks.
4. **Memory?** `/proc/PID/status` (`VmRSS`, `VmSwap`), `smem`, `valgrind --tool=massif`, or `heaptrack` for growth; `vmstat 1` for swapping.
5. **I/O?** `iostat -x 1` (device utilisation and latency), `iotop`, `pidstat -d`.
6. **Network?** `ss -tinp` (per-connection queues, retransmits, RTT), `tcpdump`/Wireshark.
7. **System-wide pressure:** `/proc/pressure/{cpu,memory,io}` shows how much time tasks were stalled waiting for each resource.

**Tracing tools for deeper problems:** `ftrace` (`trace-cmd`, function graph, scheduler events), `perf sched latency` (scheduling delays), `bpftrace`/BCC tools (`offcputime`, `biolatency`, `runqlat`), and `ltrace` for library calls.

**Embedded tip:** many of these tools are missing from a minimal image. Build a debug image variant with `perf`, `strace`, `gdbserver` and `trace-cmd`, and use `gdbserver` + a cross `gdb` on your PC with the unstripped binaries from the build system.
