#!/usr/bin/env python3
"""
شیطون انتن | Sheitoon Antenna
ساخت فایل .mobileconfig

تغییرات نسبت به نسخه قبل (برای پایداری):
  * PayloadIdentifier برای کل پروژه ثابت است (حتی بین اپراتورها و نسخه‌ها)؛ فقط PayloadUUID هر بار عوض می‌شود.
    در نتیجه نصب دوباره، پروفایل قبلی را جایگزین می‌کند و پروفایل‌ها روی هم جمع نمی‌شوند.
  * یک منبع واحد برای تعریف APN (همین فایل) تا وب، اسکریپت و قالب‌ها یکی باشند.
  * خروجی با plistlib ساخته می‌شود؛ نام پروفایل شامل & < > هم فایل را خراب نمی‌کند.
  * ProxyServer خالی حذف شد.
  * ورودی IPv4-only همراه با XLAT464 حذف شد (XLAT464 فقط وقتی معنی دارد که شبکه IPv6 باشد).

استفاده:
  python3 generate_profile.py                          # حالت تعاملی
  python3 generate_profile.py -o mci -v B             # نسخه تست B برای همراه اول
  python3 generate_profile.py -o mci -n "اسم دلخواه"   # غیرتعاملی
  python3 generate_profile.py --write-templates        # بازسازی پوشه templates
"""

import argparse
import os
import plistlib
import re
import sys
import uuid
from datetime import datetime

# کلید -> (نام نمایشی، لیست APN ها). APN اول، APN اصلی (AttachAPN) است.
OPERATORS = {
    "mci":      {"name": "همراه اول (MCI)",   "apns": ["mcinet"]},
    "irancell": {"name": "ایرانسل (Irancell)", "apns": ["mtnirancell"]},
    "rightel":  {"name": "رایتل (RighTel)",    "apns": ["RighTel"]},
    "aptel":    {"name": "آپتل (ApTel)",       "apns": ["ApTel"]},
    "samantel": {"name": "سامانتل",            "apns": ["samantel"]},
    "shatel":   {"name": "شاتل موبایل",        "apns": ["shatelmobile"]},
    "dual":     {"name": "دوتایی: همراه اول + ایرانسل", "apns": ["mcinet", "mtnirancell"]},
}

ID_PREFIX = "com.sheitoon.antenna"
PLACEHOLDER = "REPLACE_UUID"

# پروتکل: 1 = IPv4، 2 = IPv6، 3 = هر دو
# نسخه‌ها: هر کدام فقط «یک» متغیر را نسبت به A عوض می‌کند تا نتیجه تست قابل تفسیر باشد.
VARIANTS = {
    "A": {"label": "استاندارد (پیشنهادی)",   "auths": ["PAP", "CHAP"], "proto": 3, "xlat": True},
    "B": {"label": "فقط PAP",                "auths": ["PAP"],         "proto": 3, "xlat": True},
    "C": {"label": "فقط IPv4 (بدون XLAT464)", "auths": ["PAP", "CHAP"], "proto": 1, "xlat": False},
    "D": {"label": "بدون XLAT464",            "auths": ["PAP", "CHAP"], "proto": 3, "xlat": False},
}
DEFAULT_VARIANT = "A"

CUSTOM_KEY = "custom"
CUSTOM_NAME = "APN دلخواه"
MAX_LEN = 100


_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def validate_custom(custom: dict) -> dict:
    """ورودی APN دلخواه را بررسی و تمیز می‌کند. ValueError با پیام فارسی می‌دهد."""
    c = {k: (custom.get(k) or "").strip() for k in ("apn", "username", "proxy_host")}
    c["password"] = custom.get("password") or ""   # رمز دست‌نخورده می‌ماند (فاصله جزو رمز است)
    port = custom.get("proxy_port")
    port = str(port).strip().translate(_DIGITS) if port not in (None, "") else ""
    if not c["apn"]:
        raise ValueError("نام APN الزامی است")
    for k, v in c.items():
        if len(v) > MAX_LEN:
            raise ValueError(f"فیلد {k} بیش از {MAX_LEN} کاراکتر است")
        if any(ord(ch) < 32 for ch in v):
            raise ValueError(f"فیلد {k} کاراکتر نامعتبر دارد")
    if port:
        if not re.fullmatch(r"[0-9]+", port) or not (1 <= int(port) <= 65535):
            raise ValueError("پورت پروکسی باید عددی بین ۱ تا ۶۵۵۳۵ باشد")
        if not c["proxy_host"]:
            raise ValueError("پورت بدون آدرس پروکسی معنی ندارد")
    c["proxy_port"] = int(port) if port else None
    return c


def _apn_entry(name: str, auth: str, proto: int, xlat: bool, cred: dict = None) -> dict:
    cred = cred or {}
    e = {
        "Name": name,
        "AuthenticationType": auth,
        "Username": cred.get("username", ""),
        "Password": cred.get("password", ""),
        "AllowedProtocolMask": proto,
        "AllowedProtocolMaskInRoaming": proto,
        "AllowedProtocolMaskInDomesticRoaming": proto,
        "DefaultProtocolMask": proto,
    }
    if xlat:
        e["EnableXLAT464"] = True
    if cred.get("proxy_host"):
        e["ProxyServer"] = cred["proxy_host"]
        if cred.get("proxy_port"):
            e["ProxyPort"] = cred["proxy_port"]
    return e


