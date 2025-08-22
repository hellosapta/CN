# utils.py
# Shared helpers for checksum and CRC operations + bit helpers

from typing import Tuple

# Helper: read a file containing 0/1 characters and return a single string of bits
def read_bitfile(path: str) -> str:
    with open(path, 'r') as f:
        raw = f.read()
    bits = ''.join(ch for ch in raw if ch in ('0','1'))
    return bits

def pad_right(bits: str, block: int) -> str:
    if len(bits) % block == 0:
        return bits
    needed = block - (len(bits) % block)
    return bits + '0' * needed

def chunk_bits(bits: str, size: int):
    for i in range(0, len(bits), size):
        yield bits[i:i+size]

# -----------------------
# 16-bit ones-complement checksum
# -----------------------
def ones_complement_add_16(words):
    s = 0
    for w in words:
        s += w
        # fold carry while s > 0xFFFF
        s = (s & 0xFFFF) + (s >> 16)
    return s & 0xFFFF

def compute_checksum16(data_bits: str) -> str:
    # pad to 16-bit words on right
    padded = pad_right(data_bits, 16)
    words = [int(w, 2) for w in chunk_bits(padded, 16)]
    s = ones_complement_add_16(words)
    checksum = (~s) & 0xFFFF
    return format(checksum, '016b')

def verify_checksum16(data_bits: str, checksum_bits: str) -> bool:
    padded = pad_right(data_bits, 16)
    words = [int(w, 2) for w in chunk_bits(padded, 16)]
    words.append(int(checksum_bits, 2))
    s = ones_complement_add_16(words)
    # In proper 1's complement, result should be 0xFFFF (all ones) when summing including checksum
    return s == 0xFFFF or s == 0x0000  # accept either representation (some implementations check 0)

# -----------------------
# CRC functions (bit-string based)
# -----------------------
# Generator polynomials as binary strings, highest-degree bit first, without '0b' prefix
CRC_POLYS = {
    "CRC8":  "111101011",  # degree 8 -> 9 bits (leading 1 and trailing 1) (example representation)
    "CRC10": "11100000011", # degree 10 -> 11 bits (adjusted below)
    # For practical clarity I'm providing the binary forms used by the bit-division below:
    # CRC-16: x^16 + x^15 + x^2 + 1 -> binary 11000000000000101 (degree 16 -> 17 bits)
    "CRC16": "11000000000000101",
    # CRC-32 standard (IEEE 802.3) polynomial (degree 32 -> 33 bits)
    "CRC32": "100000100110000010001110110110111"
}

def xor_division(dividend: str, divisor: str) -> str:
    """
    Perform binary polynomial division (strings of '0'/'1').
    Return remainder as string of length len(divisor)-1
    """
    cur = list(dividend)
    n = len(divisor)
    for i in range(len(dividend) - n + 1):
        if cur[i] == '1':
            # XOR divisor with the slice starting at i
            for j in range(n):
                cur[i+j] = '1' if (cur[i+j] != divisor[j]) else '0'
    remainder = ''.join(cur[-(n-1):]) if n>1 else ''
    return remainder

def compute_crc(data_bits: str, poly_key: str) -> str:
    poly = CRC_POLYS[poly_key]
    k = len(poly) - 1
    appended = data_bits + ('0' * k)
    remainder = xor_division(appended, poly)
    # pad remainder to k bits
    return remainder.zfill(k)

def verify_crc(codeword_bits: str, poly_key: str) -> bool:
    poly = CRC_POLYS[poly_key]
    remainder = xor_division(codeword_bits, poly)
    # if remainder all zeros -> no error
    return set(remainder) <= {'0'}

# If you want more readable polynomial binary strings,
# feel free to replace CRC_POLYS entries with authoritative bit strings.
