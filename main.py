# -*- coding: utf-8 -*-
"""
main.py
اپلیکیشن «دفترچهٔ رشد» — برنامهٔ توسعهٔ فردی با Kivy
نوشته‌شده برای اجرا روی اندروید (تبلت) با Buildozer.

ویژگی‌ها:
- پروفایل کاربر (نام، سن، وزن فعلی/هدف)
- روودمپ یک‌ساله (زبان، پایتون، ترید، مکانیک، هک و امنیت، ورزش)
- چک‌لیست روزانه (تیک زدن کارها)
- چک‌لیست/اهداف ماهانه
- تایمر (Pomodoro-style countdown)
- یادآوری/نوتیفیکیشن محلی (در زمانی که اپ باز است، از plyer استفاده می‌شود)
- روتین پوستی (صبح/شب)

برای ساخت APK: به فایل buildozer.spec و README.md مراجعه کن.
"""

import json
import os
from datetime import datetime, date

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.metrics import dp

import roadmap

# ---------------------------------------------------------------------------
# تلاش برای بارگذاری یک فونت فارسی (در صورت وجود در پوشه fonts/).
# اگر فونت موجود نباشد، Kivy از فونت پیش‌فرض استفاده می‌کند که ممکن است
# حروف فارسی را به‌خوبی نمایش ندهد. توضیحات کامل در README.md آمده است.
# ---------------------------------------------------------------------------
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Vazirmatn-Regular.ttf")
FONT_NAME = "Vazirmatn"
if os.path.exists(FONT_PATH):
    LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)
else:
    FONT_NAME = "Roboto"  # فونت پیش‌فرض Kivy

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "user_data.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# پیش‌فرض دادهٔ کاربر
# ---------------------------------------------------------------------------
DEFAULT_DATA = {
    "profile": {
        "first_name": "",
        "last_name": "",
        "age": "",
        "weight_current": 110,
        "weight_goal": 85,
        "start_date": date.today().isoformat(),
    },
    "daily_progress": {},     # { "2026-06-20": {"task text": True, ...} }
    "monthly_progress": {},   # { "1": {"پایتون": True, ...} }
    "skincare_progress": {},  # { "2026-06-20": {"صبح": True, "شب": False} }
    "xp": 0,
    "level": 1,
}


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                # تضمین وجود کلیدهای پایه در صورت آپدیت ساختار
                for k, v in DEFAULT_DATA.items():
                    if k not in d:
                        d[k] = v
                return d
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_DATA))  # کپی عمیق


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# تلاش برای وارد کردن plyer برای نوتیفیکیشن (روی دسکتاپ هم کار می‌کند، فقط
# پنجره‌ای متفاوت‌ نشان می‌دهد؛ روی اندروید نوتیف واقعی سیستم می‌فرستد).
# ---------------------------------------------------------------------------
try:
    from plyer import notification as plyer_notification
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False


def send_notification(title, message):
    if HAS_PLYER:
        try:
            plyer_notification.notify(title=title, message=message, timeout=8)
            return
        except Exception:
            pass
    # fallback: فقط چاپ در کنسول (برای دیباگ روی دسکتاپ)
    print(f"[یادآوری] {title}: {message}")


# ---------------------------------------------------------------------------
# KV — رابط کاربری
# ---------------------------------------------------------------------------
KV = """
#:import dp kivy.metrics.dp

<RTLLabel@Label>:
    halign: "right"
    valign: "middle"
    text_size: self.size
    font_name: app.font_name

<RTLButton@Button>:
    font_name: app.font_name
    halign: "center"

<SectionTitle@Label>:
    font_size: "20sp"
    bold: True
    size_hint_y: None
    height: dp(40)
    halign: "right"
    valign: "middle"
    text_size: self.size
    font_name: app.font_name
    color: 0.06, 0.14, 0.1, 1

<TaskRow>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(56)
    padding: dp(8), dp(4)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.94, 0.93, 0.87, 1
        Rectangle:
            pos: self.pos
            size: self.size

    CheckBox:
        id: cb
        size_hint_x: None
        width: dp(40)
        active: root.done
        on_active: root.on_toggle(self, *args)

    Label:
        text: root.task_text
        font_name: app.font_name
        halign: "right"
        valign: "middle"
        text_size: self.size
        color: (0.35,0.45,0.36,1) if root.done else (0.06,0.14,0.1,1)

<NavBar@BoxLayout]>:

ScreenManager:
    transition: SlideTransition()
    id: sm

    HomeScreen:
        name: "home"
    DailyScreen:
        name: "daily"
    MonthlyScreen:
        name: "monthly"
    TimerScreen:
        name: "timer"
    SkincareScreen:
        name: "skincare"
    ProfileScreen:
        name: "profile"
"""

