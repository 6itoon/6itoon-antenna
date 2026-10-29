#!/usr/bin/env python3
"""
شیطون انتن | Sheitoon Antenna
UUID Generator for iPhone Antenna Profiles
"""

import uuid
import sys

def generate_uuid():
    return str(uuid.uuid4())

def generate_uuid_hex():
    return uuid.uuid4().hex

def main():
    print("=" * 50)
    print("  😈 شیطون انتن - UUID Generator")
    print("=" * 50)
    print()
    
    u = generate_uuid()
    u_hex = generate_uuid_hex()
    
    print(f"UUID استاندارد : {u}")
    print(f"UUID بدون خط  : {u_hex}")
    print()
    print("این کد را در بخش PayloadUUID فایل mobileconfig قرار دهید.")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        print(u)

if __name__ == "__main__":
    main()
