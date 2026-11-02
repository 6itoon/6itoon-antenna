#!/usr/bin/env python3
"""اعتبارسنجی پروفایل‌ها. اجرا: python3 tests/test_profiles.py
اگر playwright نصب باشد، خروجی واقعی سایت هم با نسخه پایتون مقایسه می‌شود."""
import os, plistlib, re, sys, uuid, copy

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import generate_profile as g

fails = []
def check(cond, msg):
    if not cond:
        fails.append(msg); print("FAIL:", msg)

def validate(d, key, label, variant="A"):
    v = g.VARIANTS[variant]
    check(d["PayloadType"] == "Configuration", f"{label}: outer type")
    check(d["PayloadIdentifier"] == g.ID_PREFIX, f"{label}: outer identifier not stable")
    inner = d["PayloadContent"]
    check(len(inner) == 1 and inner[0]["PayloadType"] == "com.apple.cellular", f"{label}: inner payload")
    c = inner[0]
    check(c["PayloadIdentifier"] == f"{g.ID_PREFIX}.cellular", f"{label}: inner identifier not stable")
    check(c["PayloadUUID"] != d["PayloadUUID"], f"{label}: uuids must differ")
    expected = g.OPERATORS[key]["apns"]
    names = [a["Name"] for a in c["APNs"]]
    check(names == [n for n in expected for _ in v["auths"]], f"{label}: APN names {names}")
    for a in c["APNs"]:
        check(a["AllowedProtocolMask"] == v["proto"] and a.get("EnableXLAT464", False) == v["xlat"], f"{label}: apn flags")
        check("ProxyServer" not in a, f"{label}: empty proxy present")
    check(c["AttachAPN"]["Name"] == expected[0], f"{label}: attach apn")
    for u in (d["PayloadUUID"], c["PayloadUUID"]):
        if not u.startswith(g.PLACEHOLDER):
            uuid.UUID(u)

def strip(d):
    d = copy.deepcopy(d)
    d["PayloadUUID"] = "X"; d["PayloadContent"][0]["PayloadUUID"] = "X"
    return d

# 1) قالب‌ها و خروجی پایتون
for key in g.OPERATORS:
    for var in g.VARIANTS:
        validate(plistlib.loads(g.create_mobileconfig(key, variant=var)), key, f"python/{key}/{var}", var)
    t = plistlib.loads(open(os.path.join(ROOT, "templates", f"{key}.mobileconfig"), "rb").read())
    validate(t, key, f"template/{key}")
    p = plistlib.loads(g.create_mobileconfig(key))
    validate(p, key, f"python/{key}")
    check(p["PayloadUUID"] != plistlib.loads(g.create_mobileconfig(key))["PayloadUUID"], f"{key}: uuid not fresh")

ids = {(plistlib.loads(g.create_mobileconfig(k, variant=v))["PayloadIdentifier"],
        plistlib.loads(g.create_mobileconfig(k, variant=v))["PayloadContent"][0]["PayloadIdentifier"])
       for k in g.OPERATORS for v in g.VARIANTS}
check(len(ids) == 1, f"identifiers differ between operators/variants: {ids}")

# ارقام فارسی، رمز با فاصله، ورودی عجیب
c = g.validate_custom({"apn": "a", "proxy_host": "h", "proxy_port": "۸۰۸۰", "password": " p "})
check(c["proxy_port"] == 8080 and c["password"] == " p ", f"normalization {c}")
for badport in ("²", "٣x", "0", "65536", "-1", "1.5"):
    try:
        g.validate_custom({"apn": "a", "proxy_host": "h", "proxy_port": badport}); check(False, f"accepted port {badport!r}")
    except ValueError:
        pass
    except Exception as e:
        check(False, f"port {badport!r} raised {type(e).__name__}")

# 2) نام خاص نباید فایل را خراب کند
weird = 'A & B <x> "q"'
check(plistlib.loads(g.create_mobileconfig("mci", weird))["PayloadDisplayName"] == weird, "python escaping")