Builder.load_string(KV)


# ---------------------------------------------------------------------------
# ردیف تسک قابل‌استفاده مجدد
# ---------------------------------------------------------------------------
class TaskRow(BoxLayout):
    task_text = StringProperty("")
    done = BooleanProperty(False)

    def __init__(self, task_text="", done=False, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.task_text = task_text
        self.done = done
        self._on_change = on_change

    def on_toggle(self, checkbox, value):
        self.done = value
        if self._on_change:
            self._on_change(self.task_text, value)


# ---------------------------------------------------------------------------
# نوار پایین (ناوبری ساده بین صفحات)
# ---------------------------------------------------------------------------
def build_bottom_nav(sm, current_name):
    nav = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(2))
    buttons = [
        ("خانه", "home"),
        ("روزانه", "daily"),
        ("ماهانه", "monthly"),
        ("تایمر", "timer"),
        ("پوست", "skincare"),
        ("پروفایل", "profile"),
    ]
    for label, name in buttons:
        btn = Button(
            text=label,
            font_name=App.get_running_app().font_name,
            background_color=(0.24, 0.34, 0.26, 1) if name == current_name else (0.06, 0.14, 0.1, 1),
        )
        btn.bind(on_release=lambda inst, n=name: setattr(sm, "current", n))
        nav.add_widget(btn)
    return nav


# ---------------------------------------------------------------------------
# صفحهٔ خانه — سلام و خلاصهٔ امروز
# ---------------------------------------------------------------------------
class HomeScreen(Screen):
    def on_pre_enter(self, *args):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        data = app.data
        profile = data["profile"]
        font = app.font_name

        root = BoxLayout(orientation="vertical")

        today = date.today()
        py_weekday = today.weekday()
        focus = roadmap.get_today_focus(py_weekday)

        name = profile.get("first_name") or "دوست من"
        greeting = f"سلام {name}! 👋"

        header = Label(
            text=greeting,
            font_name=font,
            font_size="26sp",
            bold=True,
            size_hint_y=None,
            height=dp(70),
            halign="center",
            valign="middle",
            color=(0.06, 0.14, 0.1, 1),
        )
        header.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(header)

        date_lbl = Label(
            text=f"امروز {focus['weekday_name']} است — محور امروز: {focus['focus_title']}",
            font_name=font,
            font_size="16sp",
            size_hint_y=None,
            height=dp(50),
            halign="center",
            valign="middle",
            color=(0.24, 0.34, 0.26, 1),
        )
        date_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(date_lbl)

        # خلاصهٔ پیشرفت امروز
        today_str = today.isoformat()
        today_progress = data["daily_progress"].get(today_str, {})
        all_tasks = focus["tasks"]
        done_count = sum(1 for t in all_tasks if today_progress.get(t))
        progress_lbl = Label(
            text=f"پیشرفت امروز: {done_count} از {len(all_tasks)} کار انجام شده",
            font_name=font,
            font_size="15sp",
            size_hint_y=None,
            height=dp(40),
            halign="center",
            valign="middle",
            color=(0.61, 0.49, 0.30, 1),
        )
        progress_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(progress_lbl)

        # سطح/امتیاز
        level_lbl = Label(
            text=f"سطح فعلی: {data.get('level',1)}   |   امتیاز: {data.get('xp',0)}",
            font_name=font,
            font_size="14sp",
            size_hint_y=None,
            height=dp(34),
            halign="center",
            valign="middle",
            color=(0.61, 0.49, 0.30, 1),
        )
        level_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(level_lbl)

        # دکمهٔ رفتن به برنامهٔ روزانه
        go_btn = Button(
            text="مشاهدهٔ برنامهٔ امروز",
            font_name=font,
            size_hint_y=None,
            height=dp(54),
            background_color=(0.24, 0.34, 0.26, 1),
        )
        go_btn.bind(on_release=lambda inst: setattr(self.manager, "current", "daily"))
        root.add_widget(go_btn)

        spacer = BoxLayout()
        root.add_widget(spacer)

        root.add_widget(build_bottom_nav(self.manager, "home"))
        self.add_widget(root)


