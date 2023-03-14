from contextlib import closing
from datetime import date, datetime
from socket import socket, AF_INET, SOCK_STREAM
from time import perf_counter, sleep
from typing import Optional


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


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None

    return dt.strftime("%Y-%m-%d %H:%M")


def str_to_date(s: str) -> Optional[date]:
    if s is None:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def date_to_str(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    return d.isoformat()


def dt_to_str(d: Optional[datetime]) -> Optional[str]:
    if d is None:
        return None
    return d.isoformat()
