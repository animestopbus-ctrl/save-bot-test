# Copyright (c) 2025 LastPerson07 : https://github.com/LastPerson07.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
import logging
import os
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    BadRequest,
    MessageNotModified
)
from pyrogram import enums
from LastPerson07.config import API_ID, API_HASH
from LastPerson07.shared_client import app as bot
from LastPerson07.utils.func import save_user_session, get_user_data, remove_user_session, save_user_bot, remove_user_bot
from LastPerson07.utils.encrypt import ecs, dcs
from LastPerson07.plugins.batch import UB, UC
from LastPerson07.utils.custom_filters import login_in_progress, set_user_step, get_user_step

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOGIN_STATE = {}
cancel_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("❌ Cancel")]],
    resize_keyboard=True
)
remove_keyboard = ReplyKeyboardRemove()

PROGRESS_STEPS = {
    "WAITING_PHONE": "🟢 Phone Number → 🔵 Code → 🔵 Password",
    "WAITING_CODE": "✅ Phone Number → 🟢 Code → 🔵 Password",
    "WAITING_PASSWORD": "✅ Phone Number → ✅ Code → 🟢 Password"
}

LOADING_FRAMES = [
    "🔄 Connecting •••",
    "🔄 Connecting ••○",
    "🔄 Connecting •○○",
    "🔄 Connecting ○○○",
    "🔄 Connecting ○○•",
    "🔄 Connecting ○••",
    "🔄 Connecting •••"
]

async def animate_loading(message: Message, duration: int = 5):
    for _ in range(duration):
        for frame in LOADING_FRAMES:
            try:
                await message.edit_text(f"<b>{frame}</b>", parse_mode=enums.ParseMode.HTML)
                await asyncio.sleep(0.5)
            except:
                return

@bot.on_message(filters.private & filters.command("login"))
async def login_start(client: Client, message: Message):
    user_id = message.from_user.id
   
    user_data = await get_user_data(user_id)
    if user_data and "session_string" in user_data:
        return await message.reply(
            "<b>✅ You're already logged in! 🎉</b>\n\n"
            "To switch accounts, first use /logout.",
            parse_mode=enums.ParseMode.HTML
        )
   
    LOGIN_STATE[user_id] = {"step": "WAITING_PHONE", "data": {}}
   
    progress = PROGRESS_STEPS["WAITING_PHONE"]
    await message.reply(
        f"<b>👋 Hey! Let's log you in smoothly 🌟</b>\n\n"
        f"<i>Progress: {progress}</i>\n\n"
        "📞 Please send your <b>Telegram Phone Number</b> with country code.\n\n"
        "<blockquote>Example: +919876543210</blockquote>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=cancel_keyboard
    )

