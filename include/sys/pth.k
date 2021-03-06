/**
 * pth contains low level threading / multiprocessing access.
 */
#ifndef __PTH
#define __PTH 1

#include "util/stddef.k"
#include "io/filesystem.cb"
#include "util/memory.cb"
#include "util/cstring.cb"
#include "sys/syscall.k"
typedef long pid_t;

/* Cloning flags.  */
#define CSIGNAL                    0x000000ff /* Signal mask to be sent at exit.  */
#define CLONE_VM                   0x00000100 /* Set if VM shared between processes.  */
#define CLONE_FS                   0x00000200 /* Set if fs info shared between processes.  */
#define CLONE_FILES                0x00000400 /* Set if open files shared between processes.  */
#define CLONE_SIGHAND              0x00000800 /* Set if signal handlers shared.  */
#define CLONE_PTRACE               0x00002000 /* Set if tracing continues on the child.  */
#define CLONE_VFORK                0x00004000 /* Set if the parent wants the child to wake it up on mm_release.  */
#define CLONE_PARENT               0x00008000 /* Set if we want to have the same parent as the cloner.  */
#define CLONE_THREAD               0x00010000 /* Set to add to same thread group.  */
#define CLONE_NEWNS                0x00020000 /* Set to create new namespace.  */
#define CLONE_SYSVSEM              0x00040000 /* Set to shared SVID SEM_UNDO semantics.  */
#define CLONE_SETTLS               0x00080000 /* Set TLS info.  */
#define CLONE_PARENT_SETTID        0x00100000 /* Store TID in userlevel buffer before MM copy.  */
#define CLONE_CHILD_CLEARTID       0x00200000 /* Register exit futex and memory location to clear.  */
#define CLONE_DETACHED             0x00400000 /* Create clone detached.  */
#define CLONE_UNTRACED             0x00800000 /* Set if the tracing process can't force CLONE_PTRACE on this clone.  */
#define CLONE_CHILD_SETTID         0x01000000 /* Store TID in userlevel buffer in the child.  */
#define CLONE_NEWCGROUP            0x02000000        /* New cgroup namespace.  */
#define CLONE_NEWUTS               0x04000000        /* New utsname group.  */
#define CLONE_NEWIPC               0x08000000        /* New ipcs.  */
#define CLONE_NEWUSER              0x10000000        /* New user namespace.  */
#define CLONE_NEWPID               0x20000000        /* New pid namespace.  */
#define CLONE_NEWNET               0x40000000        /* New network namespace.  */
#define CLONE_IO                   0x80000000        /* Clone I/O context.  */


/**
 * https://man7.org/linux/man-pages/man2/fork.2.html
 */
inline long fork(){
    syscall(SYS_fork);
}
/**
 * https://man7.org/linux/man-pages/man2/vfork.2.html
 */ 
inline long vfork(){
    syscall(SYS_vfork);
}
/**
 * Overwrite the current process with data found from pathname.
 * 
 * https://man7.org/linux/man-pages/man2/execve.2.html
 * @param pathname path
 * @param args arguments to pass into the new process
 * @param env environment variables
 * @returns On success execve does not return, on error it will return -1
 * 
 */
inline long execve(char* pathname, char** args, char** env){
    syscall(SYS_execve);

}
/**
 * https://www.man7.org/linux/man-pages/man2/pause.2.html
 */
inline long pause(){
    syscall(SYS_pause);

}


inline int waitid(int idtype, long id, void *infop, int options){
    syscall(SYS_waitid);
}

/**
 * https://www.man7.org/linux/man-pages/man2/waitpid.2.html
 */
inline long waitpid(pid_t pid, int *wstatus, int options){
    return waitid(0, pid, wstatus, options);
}

typedef void siginfo;
typedef void rusage;

/**
 * ID types:
 */
#define P_PID 0     /* Process id */
#define P_PGID 1    /* Process group id */
#define P_ALL 2     /* any id */

/**
 * https://www.man7.org/linux/man-pages/man2/waitpid.2.html
 */
inline long waitid(int idtype,pid_t upid, siginfo *infop, int options,rusage *ru){
    syscall(SYS_waitid);

}

/**
 * clone creates a new process. (This is the underlying function used by fork and vfork).
 * @param clone_flags a bitwize or of 0 or more of the flags listed at the top of this file
 * @param newsp a pointer to the new stack of this process.
 * @param parent_tid (optional) a pointer to write parent_tid into
 * @param child_tid (optional) a pointer to write child_tid into
 * @param tid (optional) thread id
 * @returns 0 is returned to the child, and the child tid is returned to the parent process, or errors will be returned to parent.
 */
inline long clone(unsigned long clone_flags, void* newsp, void* parent_tid, void* child_tid, unsigned int tid){
    syscall(SYS_clone);

}
/**
 * End execution with exit code c
 * @param c exit code
 * @returns on success, exit does not return.
 */
inline void exit(long c){
    syscall(SYS_exit);

}

/**
 * https://www.man7.org/linux/man-pages/man2/tgkill.2.html
 */
inline long tgkill(pid_t tgid, pid_t pid, long sig){
    syscall(SYS_tgkill);

}
/**
 * Get local thread id
 */
inline long gettid(){
    syscall(SYS_gettid);

}
/**
 * Get local process id
 */
inline long getpid(){
    syscall(SYS_getpid);

}
/**
 * https://man7.org/linux/man-pages/man2/wait4.2.html
 */
inline long wait4(pid_t upid, int*stat_addr, long options, void*ru){
    syscall(SYS_wait4);
}



#endif