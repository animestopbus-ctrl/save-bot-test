# ---------------------------------------------------
# File Name: ytdl.py (pure code)
# Description: A Pyrogram bot for downloading yt and other sites videos from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: LastPerson07
# GitHub: https://github.com/LastPerson07/
# Telegram: https://t.me/DmOwner
# YouTube: https://youtube.com/@LastPerson07
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.5
# License: MIT License
# ---------------------------------------------------

import yt_dlp
import os
import tempfile
import time
import asyncio
import random
import string
import requests
import logging
import time
import math
import shutil
from LastPerson07.shared_client import client, app
from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeVideo
from LastPerson07.utils.func import get_video_metadata, screenshot
from telethon.tl.functions.messages import EditMessageRequest
from concurrent.futures import ThreadPoolExecutor
import aiohttp 
import logging
import aiofiles
from LastPerson07.config import YT_COOKIES, INSTA_COOKIES
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC
from mutagen.mp3 import MP3
from LastPerson07.utils.upload_tools import fast_upload, split_and_upload_file
 
logger = logging.getLogger(__name__)
 
 
thread_pool = ThreadPoolExecutor()
ongoing_downloads = {}
 
def d_thumbnail(thumbnail_url, save_path):
    try:
        response = requests.get(thumbnail_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download thumbnail: {e}")
        return None
 
 
async def download_thumbnail_async(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(path, 'wb') as f:
                    f.write(await response.read())
 
 
async def extract_audio_async(ydl_opts, url):
    def sync_extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)
    return await asyncio.get_event_loop().run_in_executor(thread_pool, sync_extract)
 
 
def get_random_string(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length)) 
 
 
async def process_audio(client, event, url, cookies_env_var=None):
    cookies = None
    if cookies_env_var:
        cookies = cookies_env_var
 
    temp_cookie_path = None
    if cookies:
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_cookie_file:
            temp_cookie_file.write(cookies)
            temp_cookie_path = temp_cookie_file.name
 
    start_time = time.time()
    temp_dir = tempfile.mkdtemp()
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'cookiefile': temp_cookie_path,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': False,
        'noplaylist': False,  # Enable playlist support
    }
    prog = None
 
    progress_message = await event.reply("**__Starting audio extraction...__**")
 
    try:
         
        info_dict = await extract_audio_async(ydl_opts, url)
        is_playlist = 'entries' in info_dict
        files = []
 
        if is_playlist:
            await progress_message.edit(f"**__Playlist detected with {len(info_dict['entries'])} items...__**")
            for entry in info_dict['entries']:
                title = entry.get('title', 'Extracted Audio')
                file_path = os.path.join(temp_dir, f"{title}.mp3")
                if os.path.exists(file_path):
                    files.append((file_path, title))
        else:
            title = info_dict.get('title', 'Extracted Audio')
            file_path = os.path.join(temp_dir, f"{title}.mp3")
            if os.path.exists(file_path):
                files.append((file_path, title))
 
        for file_path, title in files:
            await progress_message.edit(f"**__Editing metadata for {title}...__**")
 
            def edit_metadata():
                audio_file = MP3(file_path, ID3=ID3)
                try:
                    audio_file.add_tags()
                except Exception:
                    pass
                audio_file.tags["TIT2"] = TIT2(encoding=3, text=title)
                audio_file.tags["TPE1"] = TPE1(encoding=3, text="LastPerson07")
                audio_file.tags["COMM"] = COMM(encoding=3, lang="eng", desc="Comment", text="Processed by LastPerson07")
 
                thumbnail_url = info_dict.get('thumbnail') if not is_playlist else entry.get('thumbnail')
                if thumbnail_url:
                    thumbnail_path = os.path.join(tempfile.gettempdir(), "thumb.jpg")
                    asyncio.run(download_thumbnail_async(thumbnail_url, thumbnail_path))
                    with open(thumbnail_path, 'rb') as img:
                        audio_file.tags["APIC"] = APIC(
                            encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read()
                        )
                    os.remove(thumbnail_path)
                audio_file.save()
 
            await asyncio.to_thread(edit_metadata)
 
            chat_id = event.chat_id
            await progress_message.delete()
            prog = await client.send_message(chat_id, f"**__Starting Upload for {title}...__**")
            uploaded = await fast_upload(
                client, file_path, 
                reply=prog, 
                name=None,
                progress_bar_function=lambda current, total: progress_callback(current, total, chat_id)
            )
            await client.send_file(chat_id, uploaded, caption=f"**{title}**\n\n**__Powered by LastPerson07__**")
            if prog:
                await prog.delete()
            os.remove(file_path)
 
    except Exception as e:
        logger.exception("Error during audio extraction or upload")
        await event.reply(f"**__An error occurred: {e}__**")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)
 