@bot.on_message(filters.private & filters.text & filters.regex("❌ Cancel"))
async def cancel_login(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in LOGIN_STATE:
        data = LOGIN_STATE.pop(user_id, None)
        if "client" in data.get("data", {}):
            await data["data"]["client"].disconnect()
        await message.reply(
            "<b>❌ Login cancelled! 😔</b>\n\n"
            "You can start again with /login anytime.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )
    else:
        await message.reply(
            "<b>❌ No active login to cancel! 🤷‍♂️</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )

@bot.on_message(filters.private & filters.text & ~filters.command(["login", "logout"]) & ~filters.regex("❌ Cancel"))
async def login_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in LOGIN_STATE:
        return
   
    state = LOGIN_STATE[user_id]
    step = state["step"]
    text = message.text.strip()
   
    progress = PROGRESS_STEPS[step]
   
    if step == "WAITING_PHONE":
        if not text.startswith("+") or not text[1:].isdigit():
            return await message.reply(
                "<b>❌ Invalid phone number! 😕</b>\n\n"
                f"<i>Progress: {progress}</i>\n\n"
                "Please send in format: +CountryCodePhoneNumber\n\n"
                "<blockquote>Example: +919876543210</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
       
        status_msg = await message.reply(
            f"<b>📱 Verifying phone number... 📱</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
       
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
       
        temp_client = Client(
            name=f"temp_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True
        )
       
        try:
            await temp_client.connect()
            sent_code = await temp_client.send_code(phone_number=text)
            animation_task.cancel()
           
            state["data"]["client"] = temp_client
            state["data"]["phone"] = text
            state["data"]["phone_code_hash"] = sent_code.phone_code_hash
            state["step"] = "WAITING_CODE"
           
            await status_msg.edit(
                f"<b>✅ Code sent to {text}! 📲</b>\n\n"
                f"<i>Progress: {PROGRESS_STEPS['WAITING_CODE']}</i>\n\n"
                "Please enter the verification code.\n\n"
                "<blockquote>Example: 12345</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneNumberInvalid:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Invalid phone number! 😕</b>\n\n"
                f"<i>Progress: {progress}</i>\n\n"
                "Please check and try again.",
                parse_mode=enums.ParseMode.HTML
            )
        except ApiIdInvalid:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Invalid API credentials! ⚠️</b>\n\n"
                f"<i>Progress: {progress}</i>\n\n"
                "Contact support.",
                parse_mode=enums.ParseMode.HTML
            )
            del LOGIN_STATE[user_id]
        except Exception as e:
            animation_task.cancel()
            await status_msg.edit(
                f"<b>❌ Error: {str(e)} 🤔</b>\n\n<i>Progress: {progress}</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]
   
    elif step == "WAITING_CODE":
        if not text.isdigit():
            return await message.reply(
                "<b>❌ Code must be numbers only! 😕</b>\n\n"
                f"<i>Progress: {progress}</i>\n\n"
                "Please enter the code again.",
                parse_mode=enums.ParseMode.HTML
            )
       
        status_msg = await message.reply(
            f"<b>🔢 Verifying code... 🔢</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
       
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
       
        temp_client = state["data"]["client"]
        phone = state["data"]["phone"]
        phone_code_hash = state["data"]["phone_code_hash"]
       
        try:
            await temp_client.sign_in(phone, phone_code_hash, text)
            animation_task.cancel()
            await finalize_login(status_msg, temp_client, user_id)
        except SessionPasswordNeeded:
            animation_task.cancel()
            state["step"] = "WAITING_PASSWORD"
            await status_msg.edit(
                "<b>🔒 2FA detected! 🔒</b>\n\n"
                f"<i>Progress: {PROGRESS_STEPS['WAITING_PASSWORD']}</i>\n\n"
                "Please enter your password.",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneCodeInvalid:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Invalid code! 😕</b>\n\n"
                f"<i>Progress: {progress}</i>\n\nPlease try again.",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneCodeExpired:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Code expired! ⏰</b>\n\n"
                f"<i>Progress: {progress}</i>\n\nUse /login to start over.",
                parse_mode=enums.ParseMode.HTML
            )
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]
        except Exception as e:
            animation_task.cancel()
            await status_msg.edit(
                f"<b>❌ Error: {str(e)} 🤔</b>\n\n<i>Progress: {progress}</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]
   
    elif step == "WAITING_PASSWORD":
        password = text
        temp_client = state["data"]["client"]
       
        status_msg = await message.reply(
            f"<b>🔑 Checking password... 🔑</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
       
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
       
        try:
            await temp_client.check_password(password=password)
            animation_task.cancel()
            await finalize_login(status_msg, temp_client, user_id)
        except PasswordHashInvalid:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Incorrect password. 🔑</b>\n\n"
                f"<i>Progress: {progress}</i>\n\nPlease try again.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            animation_task.cancel()
            await status_msg.edit(
                f"<b>❌ Something went wrong: {e} 🤔</b>\n\n<i>Progress: {progress}</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]

async def finalize_login(status_msg: Message, temp_client, user_id):
    try:
        session_string = await temp_client.export_session_string()
        encrypted_session = ecs(session_string)
        await temp_client.disconnect()
       
        await save_user_session(user_id, encrypted_session)
       
        if user_id in LOGIN_STATE:
            del LOGIN_STATE[user_id]
           
        await status_msg.edit(
            "<b>🎉 Login Successful! 🌟</b>\n\n"
            "<i>Progress: ✅ Phone Number → ✅ Code → ✅ Password</i>\n\n"
            "<i>Your session has been saved securely. 🔒</i>\n\n"
            "You can now use all features! 🚀",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )
    except Exception as e:
        await status_msg.edit(
            f"<b>❌ Failed to save session: {e} 😔</b>\n\nPlease try /login again.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )
        if user_id in LOGIN_STATE:
            del LOGIN_STATE[user_id]

@bot.on_message(filters.command('logout'))
async def logout_command(client, message):
    user_id = message.from_user.id
    await message.delete()
    status_msg = await message.reply('🔄 Processing logout request...')
    try:
        session_data = await get_user_data(user_id)
        
        if not session_data or 'session_string' not in session_data:
            await edit_message_safely(status_msg,
                '❌ No active session found for your account.')
            return
        encss = session_data['session_string']
        session_string = dcs(encss)
        temp_client = Client(f'temp_logout_{user_id}', api_id=API_ID,
            api_hash=API_HASH, session_string=session_string)
        try:
            await temp_client.connect()
            await temp_client.log_out()
            await edit_message_safely(status_msg,
                '✅ Telegram session terminated successfully. Removing from database...'
                )
        except Exception as e:
            logger.error(f'Error terminating session: {str(e)}')
            await edit_message_safely(status_msg,
                f"""⚠️ Error terminating Telegram session: {str(e)}
Still removing from database..."""
                )
        finally:
            await temp_client.disconnect()
        await remove_user_session(user_id)
        await edit_message_safely(status_msg,
            '✅ Logged out successfully!!')
        try:
            if os.path.exists(f"{user_id}_client.session"):
                os.remove(f"{user_id}_client.session")
        except Exception:
            pass
        if UC.get(user_id, None):
            del UC[user_id]
    except Exception as e:
        logger.error(f'Error in logout command: {str(e)}')
        try:
            await remove_user_session(user_id)
        except Exception:
            pass
        if UC.get(user_id, None):
            del UC[user_id]
        await edit_message_safely(status_msg,
            f'❌ An error occurred during logout: {str(e)}')
        try:
            if os.path.exists(f"{user_id}_client.session"):
                os.remove(f"{user_id}_client.session")
        except Exception:
            pass

async def edit_message_safely(message, text):
    """Helper function to edit message and handle errors"""
    try:
        await message.edit(text)
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f'Error editing message: {e}')

@bot.on_message(filters.command("setbot"))
async def set_bot_token(C, m):
    user_id = m.from_user.id
    args = m.text.split(" ", 1)
    if user_id in UB:
        try:
            await UB[user_id].stop()
            if UB.get(user_id, None):
                del UB[user_id]  # Remove from dictionary
                
            try:
                if os.path.exists(f"user_{user_id}.session"):
                    os.remove(f"user_{user_id}.session")
            except Exception:
                pass
            
            print(f"Stopped and removed old bot for user {user_id}")
        except Exception as e:
            print(f"Error stopping old bot for user {user_id}: {e}")
            del UB[user_id]  # Remove from dictionary

    if len(args) < 2:
        await m.reply_text("⚠️ Please provide a bot token. Usage: `/setbto token`", quote=True)
        return

    bot_token = args[1].strip()
    await save_user_bot(user_id, bot_token)
    await m.reply_text("✅ Bot token saved successfully.", quote=True)
    
    
@bot.on_message(filters.command("rembot"))
async def rem_bot_token(C, m):
    user_id = m.from_user.id
    if user_id in UB:
        try:
            await UB[user_id].stop()
            
            if UB.get(user_id, None):
                del UB[user_id]  # Remove from dictionary # Remove from dictionary
            print(f"Stopped and removed old bot for user {user_id}")
            try:
                if os.path.exists(f"user_{user_id}.session"):
                    os.remove(f"user_{user_id}.session")
            except Exception:
                pass
        except Exception as e:
            print(f"Error stopping old bot for user {user_id}: {e}")
            if UB.get(user_id, None):
                del UB[user_id]  # Remove from dictionary  # Remove from dictionary
            try:
                if os.path.exists(f"user_{user_id}.session"):
                    os.remove(f"user_{user_id}.session")
            except Exception:
                pass
    await remove_user_bot(user_id)
    await m.reply_text("✅ Bot token removed successfully.", quote=True)