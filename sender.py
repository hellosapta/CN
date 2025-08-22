# sender.py
# Usage:
# python3 sender.py --file test_bits.txt --host 127.0.0.1 --port 9000 --scheme crc --crc CRC16 --inject burst

import argparse
import json
import socket
import time

from utils import read_bitfile, compute_checksum16, compute_crc
import error_injector as ei
import random

def prepare_codeword(bits: str, scheme: str, crc_key: str=None):
    if scheme == "checksum":
        checksum = compute_checksum16(bits)
        return checksum
    elif scheme == "crc":
        if crc_key is None:
            raise ValueError("crc_key required for CRC scheme")
        crc = compute_crc(bits, crc_key)
        return crc
    else:
        raise ValueError("Unknown scheme")

def inject_errors(bits: str, mode: str):
    if mode is None or mode.lower() == "none":
        return bits, []
    mode = mode.lower()
    if mode == "single":
        return ei.inject_single(bits)
    if mode == "double":
        return ei.inject_two_isolated(bits)
    if mode == "odd":
        return ei.inject_odd(bits)
    if mode == "burst":
        return ei.inject_burst(bits)
    if mode == "random":
        # default 1% bit flip probability
        return ei.inject_random(bits, probability=0.01)
    # unknown mode: treat as none
    return bits, []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="path to bit file (0/1 text)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", default=9000, type=int)
    ap.add_argument("--scheme", default="crc", choices=["crc","checksum"])
    ap.add_argument("--crc", default="CRC16", help="CRC key if scheme=crc (CRC8, CRC10, CRC16, CRC32)")
    ap.add_argument("--inject", default=None, help="error injection mode: single,double,odd,burst,random,none")
    args = ap.parse_args()

    data_bits = read_bitfile(args.file)
    if len(data_bits) == 0:
        print("No bits found in file.")
        return

    # prepare codeword for original data
    code_bits = prepare_codeword(data_bits, args.scheme, crc_key=args.crc if args.scheme=="crc" else None)
    # full codeword string for checking at receiver = data + code_bits
    codeword = data_bits + code_bits

    # randomly decide whether to call error injector BEFORE sending (assignment asks sender to randomly call)
    if args.inject is None:
        # 50% chance to inject; user may override with --inject
        if random.random() < 0.5:
            inject_mode = random.choice(["single","double","odd","burst","random","none"])
        else:
            inject_mode = "none"
    else:
        inject_mode = args.inject

    sent_data_bits = data_bits
    injected_positions = []
    if inject_mode != "none":
        sent_data_bits, injected_positions = inject_errors(data_bits, inject_mode)

    # recompute code_bits after injection? The assignment states: "Sender will randomly call this method before sending the codewords"
    # That usually means inject errors into the codeword that is sent (i.e., simulate channel corruption). So we should compute codeword from original data, then inject errors into the codeword (data+code) rather than recompute the code for corrupted data.
    # For simplicity we will inject errors into the full codeword (data + code), so receiver sees corrupted codeword.
    full_codeword = data_bits + code_bits
    if inject_mode != "none":
        # inject into full_codeword
        full_codeword, injected_positions = inject_errors(full_codeword, inject_mode)

    frame = {
        "scheme": args.scheme,
        "crc_poly": args.crc if args.scheme=="crc" else None,
        "data": data_bits,
        "codeword": code_bits,
        "sent_payload": full_codeword,
        "inject_mode": inject_mode,
        "injected_positions": injected_positions
    }

    payload = json.dumps(frame) + "\n"

    print(f"Connecting to {args.host}:{args.port} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.host, args.port))
    print("Connected. Sending frame...")
    s.sendall(payload.encode('utf-8'))
    # wait for response
    resp = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
        if b'\n' in resp:
            break
    try:
        respmsg = resp.decode('utf-8').strip()
        print("Receiver response:", respmsg)
    except Exception as e:
        print("Couldn't decode response:", e)
    s.close()

if __name__ == "__main__":
    main()