@client.on(events.NewMessage(pattern="/adl"))
async def handler(event):
    user_id = event.sender_id
    if user_id in ongoing_downloads:
        await event.reply("**You already have an ongoing download. Please wait until it completes!**")
        return
 
    if len(event.message.text.split()) < 2:
        await event.reply("**Usage:** `/adl <video-link>`\n\nPlease provide a valid video link!")
        return    
 
    url = event.message.text.split()[1]
    ongoing_downloads[user_id] = True
 
    try:
        if "instagram.com" in url:
            await process_audio(client, event, url, cookies_env_var="INSTA_COOKIES")
        elif "youtube.com" in url or "youtu.be" in url:
            await process_audio(client, event, url, cookies_env_var="YT_COOKIES")
        else:
            await process_audio(client, event, url)
    except Exception as e:
        await event.reply(f"**An error occurred:** `{e}`")
    finally:
        ongoing_downloads.pop(user_id, None)
 
 
async def fetch_video_info(url, ydl_opts, progress_message, check_duration_and_size):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
 
        if check_duration_and_size:
             
            duration = info_dict.get('duration', 0)
            if duration and duration > 3 * 3600:   
                await progress_message.edit("**❌ __Video is longer than 3 hours. Download aborted...__**")
                return None
 
             
            estimated_size = info_dict.get('filesize_approx', 0)
            if estimated_size and estimated_size > 2 * 1024 * 1024 * 1024:   
                await progress_message.edit("**🤞 __Video size is larger than 2GB. Aborting download.__**")
                return None
 
        return info_dict
 
