#!/usr/bin/env python3
"""
شیطون انتن | Sheitoon Antenna
Full Profile Generator - ساخت فایل .mobileconfig کامل با UUID یکتا
"""

import uuid
import os
from datetime import datetime

OPERATORS = {
    "1": {"name": "همراه اول (MCI)", "apn": "mcinet"},
    "2": {"name": "ایرانسل (Irancell)", "apn": "mtnirancell"},
    "3": {"name": "رایتل (RighTel)", "apn": "RighTel"},
    "4": {"name": "آپتل (ApTel)", "apn": "ApTel"},
    "5": {"name": "سامانتل", "apn": "samantel"},
    "6": {"name": "شاتل موبایل", "apn": "shatelmobile"},
}

def generate_uuid():
    return str(uuid.uuid4())

def create_mobileconfig(apn: str, profile_name: str = None) -> str:
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    uuid3 = generate_uuid()

    if not profile_name:
        profile_name = f"شیطون انتن - {apn}"

    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>PayloadContent</key>
  <array>
    <dict>
      <key>PayloadDisplayName</key>
      <string>Cellular</string>
      <key>PayloadIdentifier</key>
      <string>com.apple.cellular.{uuid1}</string>
      <key>PayloadType</key>
      <string>com.apple.cellular</string>
      <key>PayloadUUID</key>
      <string>{uuid1}</string>
      <key>PayloadVersion</key>
      <integer>1</integer>
      <key>APNs</key>
      <array>
        <dict>
          <key>AllowedProtocolMask</key>
          <integer>3</integer>
          <key>AllowedProtocolMaskInDomesticRoaming</key>
          <integer>3</integer>
          <key>AllowedProtocolMaskInRoaming</key>
          <integer>3</integer>
          <key>AuthenticationType</key>
          <string>PAP</string>
          <key>DefaultProtocolMask</key>
          <integer>3</integer>
          <key>EnableXLAT464</key>
          <true/>
          <key>Name</key>
          <string>{apn}</string>
          <key>ProxyServer</key>
          <string></string>
          <key>Username</key>
          <string></string>
        </dict>
        <dict>
          <key>AllowedProtocolMask</key>
          <integer>1</integer>
          <key>AllowedProtocolMaskInDomesticRoaming</key>
          <integer>1</integer>
          <key>AllowedProtocolMaskInRoaming</key>
          <integer>1</integer>
          <key>AuthenticationType</key>
          <string>CHAP</string>
          <key>DefaultProtocolMask</key>
          <integer>1</integer>
          <key>EnableXLAT464</key>
          <true/>
          <key>Name</key>
          <string>{apn}</string>
          <key>Username</key>
          <string></string>
        </dict>
      </array>
      <key>AttachAPN</key>
      <dict>
        <key>AllowedProtocolMask</key>
        <integer>3</integer>
        <key>AuthenticationType</key>
        <string>PAP</string>
        <key>Name</key>
        <string>{apn}</string>
        <key>Username</key>
        <string></string>
      </dict>
    </dict>
  </array>
  <key>PayloadDisplayName</key>
  <string>{profile_name}</string>
  <key>PayloadIdentifier</key>
  <string>com.sheitoon.antenna.{uuid2}</string>
  <key>PayloadRemovalDisallowed</key>
  <false/>
  <key>PayloadType</key>
  <string>Configuration</string>
  <key>PayloadUUID</key>
  <string>{uuid3}</string>
  <key>PayloadVersion</key>
  <integer>1</integer>
  <key>PayloadDescription</key>
  <string>پروفایل بازگردانی آنتن - شیطون انتن</string>
  <key>PayloadOrganization</key>
  <string>شیطون انتن | Sheitoon Antenna</string>
</dict>
</plist>'''
    return plist

def main():
    print("=" * 55)
    print("  😈 شیطون انتن - Profile Generator")
    print("=" * 55)
    print()
    print("اپراتور مورد نظر را انتخاب کنید:")
    print()
    for key, op in OPERATORS.items():
        print(f"  {key}. {op['name']}")
    print()

    choice = input("شماره اپراتور: ").strip()
    if choice not in OPERATORS:
        print("❌ انتخاب نامعتبر")
        return

    op = OPERATORS[choice]
    custom_name = input(f"نام پروفایل (Enter برای پیش‌فرض 'شیطون - {op['name']}'): ").strip()
    profile_name = custom_name if custom_name else f"شیطون انتن - {op['name']}"

    content = create_mobileconfig(op["apn"], profile_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sheitoon_{op['apn']}_{timestamp}.mobileconfig"
    
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print()
    print("✅ پروفایل با موفقیت ساخته شد!")
    print(f"📁 مسیر فایل: {filepath}")
    print()
    print("حالا فایل را به آیفون منتقل کنید و نصب کنید.")

if __name__ == "__main__":
    main()
