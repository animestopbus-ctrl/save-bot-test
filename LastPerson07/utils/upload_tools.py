# LastPerson07/utils/upload_tools.py
import os
import time
import logging
import math
import aiofiles
from pyrogram import Client
from pyrogram.types import Message

logger = logging.getLogger(__name__)

def humanbytes(size: int) -> str:
    if not size:
        return "0 B"
    power = 2 ** 10
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    n = 0
    while size > power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds: parts.append(f"{seconds}s")
    return ", ".join(parts) or "0s"


async def progress_bar(current: int, total: int, ud_type: str, message: Message, start: float):
    """
    Updates the progress bar for an ongoing process.
    """
    now = time.time()
    diff = now - start
    
    if round(diff % 10) == 0 or current == total:
        percentage = (current * 100) / total
        speed = current / diff if diff else 0
        elapsed_time = round(diff * 1000)
        time_to_completion = round((total - current) / speed) * 1000 if speed else 0
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time_str = TimeFormatter(elapsed_time)
        estimated_total_time_str = TimeFormatter(estimated_total_time)

        progress = "".join(["♦" for _ in range(math.floor(percentage / 10))]) + \
                   "".join(["◇" for _ in range(10 - math.floor(percentage / 10))])
        
        progress_text = progress + """
│ **__Completed:__** {1}/{2}
│ **__Bytes:__** {0}%
│ **__Speed:__** {3}/s
│ **__ETA:__** {4}
╰─────────────────────╯
""".format(
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time_str if estimated_total_time_str else "0 s"
        )
        try:
            await message.edit(text=f"{ud_type}\n│ {progress_text}")
        except:
            pass


async def fast_upload(
    client: Client,
    file_path: str,
    reply: Message = None,
    name: str = None,
    progress_bar_function=progress_bar,
    ud_type: str = "Uploading"
):
    """Custom fast upload function with progress."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    start_time = time.time()

    if reply:
        await reply.edit(f"**{ud_type}...**")

    SIZE_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB
    if file_size > SIZE_LIMIT:
        # Use split_and_upload_file for large files
        await split_and_upload_file(client, reply.chat_id, file_path, name or os.path.basename(file_path))
    else:
        # Wrapper for Pyrogram's progress (which passes current, total)
        async def pyro_progress(current: int, total: int):
            await progress_bar_function(current, total, ud_type, reply, start_time)

        try:
            chat_id = reply.chat_id if reply else client.me.id

            uploaded = await client.send_document(
                chat_id=chat_id,
                document=file_path,
                file_name=name or os.path.basename(file_path),
                progress=pyro_progress,
            )

            if reply:
                await reply.edit("✅ **Upload completed successfully!**")

            return uploaded

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            if reply:
                await reply.edit(f"❌ **Upload failed:** {str(e)[:200]}")
            raise e


async def split_and_upload_file(client: Client, sender: int, file_path: str, caption: str):
    if not os.path.exists(file_path):
        await client.send_message(sender, "❌ File not found!")
        return

    file_size = os.path.getsize(file_path)
    start = await client.send_message(sender, f"ℹ️ File size: {file_size / (1024 * 1024):.2f} MB")
    PART_SIZE =  1.9 * 1024 * 1024 * 1024

    part_number = 0
    async with aiofiles.open(file_path, mode="rb") as f:
        while True:
            chunk = await f.read(PART_SIZE)
            if not chunk:
                break

            # Create part filename
            base_name, file_ext = os.path.splitext(file_path)
            part_file = f"{base_name}.part{str(part_number).zfill(3)}{file_ext}"

            # Write part to file
            async with aiofiles.open(part_file, mode="wb") as part_f:
                await part_f.write(chunk)

            # Uploading part
            edit = await client.send_message(sender, f"⬆️ Uploading part {part_number + 1}...")
            part_caption = f"{caption} \n\n**Part : {part_number + 1}**"
            await client.send_document(sender, document=part_file, caption=part_caption,
                progress=progress_bar,
                progress_args=("╭─────────────────────╮\n│      **__Pyro Uploader__**\n├─────────────────────", edit, time.time())
            )
            await edit.delete()
            os.remove(part_file)

            part_number += 1

    await start.delete()
    os.remove(file_path)