def download_video(url, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
 
 
@client.on(events.NewMessage(pattern="/dl"))
async def handler(event):
    user_id = event.sender_id
 
     
    if user_id in ongoing_downloads:
        await event.reply("**You already have an ongoing ytdlp download. Please wait until it completes!**")
        return
 
    if len(event.message.text.split()) < 2:
        await event.reply("**Usage:** `/dl <video-link>`\n\nPlease provide a valid video link!")
        return    
 
    url = event.message.text.split()[1]
 
     
    try:
        if "instagram.com" in url:
            await process_video(client, event, url, "INSTA_COOKIES", check_duration_and_size=False)
        elif "youtube.com" in url or "youtu.be" in url:
            await process_video(client, event, url, "YT_COOKIES", check_duration_and_size=True)
        else:
            await process_video(client, event, url, None, check_duration_and_size=False)
 
    except Exception as e:
        await event.reply(f"**An error occurred:** `{e}`")
    finally:
         
        ongoing_downloads.pop(user_id, None)
 
 
 
 
user_progress = {}
 
def progress_callback(done, total, user_id):
     
    if user_id not in user_progress:
        user_progress[user_id] = {
            'previous_done': 0,
            'previous_time': time.time()
        }
 
     
    user_data = user_progress[user_id]
 
     
    percent = (done / total) * 100
 
     
    completed_blocks = int(percent // 10)
    remaining_blocks = 10 - completed_blocks
    progress_bar = "♦" * completed_blocks + "◇" * remaining_blocks
 
     
    done_mb = done / (1024 * 1024)   
    total_mb = total / (1024 * 1024)
 
     
    speed = done - user_data['previous_done']
    elapsed_time = time.time() - user_data['previous_time']
 
    if elapsed_time > 0:
        speed_bps = speed / elapsed_time   
        speed_mbps = (speed_bps * 8) / (1024 * 1024)   
    else:
        speed_mbps = 0
 
     
    if speed_bps > 0:
        remaining_time = (total - done) / speed_bps
    else:
        remaining_time = 0
 
     
    remaining_time_min = remaining_time / 60
 
     
    final = (
        f"╭──────────────────╮\n"
        f"│        **__Uploading...__**       \n"
        f"├──────────\n"
        f"│ {progress_bar}\n\n"
        f"│ **__Progress:__** {percent:.2f}%\n"
        f"│ **__Done:__** {done_mb:.2f} MB / {total_mb:.2f} MB\n"
        f"│ **__Speed:__** {speed_mbps:.2f} Mbps\n"
        f"│ **__Time Remaining:__** {remaining_time_min:.2f} min\n"
        f"╰──────────────────╯\n\n"
        f"**__Powered by LastPerson07__**"
    )
 
     
    user_data['previous_done'] = done
    user_data['previous_time'] = time.time()
 
    return final
 
async def process_video(client, event, url, cookies_env_var, check_duration_and_size=False):
    start_time = time.time()
    logger.info(f"Received link: {url}")
     
    cookies = None
    if cookies_env_var:
        cookies = cookies_env_var
 
     
    temp_dir = tempfile.mkdtemp()
    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'format': 'best',
        'cookiefile': temp_cookie_path if temp_cookie_path else None,
        'writethumbnail': True,
        'verbose': True,
        'noplaylist': False,  # Enable playlist support
    }
    prog = None
    progress_message = await event.reply("**__Starting download...__**")
    logger.info("Starting the download process...")
    try:
        info_dict = await fetch_video_info(url, ydl_opts, progress_message, check_duration_and_size)
        if not info_dict:
            return
         
        await asyncio.to_thread(download_video, url, ydl_opts)
        is_playlist = 'entries' in info_dict
        files = []
 
        if is_playlist:
            await progress_message.edit(f"**__Playlist detected with {len(info_dict['entries'])} items...__**")
            for entry in info_dict['entries']:
                title = entry.get('title', 'Powered by LastPerson07')
                file_path = os.path.join(temp_dir, f"{title}.mp4")  # Assuming mp4 for video
                if os.path.exists(file_path):
                    files.append((file_path, title))
        else:
            title = info_dict.get('title', 'Powered by LastPerson07')
            file_path = os.path.join(temp_dir, f"{title}.mp4")
            if os.path.exists(file_path):
                files.append((file_path, title))
 
        for file_path, title in files:
            k = await get_video_metadata(file_path)      
            W = k['width']
            H = k['height']
            D = k['duration']
            metadata = {'width': info_dict.get('width') or W, 'height': info_dict.get('height') or H, 'duration': int(info_dict.get('duration') or 0) or D}
            thumbnail_url = info_dict.get('thumbnail', None) if not is_playlist else entry.get('thumbnail')
            THUMB = None
 
            if thumbnail_url:
                thumbnail_file = os.path.join(tempfile.gettempdir(), get_random_string() + ".jpg")
                downloaded_thumb = d_thumbnail(thumbnail_url, thumbnail_file)
                if downloaded_thumb:
                    logger.info(f"Thumbnail saved at: {downloaded_thumb}")
                    THUMB = downloaded_thumb
 
            if not THUMB:
                THUMB = await screenshot(file_path, metadata['duration'], event.sender_id)
 
            chat_id = event.chat_id
            SIZE = 2 * 1024 * 1024 * 1024  # 2GB limit
            caption = f"{title}"
     
            if os.path.exists(file_path) and os.path.getsize(file_path) > SIZE:
                prog = await client.send_message(chat_id, f"**__Starting Upload for {title}...__**")
                await split_and_upload_file(app, chat_id, file_path, caption)
                if prog:
                    await prog.delete()
             
            if os.path.exists(file_path):
                await progress_message.delete()
                prog = await client.send_message(chat_id, f"**__Starting Upload for {title}...__**")
                uploaded = await fast_upload(
                    client, file_path,
                    reply=prog,
                    name=None,
                    progress_bar_function=lambda current, total: progress_callback(current, total, chat_id)
                )
                await client.send_file(
                    event.chat_id,
                    uploaded,
                    caption=f"**{title}**\n\n**__Powered by LastPerson07__**",
                    attributes=[
                        DocumentAttributeVideo(
                            duration=metadata['duration'],
                            w=metadata['width'],
                            h=metadata['height'],
                            supports_streaming=True
                        )
                    ],
                    thumb=THUMB if THUMB else None
                )
                if prog:
                    await prog.delete()
                os.remove(file_path)
            else:
                await event.reply("**__File not found after download. Something went wrong!__**")
    except Exception as e:
        logger.exception("An error occurred during download or upload.")
        await event.reply(f"**__An error occurred: {e}__**")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)
        if THUMB and os.path.exists(THUMB):
            os.remove(THUMB)
 

