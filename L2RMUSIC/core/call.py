import os
import asyncio
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded
from pytgcalls.exceptions import AlreadyJoinedError, NoActiveGroupCall, TelegramServerError

from L2RMUSIC import LOGGER, YouTube, app
from L2RMUSIC.misc import db
from L2RMUSIC.utils.database import (
    group_assistant, add_active_chat, remove_active_chat,
    add_active_video_chat, remove_active_video_chat,
    get_lang, get_loop, set_loop, music_on, is_autoend
)
from L2RMUSIC.utils.exceptions import AssistantErr
from L2RMUSIC.utils.formatters import check_duration, seconds_to_min, speed_converter
from L2RMUSIC.utils.inline.play import stream_markup
from L2RMUSIC.utils.stream.autoclear import auto_clean
from L2RMUSIC.utils.thumbnails import get_thumb
from strings import get_string

import config
from pyrogram.types import InlineKeyboardMarkup

autoend = {}
counter = {}

async def _clear_(chat_id: int):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)

class Call:
    def __init__(self):
        self.clients = []
        self.calls = []

        # Dynamically create userbots based on available strings
        for i, session in enumerate([config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5], start=1):
            if session:
                client = Client(f"L2RMUSICAss{i}", config.API_ID, config.API_HASH, session_string=str(session))
                call = PyTgCalls(client, cache_duration=100)
                self.clients.append(client)
                self.calls.append(call)

    async def get_assistant(self, chat_id: int):
        return await group_assistant(self, chat_id)

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Clients...\n")
        for call in self.calls:
            await call.start()

    async def pause_stream(self, chat_id: int):
        assistant = await self.get_assistant(chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await self.get_assistant(chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await self.get_assistant(chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except Exception:
            pass

    async def stop_stream_force(self, chat_id: int):
        for call in self.calls:
            try:
                await call.leave_group_call(chat_id)
            except Exception:
                continue
        try:
            await _clear_(chat_id)
        except Exception:
            pass

    async def ping(self):
        pings = []
        for call in self.calls:
            try:
                pings.append(await call.ping)
            except Exception:
                continue
        return str(round(sum(pings) / len(pings), 3)) if pings else "0"

    async def decorators(self):
        for call in self.calls:
            @call.on_kicked()
            @call.on_closed_voice_chat()
            @call.on_left()
            async def handle_leave(_, chat_id: int):
                await self.stop_stream(chat_id)

            @call.on_stream_end()
            async def handle_stream_end(client, update: Update):
                if isinstance(update, StreamAudioEnded):
                    await self.change_stream(client, update.chat_id)
