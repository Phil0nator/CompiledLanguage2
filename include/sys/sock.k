/**
 * sock.k contains low level system socket access.
 */
#ifndef __SYSSOCK
#define __SYSSOCK 1

#include "files.k" // fd_t, read, write, etc...
#include "syscall.k" // syscall info

/** 32bit ip address type */
typedef int in_addr;

struct sockaddr_in
{
    short                   sin_family;     // e.g. AF_INET
    short                   sin_port;       // e.g. htons(3490)
    in_addr                 sin_addr;       // address (big endian 32 bit)
    long                    sin_zero = 0;   // 

};

struct sockaddr_un{
    short sun_family;
    char sun_path[108];
};



struct sockproto
{
    short data;
};

struct linger_t {

    int32 l_onoff;
    int32 l_linger;

};

/* socket types */
#define SOCK_STREAM       1
#define SOCK_DGRAM        2
#define SOCK_RAW          3
#define SOCK_SEQPACKET    5

#define SO_DEBUG          0x0001
#define SO_ACCEPTCONN     0x0002
#define SO_REUSEADDR      0x0004
#define SO_KEEPALIVE      0x0008
#define SO_DONTROUTE      0x0010
#define SO_BROADCAST      0x0020
#define SO_USELOOPBACK    0x0040
#define SO_LINGER         0x0080
#define SO_OOBINLINE      0x0100

#define SO_SNDBUF         0x1001
#define SO_RCVBUF         0x1002
#define SO_SNDLOWAT       0x1003
#define SO_RCVLOWAT       0x1004
#define SO_SNDTIMEO       0x1005
#define SO_RECVTIMEO      0x1006
#define SO_ERROR          0x1007
#define SO_TYPE           0x1008

#define SOL_SOCKET        0xffff

#define AF_UNSPEC  0
#define AF_UNIX  1
#define AF_INET 2
#define AF_AX25 3
#define AF_IPX 4
#define AF_APPLETALK 5
#define AF_NETROM 6 
#define AF_BRIDGE 7 
#define AF_AAL5 8 
#define AF_X25 9 
#define AF_INET6 10 
#define AF_MAX   12 





/**
 * socket promts the os to create a socket based on parameters.
 * @param family socket family, e.g AF_INET
 * @param type socket type, e.g SOCK_STREAM
 * @param protocal (optional), e.g SO_LINGER
 * @returns a new socket file descriptor, or a negative error
 */
inline fd_t socket(int family, int type, int protocol){
    syscall(SYS_socket);
}
/**
 * connect a socket held by fd to an address.
 * @param fd socket
 * @param uservaddr address to connect to
 * @param addrlen size of the structure used in uservaddr (simply use sizeof struct sockaddr_in)
 * @returns 0 on success, negative error on failure
 */
inline int connect(fd_t fd, sockaddr_in *uservaddr, int addrlen){
    syscall(SYS_connect);
}
/**
 * Accept an incoming connection to socket fd.
 * @param fd socket 
 * @param uservaddr pointer to location to be filled with the incoming connection information
 * @param addrlen size of uservaddr
 * @returns a new file descriptor for a socket connected with the incoming connection
 */
inline int accept(fd_t fd, sockaddr_in*uservaddr, int addrlen){
    syscall(SYS_accept);
}
/**
 * bind a socket to an address and port
 * @param fd socket
 * @param umyaddr address/port to bind to
 * @param addrlen sizeof umyaddr
 * @returns 0 on success, negative error
 */
inline int bind(fd_t fd, sockaddr_in*umyaddr, int addrlen){
    syscall(SYS_bind);
}
/**
 * Set a socket to listen for incoming connections:
 * https://man7.org/linux/man-pages/man2/listen.2.html
 */
inline int listen(fd_t fd, int backlog){
    syscall(SYS_listen);
}
/**
 * Shutdown socket sockfd with code how.
 * https://man7.org/linux/man-pages/man2/shutdown.2.html
 */
inline int shutdown(fd_t sockfd, int how){
    syscall(SYS_shutdown);
}
/**
 * https://man7.org/linux/man-pages/man2/recvfrom.2.html
 */
inline int recvfrom(fd_t sockfd, char* buff, size_t len, int flags, sockaddr_in* addr, size_t addrsize){
    syscall(SYS_recvfrom);
}
/**
 * https://www.man7.org/linux/man-pages/man2/sendto.2.html
 */
inline int sendto(fd_t fd, void* buff, size_t len, int flags, sockaddr_in* addr, size_t addrsize){
    syscall(SYS_sendto);
}





#endif