def build_profile(key: str, profile_name: str = None, fixed_uuid: str = None, variant: str = DEFAULT_VARIANT, custom: dict = None) -> dict:
    """دیکشنری پروفایل را می‌سازد. fixed_uuid فقط برای ساخت قالب/تست است."""
    cred = None
    if key == CUSTOM_KEY:
        cred = validate_custom(custom or {})
        op = {"name": CUSTOM_NAME, "apns": [cred["apn"]]}
    else:
        op = OPERATORS[key]
    v = VARIANTS[variant]
    counter = iter(range(1, 100))
    new_uuid = (lambda: f"{fixed_uuid}_{next(counter)}") if fixed_uuid else (lambda: str(uuid.uuid4()).upper())
    suffix = "" if variant == DEFAULT_VARIANT else f" ({variant})"
    profile_name = (profile_name or "").strip()
    if len(profile_name) > 40:
        raise ValueError("نام پروفایل بیش از ۴۰ کاراکتر است")
    profile_name = profile_name or f"شیطون انتن - {op['name']}{suffix}"

    apns = [_apn_entry(apn, auth, v["proto"], v["xlat"], cred) for apn in op["apns"] for auth in v["auths"]]

    cellular = {
        "PayloadType": "com.apple.cellular",
        "PayloadDisplayName": "Cellular",
        # ثابت: نصب مجدد همین را جایگزین می‌کند
        "PayloadIdentifier": f"{ID_PREFIX}.cellular",
        "PayloadUUID": new_uuid(),
        "PayloadVersion": 1,
        "APNs": apns,
        "AttachAPN": {
            "Name": op["apns"][0],
            "AuthenticationType": v["auths"][0],
            "Username": (cred or {}).get("username", ""),
            "Password": (cred or {}).get("password", ""),
            "AllowedProtocolMask": v["proto"],
        },
    }

    return {
        "PayloadType": "Configuration",
        "PayloadDisplayName": profile_name,
        "PayloadDescription": f"پروفایل بازگردانی آنتن - شیطون انتن - نسخه {variant}",
        "PayloadOrganization": "شیطون انتن | Sheitoon Antenna",
        "PayloadIdentifier": ID_PREFIX,   # ثابت برای کل پروژه: هر نصب جدید (اپراتور/نسخه دیگر) پروفایل قبلی را جایگزین می‌کند
        "PayloadUUID": new_uuid(),
        "PayloadVersion": 1,
        "PayloadRemovalDisallowed": False,
        "PayloadContent": [cellular],
    }


def create_mobileconfig(key: str, profile_name: str = None, fixed_uuid: str = None, variant: str = DEFAULT_VARIANT, custom: dict = None) -> bytes:
    return plistlib.dumps(build_profile(key, profile_name, fixed_uuid, variant, custom), fmt=plistlib.FMT_XML)


def write_templates(templates_dir: str) -> None:
    os.makedirs(templates_dir, exist_ok=True)
    for key in OPERATORS:
        path = os.path.join(templates_dir, f"{key}.mobileconfig")
        with open(path, "wb") as f:
            f.write(create_mobileconfig(key, fixed_uuid=PLACEHOLDER))
        print("wrote", path)


def _choose_interactive() -> str:
    keys = list(OPERATORS)
    print("=" * 55)
    print("  😈 شیطون انتن - Profile Generator")
    print("=" * 55)
    print("\nاپراتور مورد نظر را انتخاب کنید:\n")
    for i, k in enumerate(keys, 1):
        print(f"  {i}. {OPERATORS[k]['name']}")
    choice = input("\nشماره اپراتور: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(keys)):
        print("❌ انتخاب نامعتبر")
        sys.exit(1)
    return keys[int(choice) - 1]


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(here, "..")

    ap = argparse.ArgumentParser(description="Sheitoon Antenna profile generator")
    ap.add_argument("-o", "--operator", choices=list(OPERATORS) + [CUSTOM_KEY],
                    help="custom = APN دلخواه (با --apn)")
    ap.add_argument("--apn", help="نام APN (فقط با -o custom)")
    ap.add_argument("--username", default="")
    ap.add_argument("--password", default="")
    ap.add_argument("--proxy", default="", help="host یا host:port")
    ap.add_argument("-v", "--variant", choices=list(VARIANTS), default=DEFAULT_VARIANT,
                    help="نسخه تست: " + " | ".join(f"{k}={x['label']}" for k, x in VARIANTS.items()))
    ap.add_argument("-n", "--name", help="نام نمایشی پروفایل")
    ap.add_argument("--out", default=os.path.join(root, "output"), help="پوشه خروجی")
    ap.add_argument("--write-templates", action="store_true", help="بازسازی templates/")
    args = ap.parse_args(argv)

    if args.write_templates:
        write_templates(os.path.join(root, "templates"))
        return

    custom = None
    if args.operator == CUSTOM_KEY:
        host, _, port = args.proxy.partition(":")
        custom = {"apn": args.apn, "username": args.username, "password": args.password,
                  "proxy_host": host, "proxy_port": port}
        try:
            validate_custom(custom)
        except ValueError as e:
            ap.error(str(e))

    interactive = args.operator is None
    key = args.operator or _choose_interactive()
    name = args.name
    if interactive and name is None:
        name = input("نام پروفایل (Enter برای پیش‌فرض): ").strip() or None

    try:
        data = create_mobileconfig(key, name, variant=args.variant, custom=custom)
    except ValueError as e:
        ap.error(str(e))
    os.makedirs(args.out, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(args.out, f"sheitoon_{key}_{args.variant}_{stamp}.mobileconfig")
    with open(path, "wb") as f:
        f.write(data)

    print("\n✅ پروفایل ساخته شد:", os.path.abspath(path))
    print("اگر قبلاً پروفایل شیطون انتن نصب کرده‌اید، نصب این فایل آن را جایگزین می‌کند.")


if __name__ == "__main__":
    main()
