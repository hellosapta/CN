# error_injector.py
# Functions to flip bits in given data string to simulate error types

import random
from typing import Tuple

def flip_bit(bits: str, pos: int) -> str:
    b = list(bits)
    b[pos] = '1' if b[pos] == '0' else '0'
    return ''.join(b)

def inject_single(bits: str, pos: int = None) -> Tuple[str, list]:
    n = len(bits)
    if pos is None:
        pos = random.randrange(n)
    return flip_bit(bits, pos), [pos]

def inject_two_isolated(bits: str) -> Tuple[str, list]:
    n = len(bits)
    pos1 = random.randrange(n)
    pos2 = random.randrange(n)
    while pos2 == pos1:
        pos2 = random.randrange(n)
    b = list(bits)
    b[pos1] = '1' if b[pos1] == '0' else '0'
    b[pos2] = '1' if b[pos2] == '0' else '0'
    return ''.join(b), [pos1, pos2]

def inject_odd(bits: str, count: int = 3) -> Tuple[str, list]:
    # flip an odd number of randomly selected bits (default 3)
    n = len(bits)
    count = count if count % 2 == 1 else count + 1
    positions = random.sample(range(n), count)
    b = list(bits)
    for p in positions:
        b[p] = '1' if b[p] == '0' else '0'
    return ''.join(b), positions

def inject_burst(bits: str, burst_length: int = 5) -> Tuple[str, list]:
    n = len(bits)
    if burst_length >= n:
        burst_length = n//2
    start = random.randrange(0, n - burst_length + 1)
    b = list(bits)
    positions = []
    for i in range(start, start + burst_length):
        b[i] = '1' if b[i] == '0' else '0'
        positions.append(i)
    return ''.join(b), positions

def inject_random(bits: str, probability: float = 0.01) -> Tuple[str, list]:
    b = list(bits)
    positions = []
    for i in range(len(b)):
        if random.random() < probability:
            b[i] = '1' if b[i] == '0' else '0'
            positions.append(i)
    return ''.join(b), positions
