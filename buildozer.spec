[app]

# نام اپلیکیشن (انگلیسی بنویس، مشکلی با حروف فارسی در این فایل وجود دارد)
title = Growth Journal
package.name = growthjournal
package.domain = org.myapps

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json

version = 1.0

# کتابخانه‌های لازم
requirements = python3,kivy==2.3.0,plyer

# آیکون و splash اختیاری (اگر فایل داری، مسیرش رو اینجا بگذار)
# icon.filename = %(source.dir)s/data/icon.png
# presplash.filename = %(source.dir)s/data/presplash.png

orientation = portrait
fullscreen = 0

# مجوزهای اندروید
android.permissions = INTERNET,VIBRATE,WAKE_LOCK,POST_NOTIFICATIONS

# نسخهٔ API اندروید (قابل تنظیم، این مقادیر برای دستگاه‌های جدید مناسب است)
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

# اجازهٔ نوشتن روی حافظهٔ داخلی برای ذخیرهٔ user_data.json
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
