# 😈 شیطون انتن | Sheitoon Antenna

**بازگردانی آنتن آیفون‌های رجیسترنشده سری ۱۴، ۱۵، ۱۶ و بالاتر**

پروژه رایگان و متن‌باز برای ساخت پروفایل `.mobileconfig` با **UUID یکتا** جهت جلوگیری از بسته شدن.

> ⚠️ این پروژه جایگزین رجیستری رسمی نیست و صرفاً یک راه‌حل موقت فنی است.

---

## 🔗 لینک‌ها

- **گیت‌هاب:** [https://github.com/6itoon/6itoon-antenna](https://github.com/6itoon/6itoon-antenna)
- **سایت (GitHub Pages):** بعد از فعال‌سازی Pages، آدرس شما اینجا قرار می‌گیرد

---

## 🚀 روش سریع (پیشنهادی)

### استفاده از وب‌سایت (بدون نیاز به نصب)

1. فایل `index.html` را در GitHub Pages فعال کنید.
2. با مرورگر **Safari** روی خود آیفون باز کنید.
3. اپراتور را انتخاب کنید و روی **ساخت پروفایل** بزنید.
4. فایل را نصب کنید.

---

## 📁 ساختار پروژه

```
sheitoon-antenna/
├── index.html                 # ژنراتور وب (اصلی)
├── README.md
├── scripts/
│   ├── uuid_generator.py      # ساخت UUID یکتا
│   └── generate_profile.py    # ساخت کامل فایل mobileconfig با پایتون
├── templates/
│   ├── mci.mobileconfig
│   ├── irancell.mobileconfig
│   └── rightel.mobileconfig
└── docs/
    └── install-guide.md
```

---

## 📱 مراحل نصب پروفایل روی آیفون

1. **ریست شبکه**  
   `Settings → General → Transfer or Reset iPhone → Reset → Reset Network Settings`

2. فایل `.mobileconfig` را دانلود و در **Files** ذخیره کنید.

3. روی فایل بزنید تا پیام نصب ظاهر شود.

4. برو به:  
   `Settings → Profile Downloaded` (یا `VPN & Device Management`) → **Install**

5. بعد از نصب:
   - Data Roaming را روشن کنید
   - Voice & Data را روی **5G** یا **LTE** بگذارید
   - VoLTE را فعال کنید
   - یک‌بار حالت هواپیما را روشن/خاموش کنید یا گوشی را ری‌استارت کنید

6. **حذف پروفایل قبلی** قبل از نصب پروفایل جدید الزامی است.

---

## 🛠 روش پایتون (برای ساخت تعداد زیاد)

```bash
python scripts/uuid_generator.py
python scripts/generate_profile.py
```

---

## 📌 نکات مهم

- هر بار از **UUID جدید** استفاده کنید (سایت و اسکریپت خودکار می‌سازند).
- ترجیحاً فقط یک سیم‌کارت داخل گوشی باشد.
- روی شبکه همراه اول معمولاً نتیجه بهتری می‌دهد.
- اگر اینترنت نداشت، IPv6 را امتحان کنید.
- پروفایل‌های قدیمی را قبل از نصب جدید حذف کنید.

---

## 📋 اپراتورهای پشتیبانی‌شده

| اپراتور       | APN            |
|---------------|----------------|
| همراه اول     | mcinet         |
| ایرانسل       | mtnirancell    |
| رایتل         | RighTel        |
| آپتل          | ApTel          |
| سامانتل       | samantel       |
| شاتل موبایل   | shatelmobile   |

---

## 📄 لایسنس

این پروژه رایگان و متن‌باز است. استفاده شخصی و تجاری مجاز است.

---

**ساخته‌شده توسط شیطون**  
گیت‌هاب: [6itoon/6itoon-antenna](https://github.com/6itoon/6itoon-antenna)
