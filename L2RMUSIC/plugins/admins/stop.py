from pyrogram import filters
from pyrogram.types import Message

from L2RMUSIC import app
from L2RMUSIC.core.call import Ashish
from L2RMUSIC.utils.database import set_loop
from L2RMUSIC.utils.decorators import AdminRightsCheck
from L2RMUSIC.utils.inline import close_markup
from config import BANNED_USERS


@app.on_message(
    filters.command(["end", "stop", "cend", "cstop"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_music(cli, message: Message, _, chat_id):
    if not len(message.command) == 1:
        return
    await Ashish.stop_stream(chat_id)
    await set_loop(chat_id, 0)
    await message.reply_text(
        _["admin_5"].format(message.from_user.mention), reply_markup=close_markup(_)
    )
