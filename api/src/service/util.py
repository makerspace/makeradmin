from contextlib import closing
from socket import socket, AF_INET, SOCK_STREAM
from time import perf_counter, sleep


def can_connect(host, port):
    with closing(socket(AF_INET, SOCK_STREAM)) as sock:
        return 0 == sock.connect_ex((host, port))


def wait_for(func, timeout=2, interval=0.2):
    start = perf_counter()
    while perf_counter() < start + timeout:
        if func():
            return True
        sleep(interval)
    return False


def format_datetime(dt):
    if dt is None:
        return None

    return dt.strftime("%Y-%m-%d %H:%M")