# 3) خروجی واقعی سایت
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright not installed: web check skipped")
else:
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(accept_downloads=True)
        pg.goto("file://" + os.path.abspath(os.path.join(ROOT, "index.html")))
        opts = pg.eval_on_selector_all("#apn option", "e=>e.map(o=>o.value)")
        check(sorted(opts) == sorted(list(g.OPERATORS) + ["custom"]), f"select options {opts}")
        opts = [o for o in opts if o != "custom"]
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        vopts = pg.eval_on_selector_all("#variant option", "e=>e.map(o=>o.value)")
        check(sorted(vopts) == sorted(g.VARIANTS), f"variant options {vopts}")
        for key, var, name in [(k, v, n) for k in opts for v in vopts for n in ("", weird)]:
            pg.select_option("#apn", key); pg.select_option("#variant", var); pg.fill("#profileName", name)
            with pg.expect_download() as dl:
                pg.click("#submitBtn")
            data = open(dl.value.path(), "rb").read()
            w = plistlib.loads(data)
            validate(w, key, f"web/{key}/{var}", var)
            ref = plistlib.loads(g.create_mobileconfig(key, name, variant=var))
            check(strip(w) == strip(ref), f"web != python for {key}/{var} name={name!r}")
            pg.wait_for_timeout(100)

        # --- APN دلخواه ---
        def download(name="", variant="A"):
            pg.select_option("#variant", variant); pg.fill("#profileName", name)
            with pg.expect_download() as dl:
                pg.click("#submitBtn")
            return plistlib.loads(open(dl.value.path(), "rb").read())

        pg.select_option("#apn", "custom")
        check(pg.is_visible("#customFields"), "custom fields should be visible")
        cases = [
            {"apn": "my apn", "username": "u", "password": "p&<>", "proxy_host": "10.0.0.1", "proxy_port": "8080"},
            {"apn": "internet", "username": "", "password": "", "proxy_host": "", "proxy_port": ""},
            {"apn": "x", "username": "", "password": "", "proxy_host": "proxy.example", "proxy_port": ""},
            {"apn": "p", "username": "u", "password": "  sp ace  ", "proxy_host": "h", "proxy_port": "۸۰۸۰"},
            {"apn": "q", "username": "", "password": "", "proxy_host": "h", "proxy_port": "٣١٢٨"},
        ]
        for cs in cases:
            pg.fill("#customApn", cs["apn"]); pg.fill("#customUser", cs["username"]); pg.fill("#customPass", cs["password"])
            pg.fill("#customProxy", cs["proxy_host"]); pg.fill("#customPort", cs["proxy_port"])
            for var in g.VARIANTS:
                w = download("", var)
                ref = plistlib.loads(g.create_mobileconfig("custom", variant=var, custom=cs))
                check(strip(w) == strip(ref), f"custom web != python {cs} {var}")
        # رمز در پیش‌نمایش خام نباید دیده شود
        pg.fill("#customApn", "a"); pg.fill("#customPass", "SECRET123"); pg.fill("#customUser", ""); pg.fill("#customProxy", ""); pg.fill("#customPort", "")
        check("SECRET123" not in pg.inner_text("#previewRaw"), "password leaked in preview")

        # خطاها: دانلود نباید رخ دهد و پیام باید نشان داده شود
        bad = [("", "", "", "", "err_apn"), ("a", "", "", "5", "err_port_host"),
               ("a", "", "h", "70000", "err_port"), ("a", "", "h", "abc", "err_port")]
        for apn, user, host, port, _ in bad:
            pg.fill("#customApn", apn); pg.fill("#customUser", user); pg.fill("#customProxy", host); pg.fill("#customPort", port); pg.fill("#customPass", "")
            pg.click("#submitBtn")
            check(pg.is_visible("#errorMsg"), f"no error shown for {(apn[:5], host, port)}")
            try:
                g.validate_custom({"apn": apn, "username": user, "proxy_host": host, "proxy_port": port}); check(False, f"python accepted {(apn[:5], host, port)}")
            except ValueError:
                pass

        # طول بیش از ۱۰۰ را maxlength فیلد HTML جلوی کاربر می‌گیرد؛ پایتون هم باید رد کند
        try:
            g.validate_custom({"apn": "x" * 101}); check(False, "python accepted 101 chars")
        except ValueError:
            pass

        # XSS: مقدارهای دلخواه نباید به‌عنوان HTML اجرا شوند
        evil = '<img src=x onerror="window.__x=1">'
        pg.fill("#customApn", evil); pg.fill("#customUser", ""); pg.fill("#customProxy", ""); pg.fill("#customPort", "")
        pg.wait_for_timeout(100)
        check(pg.evaluate("window.__x") is None and pg.locator("#previewTable img").count() == 0, "XSS in preview")
        check(download()["PayloadContent"][0]["APNs"][0]["Name"] == evil, "evil apn not preserved")

        # --- عیب‌یابی ---
        pg.select_option("#apn", "mci")
        check(not pg.is_visible("#customFields"), "custom fields should hide")
        pg.evaluate("document.getElementById('helpBox').open = true")
        pg.select_option("#symptom", "sos")
        check(pg.is_visible("#helpApply") and pg.locator("#helpSteps li").count() >= 3, "help steps")
        pg.click("#helpApply")
        check(pg.input_value("#variant") == "B", "help apply variant")
        pg.select_option("#symptom", "inst")
        check(not pg.is_visible("#helpApply"), "inst has no variant button")

        # --- زبان و حافظه ---
        pg.click("#langBtn")
        check(pg.evaluate("document.documentElement.dir") == "ltr" and "Build" in pg.inner_text("#submitBtn"), "english")
        pg.reload()
        check(pg.evaluate("document.documentElement.dir") == "ltr", "language not remembered")
        check(pg.input_value("#variant") == "B", "variant not remembered")
        pg.click("#langBtn")
        check(pg.evaluate("document.documentElement.dir") == "rtl", "back to persian")
        check(not errors, f"page errors: {errors}")
        b.close()

print("\nALL OK" if not fails else f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
