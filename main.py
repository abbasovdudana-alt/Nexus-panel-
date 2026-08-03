import telebot
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
from flask import Flask
from threading import Thread
import os

TOKEN = "8985105386:AAF2M1A0vcy-Z_kqCs4smKMkYyLOx38YkNs"
bot = telebot.TeleBot(TOKEN)

# Render-in port gözləntisini qarşılamaq üçün mini Flask serveri
app_web = Flask('')

@app_web.route('/')
def home():
    return "Nexus Panel is Alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

user_data = {}
VERSION_SIGNATURE = "\n\n━━━━━━━━━━━━━━━━━━\n⚙️ Versiya: v1"
PLUGIN_CHANNEL_LINK = "https://t.me/nexususerbotplugin"

ACTIVE_LICENSES = {
    "NEXUS-PRO-1MONTH-777": 30,
    "TEST-KEY-1": 1,
    "NEXUS-ONE-DAY-999": 1
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    text = (
        f"Salam, {user_name}! Xoş gəlmisiniz. 🚀\n\n"
        "Bu professional sistem vasitəsilə öz Telegram userbotunuz üçün təhlükəsiz Session String əldə edə bilərsiniz.\n\n"
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
            
        user_data[chat_id]['api_id'] = int(text_input)
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
            
        phone = text_input
        user_data[chat_id]['phone'] = phone
        
        bot.send_message(
            chat_id, 
            "⏳ Nömrəyə Telegram-dan təsdiq kodu göndərilir, zəhmət olmasa gözləyin..."
            f"{VERSION_SIGNATURE}"
        )
        
        try:
            api_id = user_data[chat_id]['api_id']
            api_hash = user_data[chat_id]['api_hash']
            session_name = f"session_{chat_id}"
            
            async def send_code_async():
                client = Client(session_name, api_id=api_id, api_hash=api_hash, in_memory=True)
                await client.connect()
                sent_code = await client.send_code(phone)
                return client, sent_code.phone_code_hash

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client, phone_code_hash = loop.run_until_complete(send_code_async())
            
            user_data[chat_id]['client'] = client
            user_data[chat_id]['loop'] = loop
            user_data[chat_id]['phone_code_hash'] = phone_code_hash
            user_data[chat_id]['step'] = 'waiting_otp'
            
            bot.send_message(
                chat_id, 
                "📲 Telegram hesabınıza kod göndərildi!\n\n"
                "Zəhmət olmasa gələn təsdiq kodunu (OTP) rəqəmlər arasında boşluq buraxaraq daxil edin (məsələn: 1 2 3 4 5):"
                f"{VERSION_SIGNATURE}"
            )
        except Exception as e:
            bot.send_message(
                chat_id, 
                f"❌ Xəta baş verdi:\n{str(e)}\n\n"
                "Zəhmət olmasa nömrəni düzgün daxil etdiyinizə əmin olun."
                f"{VERSION_SIGNATURE}"
            )
            del user_data[chat_id]
        
    elif step == 'waiting_otp':
        otp_code = text_input.replace(" ", "")
        
        try:
            client = user_data[chat_id]['client']
            loop = user_data[chat_id]['loop']
            phone_code_hash = user_data[chat_id]['phone_code_hash']
            phone = user_data[chat_id]['phone']
            
            async def sign_in_async():
                try:
                    await client.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=otp_code)
                    return "success"
                except SessionPasswordNeeded:
                    return "password_needed"

            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(sign_in_async())
            
            if result == "success":
                async def export_session():
                    return await client.export_session_string()
                
                session_string = loop.run_until_complete(export_session())
                try:
                    loop.run_until_complete(client.disconnect())
                except:
                    pass

                bot.send_message(
                    chat_id, 
                    "✅ Təsdiq kodu uğurla təsdiqləndi!\n\n"
                    "🎉 **Sənin Session String açarın hazırdır!**\n\n"
                    f"`{session_string}`\n\n"
                    "📌 **Termux-da nə etməlisən?**\n"
                    "1. Termux-u aç və userbot qovluğuna daxil ol.\n"
                    "2. Quraşdırma zamanı və ya `.env` / `config.py` faylında bu açarı tələb edən yerə yapışdır.\n"
                    "3. Botunu işə sal və istənilən çata `.alive` yazaraq yoxla!\n\n"
                    f"📂 Plugin və yeniliklər kanalımız: {PLUGIN_CHANNEL_LINK}"
                    f"{VERSION_SIGNATURE}"
                )
                del user_data[chat_id]
            elif result == "password_needed":
                user_data[chat_id]['step'] = 'waiting_password'
                bot.send_message(
                    chat_id,
                    "🔐 Hesabınızda İki Mərhələli Təsdiq (Bulud Şifrəsi) aktivdir.\n\n"
                    "Zəhmət olmasa hesabınızın şifrəsini daxil edin:"
                    f"{VERSION_SIGNATURE}"
                )
        except Exception as e:
            bot.send_message(
                chat_id, 
                f"❌ Kod səhvdir və ya xəta baş verdi:\n{str(e)}"
                f"{VERSION_SIGNATURE}"
            )
            del user_data[chat_id]

    elif step == 'waiting_password':
        password = text_input
        
        try:
            client = user_data[chat_id]['client']
            loop = user_data[chat_id]['loop']
            
            async def check_password_async():
                if not client.is_connected:
                    await client.connect()
                await client.check_password(password)
                return await client.export_session_string()

            asyncio.set_event_loop(loop)
            session_string = loop.run_until_complete(check_password_async())
            try:
                loop.run_until_complete(client.disconnect())
            except:
                pass
            
            bot.send_message(
                chat_id, 
                "✅ Şifrə uğurla təsdiqləndi!\n\n"
                "🎉 **Sənin Session String açarın hazırdır!**\n\n"
                f"`{session_string}`\n\n"
                "📌 **Termux-da nə etməlisən?**\n"
                "1. Termux-u aç və userbot qovluğuna daxil ol.\n"
                "2. Kodu kopyalayıb Termux-dakı tələb olunan yerə yapışdır.\n"
                "3. Userbotunu işə sal!\n\n"
                f"📂 Plugin və yeniliklər kanalımız: {PLUGIN_CHANNEL_LINK}"
                f"{VERSION_SIGNATURE}"
            )
        except Exception as e:
            bot.send_message(
                chat_id, 
                f"❌ Şifrə səhvdir və ya xəta baş verdi:\n{str(e)}"
                f"{VERSION_SIGNATURE}"
            )
            
        del user_data[chat_id]

if __name__ == "__main__":
    # Flask-ı arxa planda işə salırıq ki, Render port tələbini ödəsin
    t = Thread(target=run_web)
    t.start()
    
    print("Nexus Session Generator Paneli işə düşdü...")
    bot.infinity_polling()
