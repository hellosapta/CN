# receiver.py
# Usage:
# python3 receiver.py --port 9000

import argparse
import socket
import json

from utils import verify_checksum16, verify_crc

def handle_frame(frame_json: str) -> str:
    try:
        frame = json.loads(frame_json)
    except:
        return "REJECT: malformed JSON"
    scheme = frame.get("scheme")
    crc_poly = frame.get("crc_poly")
    data = frame.get("data")
    codeword_sent = frame.get("codeword")
    # Depending on sender behavior, the 'sent_payload' field contains the actual bits received over channel.
    sent_payload = frame.get("sent_payload")  # this represents data+codeword potentially corrupted
    # If sent_payload missing, construct from data+codeword
    if sent_payload is None:
        sent_payload = (data or "") + (codeword_sent or "")

    if scheme == "checksum":
        # data portion length == len(data)
        # codeword_len assumed 16 bits
        data_received = sent_payload[:len(data)]
        checksum_received = sent_payload[len(data):len(data)+16]
        ok = verify_checksum16(data_received, checksum_received)
        return "ACCEPT" if ok else "REJECT"
    elif scheme == "crc":
        # For CRC, determine k from poly
        codeword_received = sent_payload
        ok = verify_crc(codeword_received, crc_poly)
        return "ACCEPT" if ok else "REJECT"
    else:
        return "REJECT: unknown scheme"

def serve(host: str, port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    print(f"Receiver listening on {host}:{port}")
    while True:
        conn, addr = s.accept()
        print("Connection from", addr)
        data = b''
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b'\n' in data:
                break
        try:
            msg = data.decode('utf-8').strip()
        except:
            msg = ''
        result = handle_frame(msg)
        conn.sendall((result + "\n").encode('utf-8'))
        conn.close()
        print("Processed frame ->", result)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", default=9000, type=int)
    args = ap.parse_args()
    serve(args.host, args.port)