# ---------------------------------------------------------------------------
# صفحهٔ روزانه — چک‌لیست روزانه بر اساس روودمپ
# ---------------------------------------------------------------------------
class DailyScreen(Screen):
    def on_pre_enter(self, *args):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        font = app.font_name
        data = app.data

        today = date.today()
        today_str = today.isoformat()
        focus = roadmap.get_today_focus(today.weekday())

        root = BoxLayout(orientation="vertical")

        title = Label(
            text=f"برنامهٔ امروز ({focus['weekday_name']}) — {focus['focus_title']}",
            font_name=font,
            font_size="19sp",
            bold=True,
            size_hint_y=None,
            height=dp(60),
            halign="center",
            valign="middle",
            color=(0.06, 0.14, 0.1, 1),
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(title)

        scroll = ScrollView()
        task_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        task_list.bind(minimum_height=task_list.setter("height"))

        if today_str not in data["daily_progress"]:
            data["daily_progress"][today_str] = {}

        def on_task_change(task_text, value):
            data["daily_progress"][today_str][task_text] = value
            if value:
                app.add_xp(10)
            else:
                app.add_xp(-10)
            save_data(data)

        for task in focus["tasks"]:
            done = data["daily_progress"][today_str].get(task, False)
            row = TaskRow(task_text=task, done=done, on_change=on_task_change)
            task_list.add_widget(row)

        scroll.add_widget(task_list)
        root.add_widget(scroll)
        root.add_widget(build_bottom_nav(self.manager, "daily"))
        self.add_widget(root)


# ---------------------------------------------------------------------------
# صفحهٔ ماهانه — اهداف ماهانه از روودمپ
# ---------------------------------------------------------------------------
class MonthlyScreen(Screen):
    def on_pre_enter(self, *args):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        font = app.font_name
        data = app.data

        profile = data["profile"]
        start_date = date.fromisoformat(profile.get("start_date", date.today().isoformat()))
        today = date.today()
        months_passed = (today.year - start_date.year) * 12 + (today.month - start_date.month) + 1
        current_month = max(1, min(12, months_passed))

        month_data = roadmap.get_month_goals(current_month)
        month_key = str(current_month)

        root = BoxLayout(orientation="vertical")

        title = Label(
            text=f"ماه {current_month} از ۱۲ — {month_data['title']}",
            font_name=font,
            font_size="19sp",
            bold=True,
            size_hint_y=None,
            height=dp(60),
            halign="center",
            valign="middle",
            color=(0.06, 0.14, 0.1, 1),
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(title)

        scroll = ScrollView()
        goal_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        goal_list.bind(minimum_height=goal_list.setter("height"))

        if month_key not in data["monthly_progress"]:
            data["monthly_progress"][month_key] = {}

        def on_goal_change(goal_text, value):
            data["monthly_progress"][month_key][goal_text] = value
            if value:
                app.add_xp(50)
            else:
                app.add_xp(-50)
            save_data(data)

        for skill, goal_text in month_data["goals"].items():
            full_text = f"[{skill}] {goal_text}"
            done = data["monthly_progress"][month_key].get(full_text, False)
            row = TaskRow(task_text=full_text, done=done, on_change=on_goal_change)
            row.height = dp(76)
            goal_list.add_widget(row)

        scroll.add_widget(goal_list)
        root.add_widget(scroll)
        root.add_widget(build_bottom_nav(self.manager, "monthly"))
        self.add_widget(root)


# ---------------------------------------------------------------------------
# صفحهٔ تایمر — تایمر شمارش‌معکوس ساده (Pomodoro-style)
# ---------------------------------------------------------------------------
class TimerScreen(Screen):
    remaining = NumericProperty(0)
    running = BooleanProperty(False)
    label_text = StringProperty("۲۵:۰۰")

    def on_pre_enter(self, *args):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        font = app.font_name

        self._event = None
        if not hasattr(self, "remaining") or self.remaining == 0:
            self.remaining = 25 * 60

        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(16))

        title = Label(
            text="تایمر تمرکز",
            font_name=font,
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            height=dp(50),
        )
        root.add_widget(title)

        self.time_label = Label(
            text=self._format_time(self.remaining),
            font_name=font,
            font_size="56sp",
            size_hint_y=None,
            height=dp(120),
            color=(0.06, 0.14, 0.1, 1),
        )
        root.add_widget(self.time_label)

        preset_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        for minutes in (5, 15, 25, 45, 60):
            b = Button(text=f"{minutes} دقیقه", font_name=font)
            b.bind(on_release=lambda inst, m=minutes: self.set_minutes(m))
            preset_row.add_widget(b)
        root.add_widget(preset_row)

        control_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10))
        start_btn = Button(text="شروع", font_name=font, background_color=(0.24, 0.34, 0.26, 1))
        start_btn.bind(on_release=lambda inst: self.start_timer())
        pause_btn = Button(text="توقف موقت", font_name=font)
        pause_btn.bind(on_release=lambda inst: self.pause_timer())
        reset_btn = Button(text="ریست", font_name=font, background_color=(0.69, 0.27, 0.24, 1))
        reset_btn.bind(on_release=lambda inst: self.reset_timer())
        control_row.add_widget(start_btn)
        control_row.add_widget(pause_btn)
        control_row.add_widget(reset_btn)
        root.add_widget(control_row)

        root.add_widget(BoxLayout())
        root.add_widget(build_bottom_nav(self.manager, "timer"))
        self.add_widget(root)

    def _format_time(self, total_seconds):
        m, s = divmod(max(0, int(total_seconds)), 60)
        fa = ['۰','۱','۲','۳','۴','۵','۶','۷','۸','۹']
        def to_fa(n):
            return "".join(fa[int(c)] for c in str(n))
        return f"{to_fa(f'{m:02d}')}:{to_fa(f'{s:02d}')}"

    def set_minutes(self, minutes):
        self.pause_timer()
        self.remaining = minutes * 60
        self.time_label.text = self._format_time(self.remaining)

    def start_timer(self):
        if self.running:
            return
        self.running = True
        self._event = Clock.schedule_interval(self._tick, 1)

    def pause_timer(self):
        self.running = False
        if self._event:
            self._event.cancel()
            self._event = None

    def reset_timer(self):
        self.pause_timer()
        self.remaining = 25 * 60
        self.time_label.text = self._format_time(self.remaining)

    def _tick(self, dt):
        self.remaining -= 1
        self.time_label.text = self._format_time(self.remaining)
        if self.remaining <= 0:
            self.pause_timer()
            send_notification("تایمر تمام شد", "وقت استراحت یا رفتن سراغ کار بعدی است.")