PROGRESS_BAR = """
│ **__Completed:__** {1}/{2}
│ **__Bytes:__** {0}%
│ **__Speed:__** {3}/s
│ **__ETA:__** {4}
╰─────────────────────╯
"""

async def get_seconds(time_string: str) -> int:
    """
    Converts a time string (e.g., '5min', '2hour') into seconds.
    """
    def extract_value_and_unit(ts: str):
        value = ''.join(filter(str.isdigit, ts))
        unit = ts[len(value):].strip()
        return int(value) if value else 0, unit
    
    value, unit = extract_value_and_unit(time_string)
    time_units = {
        's': 1,
        'min': 60,
        'hour': 3600,
        'day': 86400,
        'month': 86400 * 30,
        'year': 86400 * 365
    }
    
    return value * time_units.get(unit, 0)

def progress_callback(done, total, user_id):
     
    if user_id not in user_progress:
        user_progress[user_id] = {
            'previous_done': 0,
            'previous_time': time.time()
        }
 
     
    user_data = user_progress[user_id]
 
     
    percent = (done / total) * 100
 
     
    completed_blocks = int(percent // 10)
    remaining_blocks = 10 - completed_blocks
    progress_bar = "♦" * completed_blocks + "◇" * remaining_blocks
 
     
    done_mb = done / (1024 * 1024)   
    total_mb = total / (1024 * 1024)
 
     
    speed = done - user_data['previous_done']
    elapsed_time = time.time() - user_data['previous_time']
 
    if elapsed_time > 0:
        speed_bps = speed / elapsed_time   
        speed_mbps = (speed_bps * 8) / (1024 * 1024)   
    else:
        speed_mbps = 0
 
     
    if speed_bps > 0:
        remaining_time = (total - done) / speed_bps
    else:
        remaining_time = 0
 
     
    remaining_time_min = remaining_time / 60
 
     
    final = (
        f"╭──────────────────╮\n"
        f"│        **__Uploading...__**       \n"
        f"├──────────\n"
        f"│ {progress_bar}\n\n"
        f"│ **__Progress:__** {percent:.2f}%\n"
        f"│ **__Done:__** {done_mb:.2f} MB / {total_mb:.2f} MB\n"
        f"│ **__Speed:__** {speed_mbps:.2f} Mbps\n"
        f"│ **__Time Remaining:__** {remaining_time_min:.2f} min\n"
        f"╰──────────────────╯\n\n"
        f"**__Powered by LastPerson07__**"
    )
 
     
    user_data['previous_done'] = done
    user_data['previous_time'] = time.time()
 
    return final

def humanbytes(size: int) -> str:
    """
    Converts bytes into a human-readable format.
    """
    if not size:
        return ""
    
    power = 2**10
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    n = 0
    while size > power and n < len(units) - 1:
        size /= power
        n += 1
    
    return f"{round(size, 2)} {units[n]}"

def TimeFormatter(milliseconds: int) -> str:
    """
    Formats milliseconds into a human-readable duration.
    """
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds: parts.append(f"{seconds}s")
    if milliseconds: parts.append(f"{milliseconds}ms")
    
    return ', '.join(parts)

def convert(seconds: int) -> str:
    """
    Converts seconds into HH:MM:SS format.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"