import asyncio
import os
import random
import re
from typing import Union

import httpx
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from L2RMUSIC.utils.formatters import time_to_seconds
from L2RMUSIC.utils.database import is_on_off


def cookies():
    cookie_dir = os.path.join("cookies", "yt-dlp")  # Fixed this line
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))
    return cookie_file


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    err_decoded = err.decode("utf-8").strip()

    if err and "unavailable videos are hidden" not in err_decoded.lower():
        return err_decoded
    return out.decode("utf-8").strip()


async def api_download(vidid, video=False):
    API = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/116.0.0.0",
    }

    if video:
        path = os.path.join("downloads", f"{vidid}.mp4")
        data = {"url": f"https://www.youtube.com/watch?v={vidid}", "vQuality": "480"}
    else:
        path = os.path.join("downloads", f"{vidid}.m4a")
        data = {
            "url": f"https://www.youtube.com/watch?v={vidid}",
            "isAudioOnly": "True",
            "aFormat": "opus",
        }

    async with httpx.AsyncClient(http2=True) as client:
        response = await client.post(API, headers=headers, json=data)
        response.raise_for_status()
        results = response.json().get("url")

    cmd = f"yt-dlp '{results}' -o '{path}'"
    await shell_cmd(cmd)
    return path if os.path.isfile(path) else None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        return (message.text or message.caption)[
                            entity.offset: entity.offset + entity.length
                        ]
            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]

        title = result["title"]
        duration_min = result.get("duration", "0:00")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]
        duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0

        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        results = VideosSearch(link, limit=1)
        return (await results.next())["result"][0]["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        results = VideosSearch(link, limit=1)
        return (await results.next())["result"][0]["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        results = VideosSearch(link, limit=1)
        return (await results.next())["result"][0]["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--cookies", cookies(), "-g",
            "-f", "best[height<=?720][width<=?1280]",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return (1, stdout.decode().strip()) if stdout else (0, stderr.decode().strip())

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        link = link.split("&")[0]

        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download --cookies {cookies()} {link}"
        )
        return [x for x in playlist.strip().split("\n") if x]

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]

        return {
            "title": result["title"],
            "link": result["link"],
            "vidid": result["id"],
            "duration_min": result["duration"],
            "thumb": result["thumbnails"][0]["url"].split("?")[0],
        }, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        ytdl_opts = {"quiet": True, "cookiefile": cookies()}
        formats_available = []

        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            r = ydl.extract_info(link, download=False)
            for format in r.get("formats", []):
                if "dash" in str(format.get("format", "")).lower():
                    continue
                try:
                    formats_available.append({
                        "format": format["format"],
                        "filesize": format.get("filesize"),
                        "format_id": format["format_id"],
                        "ext": format["ext"],
                        "format_note": format["format_note"],
                        "yturl": link,
                    })
                except KeyError:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        results = await VideosSearch(link, limit=10).next()
        result = results["result"][query_type]

        return (
            result["title"],
            result["duration"],
            result["thumbnails"][0]["url"].split("?")[0],
            result["id"],
        )

    async def download(
        self,
        link: str,
        myst
