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


def cookies() -> str:
    cookie_dir = "cookies"
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not cookies_files:
        raise FileNotFoundError("No cookie files found in 'cookies' directory")
    cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))
    return cookie_file


async def shell_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if err:
        err_str = err.decode("utf-8")
        if "unavailable videos are hidden" in err_str.lower():
            return out.decode("utf-8")
        else:
            return err_str
    return out.decode("utf-8")


async def api_download(vidid: str, video: bool = False) -> Union[str, None]:
    API = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
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
        results = response.json()["url"]

    cmd = f"yt-dlp '{results}' -o '{path}'"
    await shell_cmd(cmd)
    if os.path.isfile(path):
        return path
    return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message: Message) -> Union[str, None]:
        messages = [message]
        if message.reply_to_message:
            messages.append(message.reply_to_message)

        for msg in messages:
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        text = msg.text or msg.caption or ""
                        return text[entity.offset : entity.offset + entity.length]
            if msg.caption_entities:
                for entity in msg.caption_entities:
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
        duration_min = result["duration"]
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]
        duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]
        return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]
        return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]
        return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies",
            cookies(),
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        return 0, stderr.decode()

    async def playlist(self, link: str, limit: int, user_id: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download --cookies {cookies()} {link}"
        )
        result = [key for key in playlist.split("\n") if key]
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        result = (await results.next())["result"][0]
        track_details = {
            "title": result["title"],
            "link": result["link"],
            "vidid": result["id"],
            "duration_min": result["duration"],
            "thumb": result["thumbnails"][0]["url"].split("?")[0],
        }
        return track_details, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        ytdl_opts = {"quiet": True, "cookiefile": cookies()}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for fmt in r.get("formats", []):
                try:
                    # Skip dash manifests and incomplete formats
                    if "dash" in str(fmt["format"]).lower():
                        continue
                    formats_available.append(
                        {
                            "format": fmt["format"],
                            "filesize": fmt.get("filesize"),
                            "format_id": fmt.get("format_id"),
                            "ext": fmt.get("ext"),
                            "format_note": fmt.get("format_note"),
                            "yturl": link,
                        }
                    )
                except KeyError:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=10)
        result = (await results.next())["result"]
        entry = result[query_type]
        title = entry["title"]
        duration_min = entry["duration"]
        vidid = entry["id"]
        thumbnail = entry["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> Union[str, tuple]:

        if videoid:
            vidid = link
            link = self.base + link
        else:
            pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=|embed\/|v\/|live_stream\?stream_id=|(?:\/|\?|&)v=)?([^&\n]+)"
            match = re.search(pattern, link)
            if not match:
                raise ValueError("Invalid YouTube link")
            vidid = match.group(1)

        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies(),
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=False)
            file_path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(file_path):
                return file_path
            ydl.download([link])
            return file_path

        def video_dl():
            ydl_opts = {
                "format": "(bestvideo[height<=720][width<=1280][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies(),
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            info = ydl.extract_info(link, download=False)
            file_path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(file_path):
                return file_path
            ydl.download([link])
            return file_path

        def song_video_dl():
            if not (format_id and title):
                raise ValueError("format_id and title must be provided for song_video_dl")
            formats = f"{format_id}+140"
            outtmpl = f"downloads/{title}"
            ydl_opts = {
                "format": formats,
                "outtmpl": outtmpl,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
                "cookiefile": cookies(),
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            ydl.download([link])

        def song_audio_dl():
            if not (format_id and title):
                raise ValueError("format_id and title must be provided for song_audio_dl")
            outtmpl = f"downloads/{title}.%(ext)s"
            ydl_opts = {
                "format": format_id,
                "outtmpl": outtmpl,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "cookiefile": cookies(),
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            ydl.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            return f"downloads/{title}.mp4"

        if songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            return f"downloads/{title}.mp3"

        if video:
            if await is_on_off(2):
                # Direct download using yt-dlp
                downloaded_file = await loop.run_in_executor(None, video_dl)
                direct = True
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "-g",
                    "-f",
                    "best[height<=720][width<=1280]",
                    link,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = None
                else:
                    return None
            return downloaded_file, direct

        # Default audio download
        downloaded_file = await loop.run_in_executor(None, audio_dl)
        direct = True
        return downloaded_file, direct