# ---------------------------------------------------------------------------
# صفحهٔ پوست — روتین پوستی صبح و شب
# ---------------------------------------------------------------------------
class SkincareScreen(Screen):
    def on_pre_enter(self, *args):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        font = app.font_name
        data = app.data

        today_str = date.today().isoformat()
        if today_str not in data["skincare_progress"]:
            data["skincare_progress"][today_str] = {}

        root = BoxLayout(orientation="vertical")

        title = Label(
            text="روتین پوستی امروز",
            font_name=font,
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            height=dp(60),
            halign="center",
            valign="middle",
            color=(0.06, 0.14, 0.1, 1),
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(title)

        scroll = ScrollView()
        container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=dp(10))
        container.bind(minimum_height=container.setter("height"))

        for period, steps in roadmap.SKINCARE_ROUTINE.items():
            section_title = Label(
                text=f"روتین {period}",
                font_name=font,
                font_size="17sp",
                bold=True,
                size_hint_y=None,
                height=dp(40),
                halign="right",
                valign="middle",
                color=(0.24, 0.34, 0.26, 1),
            )
            section_title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            container.add_widget(section_title)

            def make_on_change(period_name):
                def on_change(task_text, value):
                    key = f"{period_name}::{task_text}"
                    data["skincare_progress"][today_str][key] = value
                    save_data(data)
                return on_change

            for step in steps:
                key = f"{period}::{step}"
                done = data["skincare_progress"][today_str].get(key, False)
                row = TaskRow(task_text=step, done=done, on_change=make_on_change(period))
                container.add_widget(row)

        scroll.add_widget(container)
        root.add_widget(scroll)
        root.add_widget(build_bottom_nav(self.manager, "skincare"))
        self.add_widget(root)


