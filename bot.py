import telebot
from telebot import types
from datetime import datetime, timedelta
import json
import os
import time
import threading

TOKEN = "8344475065:AAGLpHwOEibVlcuT_k2N1Hd97ZWDF6QzA7c"

bot = telebot.TeleBot(TOKEN)

FILE = "users.json"

# Ma'lumotlarni saqlash
if os.path.exists(FILE):
    with open(FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}


def save():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# 🇺🇿 O'zbekiston bayramlari
HOLIDAYS = {
    "01.01": "🎄 Yangi yil muborak!",
    "08.03": "🌷 Xotin-qizlar kuni muborak!",
    "21.03": "🌸 Navro'z bayrami muborak!",
    "09.05": "🇺🇿 Xotira va qadrlash kuni muborak!",
    "01.09": "🇺🇿 Mustaqillik kuni muborak!",
    "01.10": "📚 O'qituvchi va murabbiylar kuni muborak!",
    "08.12": "⚖️ Konstitutsiya kuni muborak!"
}


def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        "📅 Bugungi sana",
        "🇺🇿 Bayramlar"
    )

    kb.row(
        "🎯 Maxsus kun",
        "📋 Mening sanalarim"
    )

    return kb


@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.chat.id)

    if user_id not in users:
        users[user_id] = {
            "dates": []
        }
        save()

    bot.send_message(
        message.chat.id,
        "👋 Salom!\n\n"
        "Men sana va bayramlar botiman 🤖\n\n"
        "Har kuni soat 00:00 da bugungi sanani "
        "avtomatik yuboraman.",
        reply_markup=menu()
    )


# 📅 Bugungi sana
@bot.message_handler(func=lambda m: m.text == "📅 Bugungi sana")
def today(message):
    now = datetime.now()

    bot.send_message(
        message.chat.id,
        f"📅 Bugungi sana: {now.strftime('%d.%m.%Y')}"
    )


# 🇺🇿 Bayramlar
@bot.message_handler(func=lambda m: m.text == "🇺🇿 Bayramlar")
def holidays(message):
    text = "🇺🇿 O'zbekiston bayramlari:\n\n"

    for date, name in HOLIDAYS.items():
        text += f"📅 {date} — {name}\n"

    bot.send_message(message.chat.id, text)


# 🎯 Maxsus kun
@bot.message_handler(func=lambda m: m.text == "🎯 Maxsus kun")
def special_day(message):
    msg = bot.send_message(
        message.chat.id,
        "📅 Maxsus kun sanasini yozing.\n\n"
        "Masalan:\n"
        "25.12.2026"
    )

    bot.register_next_step_handler(msg, get_date)


def get_date(message):
    try:
        date_obj = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        )

        if date_obj.date() < datetime.now().date():
            bot.send_message(
                message.chat.id,
                "❌ Bu sana o'tib ketgan."
            )
            return

        msg = bot.send_message(
            message.chat.id,
            "📝 Endi bu kunning nomini yozing.\n\n"
            "Masalan: Tug'ilgan kunim"
        )

        bot.register_next_step_handler(
            msg,
            save_special_day,
            message.text.strip()
        )

    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Sana noto'g'ri.\n\n"
            "Masalan:\n"
            "25.12.2026"
        )


def save_special_day(message, date_text):
    user_id = str(message.chat.id)
    name = message.text.strip()

    if user_id not in users:
        users[user_id] = {"dates": []}

    users[user_id]["dates"].append({
        "date": date_text,
        "name": name,
        "sent": False
    })

    save()

    bot.send_message(
        message.chat.id,
        f"✅ Maxsus kun saqlandi!\n\n"
        f"🎯 {name}\n"
        f"📅 {date_text}",
        reply_markup=menu()
    )


# 📋 Mening sanalarim
@bot.message_handler(func=lambda m: m.text == "📋 Mening sanalarim")
def my_dates(message):
    user_id = str(message.chat.id)

    if user_id not in users or not users[user_id]["dates"]:
        bot.send_message(
            message.chat.id,
            "📭 Sizda hali maxsus sana yo'q."
        )
        return

    text = "📋 Sizning maxsus kunlaringiz:\n\n"

    today = datetime.now().date()
  for item in users[user_id]["dates"]:

        d = datetime.strptime(
            item["date"],
            "%d.%m.%Y"
        ).date()

        days = (d - today).days

        if days > 0:
            status = f"⏳ {days} kun qoldi"
        elif days == 0:
            status = "🎉 BUGUN!"
        else:
            status = "✅ O'tib ketgan"

        text += (
            f"🎯 {item['name']}\n"
            f"📅 {item['date']}\n"
            f"{status}\n\n"
        )

    bot.send_message(message.chat.id, text)


# 🌙 Har kuni 00:00 da xabar yuborish
def midnight_checker():

    last_sent_date = None

    while True:

        try:
            now = datetime.now()

            current_date = now.strftime("%d.%m.%Y")

            # Soat 00:00-00:00:59 oralig'ida
            if now.hour == 0 and now.minute == 0:

                if last_sent_date != current_date:

                    for user_id in users:

                        try:

                            message = (
                                "🌙 Yangi kun boshlandi!\n\n"
                                f"📅 Bugun: {current_date}"
                            )

                            # Bayramni tekshirish
                            key = now.strftime("%d.%m")

                            if key in HOLIDAYS:
                                message += (
                                    "\n\n🇺🇿 "
                                    + HOLIDAYS[key]
                                )

                            bot.send_message(
                                int(user_id),
                                message
                            )

                        except Exception as e:
                            print(
                                "Xabar yuborishda xato:",
                                e
                            )

                    last_sent_date = current_date

            time.sleep(20)

        except Exception as e:
            print("Midnight xatosi:", e)
            time.sleep(20)


# 🎯 Maxsus kunlarni tekshirish
def special_checker():

    while True:

        try:

            today = datetime.now().strftime(
                "%d.%m.%Y"
            )

            changed = False

            for user_id in users:

                for item in users[user_id]["dates"]:

                    if (
                        item["date"] == today
                        and not item["sent"]
                    ):

                        bot.send_message(
                            int(user_id),
                            "🎉 BUGUN MAXSUS KUN!\n\n"
                            f"🎯 {item['name']}\n"
                            f"📅 {item['date']}"
                        )

                        item["sent"] = True
                        changed = True

            if changed:
                save()

            time.sleep(30)

        except Exception as e:
            print(
                "Maxsus sana xatosi:",
                e
            )

            time.sleep(30)


# Avtomatik tizimlarni ishga tushirish
threading.Thread(
    target=midnight_checker,
    daemon=True
).start()

threading.Thread(
    target=special_checker,
    daemon=True
).start()


print("🤖 BOT ISHLADI!")
print("🌙 00:00 avtomatik sana xabari yoqilgan.")
print("🎯 Maxsus kun tizimi yoqilgan.")

bot.infinity_polling()
