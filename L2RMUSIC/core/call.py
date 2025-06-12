import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded

import config
from L2RMUSIC import LOGGER, YouTube, app
from L2RMUSIC.misc import db
from L2RMUSIC.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from L2RMUSIC.utils.exceptions import AssistantErr
from L2RMUSIC.utils.formatters import check_duration, seconds_to_min, speed_converter
from L2RMUSIC.utils.inline.play import stream_markup
from L2RMUSIC.utils.stream.autoclear import auto_clean
from L2RMUSIC.utils.thumbnails import get_thumb
from strings import get_string


autoend = {}
counter = {}


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        # Setup multiple clients for concurrent operations
        self.clients = [
            self._create_client("AshishAss1", config.STRING1),
            self._create_client("AshishAss2", config.STRING2),
            self._create_client("AshishAss3", config.STRING3),
            self._create_client("AshishAss4", config.STRING4),
            self._create_client("AshishAss5", config.STRING5),
        ]
        self.pytg_calls = [PyTgCalls(client, cache_duration=100) for client in self.clients]

    def _create_client(self, name, session_string):
        return Client(name=name, api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(session_string))

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except Exception as e:
            LOGGER(__name__).error(f"Error stopping stream: {e}")

    async def stop_stream_force(self, chat_id: int):
        # Loop over each client and try to stop the stream if active
        for call in self.pytg_calls:
            try:
                await call.leave_group_call(chat_id)
            except:
                pass
        await _clear_(chat_id)

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != "1.0":
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                vs = {
                    "0.5": 2.0,
                    "0.75": 1.35,
                    "1.5": 0.68,
                    "2.0": 0.5
                }.get(str(speed), 1.0)
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                out = file_path
        else:
            out = file_path

        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)

        stream = AudioVideoPiped(
            out,
            audio_parameters=HighQualityAudio(),
            video_parameters=MediumQualityVideo(),
            additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
        ) if playing[0]["streamtype"] == "video" else AudioPiped(
            out,
            audio_parameters=HighQualityAudio(),
            additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
        )

        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.change_stream(chat_id, stream)
        else:
            raise AssistantErr("Umm")

        db[chat_id][0]["played"] = con_seconds
        db[chat_id][0]["dur"] = duration
        db[chat_id][0]["seconds"] = dur
        db[chat_id][0]["speed_path"] = out
        db[chat_id][0]["speed"] = speed

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        stream = AudioVideoPiped(link, audio_parameters=HighQualityAudio(), video_parameters=MediumQualityVideo()) if video else AudioPiped(link, audio_parameters=HighQualityAudio())
        await assistant.change_stream(chat_id, stream)

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except Exception as e:
            LOGGER(__name__).error(f"Error in force_stop_stream: {e}")

        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except Exception as e:
            LOGGER(__name__).error(f"Error leaving group call: {e}")

    async def ping(self):
        pings = []
        for call in self.pytg_calls:
            try:
                pings.append(await call.ping)
            except Exception as e:
                LOGGER(__name__).error(f"Error pinging client: {e}")
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        for client in self.clients:
            await client.start()

    async def decorators(self):
        # Re-organize the decorator logic to handle all clients dynamically
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        async def stream_end_handler(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)

        for client in self.pytg_calls:
            client.on_kicked()(stream_services_handler)
            client.on_closed_voice_chat()(stream_services_handler)
            client.on_left()(stream_services_handler)
            client.on_stream_end()(stream_end_handler)


Ashish = Call()