# ---------------------------------------------------------------------------
# صفحهٔ پروفایل
# ---------------------------------------------------------------------------
class ProfileScreen(Screen):
    def on_pre_enter(self, *args):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        from kivy.uix.textinput import TextInput

        app = App.get_running_app()
        font = app.font_name
        data = app.data
        profile = data["profile"]

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        title = Label(
            text="پروفایل من",
            font_name=font,
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            height=dp(50),
        )
        root.add_widget(title)

        def field(label_text, value, on_text):
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            lbl = Label(text=label_text, font_name=font, size_hint_x=0.4, halign="right", valign="middle")
            lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            ti = TextInput(text=str(value), multiline=False, font_name=font, halign="right")
            ti.bind(text=lambda inst, val: on_text(val))
            row.add_widget(ti)
            row.add_widget(lbl)
            return row

        def set_first_name(v): profile["first_name"] = v
        def set_last_name(v): profile["last_name"] = v
        def set_age(v): profile["age"] = v
        def set_weight_current(v):
            try: profile["weight_current"] = float(v)
            except ValueError: pass
        def set_weight_goal(v):
            try: profile["weight_goal"] = float(v)
            except ValueError: pass

        root.add_widget(field("نام", profile.get("first_name",""), set_first_name))
        root.add_widget(field("نام خانوادگی", profile.get("last_name",""), set_last_name))
        root.add_widget(field("سن", profile.get("age",""), set_age))
        root.add_widget(field("وزن فعلی (کیلوگرم)", profile.get("weight_current",110), set_weight_current))
        root.add_widget(field("وزن هدف (کیلوگرم)", profile.get("weight_goal",85), set_weight_goal))

        start_date = profile.get("start_date", date.today().isoformat())
        info_lbl = Label(
            text=f"تاریخ شروع روودمپ: {start_date}",
            font_name=font,
            size_hint_y=None,
            height=dp(40),
            halign="right",
            valign="middle",
            color=(0.61,0.49,0.30,1),
        )
        info_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        root.add_widget(info_lbl)

        save_btn = Button(
            text="ذخیره",
            font_name=font,
            size_hint_y=None,
            height=dp(54),
            background_color=(0.24, 0.34, 0.26, 1),
        )

        def do_save(inst):
            save_data(data)
            popup = Popup(
                title="ذخیره شد",
                content=Label(text="مشخصات با موفقیت ذخیره شد.", font_name=font),
                size_hint=(0.7, 0.3),
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)

        save_btn.bind(on_release=do_save)
        root.add_widget(save_btn)

        root.add_widget(BoxLayout())
        root.add_widget(build_bottom_nav(self.manager, "profile"))
        self.add_widget(root)


# ---------------------------------------------------------------------------
# اپلیکیشن اصلی
# ---------------------------------------------------------------------------
class GrowthApp(App):
    font_name = StringProperty(FONT_NAME)

    def build(self):
        self.title = "دفترچهٔ رشد"
        self.data = load_data()
        Window.clearcolor = (0.97, 0.96, 0.93, 1)
        root = Builder.load_string(KV)
        # یادآوری روزانه ساده: هر ۳ ساعت یک‌بار یادآوری بفرست در صورت باز بودن اپ
        Clock.schedule_interval(self._periodic_reminder, 60 * 60 * 3)
        return root

    def _periodic_reminder(self, dt):
        send_notification("یادآوری دفترچهٔ رشد", "وقتشه سر بزنی به برنامهٔ امروزت 💪")

    def add_xp(self, amount):
        self.data["xp"] = max(0, self.data.get("xp", 0) + amount)
        needed = self.data.get("level", 1) * 100
        while self.data["xp"] >= needed:
            self.data["xp"] -= needed
            self.data["level"] = self.data.get("level", 1) + 1
            needed = self.data["level"] * 100
        save_data(self.data)

    def on_stop(self):
        save_data(self.data)


if __name__ == "__main__":
    GrowthApp().run()
