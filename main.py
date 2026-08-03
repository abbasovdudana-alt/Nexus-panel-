import asyncio
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

from datetime import datetime, timedelta
import telebot
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
    
TOKEN = "8985105386:AAF2M1A0vcy-Z_kqCs4smKMkYyLOx38YkNs"
bot = telebot.TeleBot(TOKEN)

user_data = {}
VERSION_SIGNATURE = "\n\n━━━━━━━━━━━━━━━━━━\n⚙️ Versiya: v1"
PLUGIN_CHANNEL_LINK = "https://t.me/nexususerbotplugin"

ACTIVE_LICENSES = {
    "NEXUS-PRO-1MONTH-777": 30,
    "TEST-KEY-1": 1,
    "NEXUS-ONE-DAY-999": 1
}

def run_async(coro):
    """Asinxron funksiyaları sinxron mühitdə işlətmək üçün köməkçi funksiya."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    text = (
        f"Salam, {user_name}! Xoş gəlmisiniz. 🚀\n\n"
        "Bu professional sistem vasitəsilə öz Telegram userbotunuzu tam avtomatik və təhlükəsiz şəkildə quraşdıra bilərsiniz.\n\n"
        "✨ Üstünlüklərimiz:\n"
        "• Sürətli və etibarlı qoşulma\n"
        "• Peşəkar idarəetmə interfeysi\n"
        "• 7/7 avtomatlaşdırılmış dəstək\n\n"
        "Başlamaq üçün aşağıdakı əmri seçin:\n"
        "👉 /setup - Qurulumu Başlat"
        f"{VERSION_SIGNATURE}"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['setup'])
def start_setup(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'step': 'waiting_license'}
    
    text = (
        "🔐 Lisenziya Təsdiqi\n\n"
        "Botdan istifadə etmək üçün admin @Samirdideee -dən əldə etdiyiniz lisenziya kodunu daxil edin:"
        f"{VERSION_SIGNATURE}"
    )
    bot.send_message(chat_id, text)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def process_setup(message):
    chat_id = message.chat.id
    step = user_data[chat_id].get('step')
    text_input = message.text.strip()
    
    if step == 'waiting_license':
        if text_input in ACTIVE_LICENSES:
            days = ACTIVE_LICENSES[text_input]
            now = datetime.now()
            expire_date = now + timedelta(days=days)
            
            start_str = now.strftime("%d.%m.%Y - %H:%M")
            expire_str = expire_date.strftime("%d.%m.%Y - %H:%M")
            
            del ACTIVE_LICENSES[text_input]
            
            user_data[chat_id]['license'] = text_input
            user_data[chat_id]['expire_date'] = expire_date
            user_data[chat_id]['step'] = 'waiting_api_id'
            
            bot.send_message(
                chat_id,
                "✅ Lisenziya uğurla təsdiqləndi və aktivləşdirildi!\n\n"
                f"🕒 Aktivləşmə saatı: {start_str}\n"
                f"📅 Bitmə saatı: {expire_str} ({days} günlük)\n\n"
                "⚙️ Userbot Qurulum Paneli\n\n"
                "1️⃣ Zəhmət olmasa, my.telegram.org saytından əldə etdiyiniz API_ID rəqəmini daxil edin:\n"
                "(Məsələn: 36376916)"
                f"{VERSION_SIGNATURE}"
            )
        else:
            bot.send_message(
                chat_id,
                "❌ Yanlış, artıq istifadə olunmuş və ya vaxtı bitmiş lisenziya kodu!\n\n"
                "Zəhmət olmasa admin @Samirdideee ilə əlaqə saxlayıb yeni kod əldə edin."
                f"{VERSION_SIGNATURE}"
            )
            
    elif step == 'waiting_api_id':
        if datetime.now() > user_data[chat_id]['expire_date']:
            bot.send_message(chat_id, f"❌ Təəssüf ki, lisenziya vaxtınız bitmişdir!{VERSION_SIGNATURE}")
            del user_data[chat_id]
            return
            
        user_data[chat_id]['api_id'] = text_input
        user_data[chat_id]['step'] = 'waiting_api_hash'
        bot.send_message(
            chat_id, 
            "✅ API_ID uğurla qəbul edildi!\n\n"
            "2️⃣ İndi isə həmin paneldən əldə etdiyiniz API_HASH kodunu göndərin:"
            f"{VERSION_SIGNATURE}"
        )
        
    elif step == 'waiting_api_hash':
        if datetime.now() > user_data[chat_id]['expire_date']:
            bot.send_message(chat_id, f"❌ Təəssüf ki, lisenziya vaxtınız bitmişdir!{VERSION_SIGNATURE}")
            del user_data[chat_id]
            return
            
        user_data[chat_id]['api_hash'] = text_input
        user_data[chat_id]['step'] = 'waiting_phone'
        bot.send_message(
            chat_id, 
            "✅ API_HASH uğurla qəbul edildi!\n\n"
            "3️⃣ İndi isə userbotu qoşmaq istədiyiniz telefon nömrəsini beynəlxalq formatda daxil edin (məsələn: +994501234567):"
            f"{VERSION_SIGNATURE}"
        )
        
    elif step == 'waiting_phone':
        if datetime.now() > user_data[chat_id]['expire_date']:
            bot.send_message(chat_id, f"❌ Təəssüf ki, lisenziya vaxtınız bitmişdir!{VERSION_SIGNATURE}")
            del user_data[chat_id]
            return
            
        user_data[chat_id]['phone'] = text_input
        user_data[chat_id]['step'] = 'waiting_code'
        
        bot.send_message(chat_id, f"🔄 Telegram-a qoşulma sorğusu göndərilir və kod gözlənilir...{VERSION_SIGNATURE}")
        
        try:
            api_id = int(user_data[chat_id]['api_id'])
            api_hash = user_data[chat_id]['api_hash']
            phone = user_data[chat_id]['phone']
            
            app = Client(name=f"session_{chat_id}", api_id=api_id, api_hash=api_hash, in_memory=True)
            user_data[chat_id]['app'] = app
            
            run_async(app.connect())
            sent_code = run_async(app.send_code(phone))
            user_data[chat_id]['phone_code_hash'] = sent_code.phone_code_hash
            
            bot.send_message(
                chat_id,
                "✅ Təsdiq kodu nömrənizə göndərildi!\n\n"
                "Zəhmət olmasa Telegram-dan gələn kodu bura yazın (məsələn: 12345):"
                f"{VERSION_SIGNATURE}"
            )
        except Exception as e:
            bot.send_message(chat_id, f"❌ Xəta baş verdi: {e}{VERSION_SIGNATURE}")
            del user_data[chat_id]

    elif step == 'waiting_code':
        code = text_input
        app = user_data[chat_id]['app']
        phone = user_data[chat_id]['phone']
        phone_code_hash = user_data[chat_id]['phone_code_hash']
        
        try:
            run_async(app.sign_in(phone, phone_code_hash, code))
            session_string = run_async(app.export_session_string())
            run_async(app.disconnect())
            
            bot.send_message(
                chat_id,
                "🎉 Uğurlu giriş!\n\n"
                "Sənin **Session String** açarın aşağıdadır. Bunu kopyalayıb Termux-dakı botuna qura bilərsən:\n\n"
                f"`{session_string}`"
                f"{VERSION_SIGNATURE}"
            )
            del user_data[chat_id]
            
        except SessionPasswordNeeded:
            user_data[chat_id]['step'] = 'waiting_password'
            bot.send_message(
                chat_id,
                "🔒 Hesabınızda İki Addımlı Doğrulama (2FA) şifrəsi mövcuddur.\n\n"
                "Zəhmət olmasa hesabınızın şifrəsini daxil edin:"
                f"{VERSION_SIGNATURE}"
            )
        except Exception as e:
            bot.send_message(chat_id, f"❌ Kod səhvdir və ya xəta baş verdi: {e}{VERSION_SIGNATURE}")
            del user_data[chat_id]

    elif step == 'waiting_password':
        password = text_input
        app = user_data[chat_id]['app']
        
        try:
            run_async(app.check_password(password))
            session_string = run_async(app.export_session_string())
            run_async(app.disconnect())
            
            bot.send_message(
                chat_id,
                "🎉 2FA təsdiqi uğurla keçdi!\n\n"
                "Sənin **Session String** açarın aşağıdadır:\n\n"
                f"`{session_string}`"
                f"{VERSION_SIGNATURE}"
            )
            del user_data[chat_id]
            
        except Exception as e:
            bot.send_message(chat_id, f"❌ Şifrə səhvdir və ya xəta baş verdi: {e}{VERSION_SIGNATURE}")
            del user_data[chat_id]

print("Nexus İdarəetmə Paneli işə düşdü...")
bot.infinity_polling()
