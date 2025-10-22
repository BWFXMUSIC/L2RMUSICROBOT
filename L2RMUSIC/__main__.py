import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from L2RMUSIC import LOGGER, app, userbot
from L2RMUSIC.core.call import Ashish
from L2RMUSIC.misc import sudo
from L2RMUSIC.plugins import ALL_MODULES
from L2RMUSIC.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("♦️ 𝐒𝐭𝐫𝐢𝐧𝐠 𝐒𝐞𝐬𝐬𝐢𝐨𝐧 𝐍𝐨𝐭 𝐅𝐢𝐥𝐥𝐞𝐝, 𝐏𝐥𝐞𝐚𝐬𝐞 𝐅𝐢𝐥𝐥 𝐀 𝐏𝐲𝐫𝐨𝐠𝐫𝐚𝐦 𝐒𝐞𝐬𝐬𝐢𝐨𝐧 🍃...")
        exit()

    # Run sudo method to initialize required configurations
    await sudo()

    # Try to load banned users
    try:
        # Get global and normal banned users and add to BANNED_USERS set
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)

        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)

    except Exception as e:
        LOGGER(__name__).error(f"Error loading banned users: {str(e)}")
        pass  # Optionally, you can handle this error or log it

    # Start the app and userbot
    await app.start()

    # Dynamically load all modules
    for all_module in ALL_MODULES:
        importlib.import_module("L2RMUSIC.plugins" + all_module)

    LOGGER("L2RMUSIC.plugins").info("👻 𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲❣️...")

    # Start the userbot and Ashish (your music call handler)
    await userbot.start()
    await Ashish.start()

    # Try to start streaming a media file
    try:
        await Ashish.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("L2RMUSIC").error(
            "🙏𝗣𝗹𝗭 𝗦𝗧𝗔𝗥𝗧 𝗬𝗢𝗨𝗥 𝗟𝗢𝗚 𝗚𝗥𝗢𝗨𝗣 𝗩𝗢𝗜𝗖𝗘𝗖𝗛𝗔𝗧/𝗖𝗛𝗔𝗡𝗡𝗘𝗟\n\n𝗠𝗨𝗦𝗜𝗖 𝗕𝗢𝗧 𝗦𝗧𝗢𝗣✨........"
        )
        exit()
    except Exception as e:
        LOGGER("L2RMUSIC").error(f"Error during stream_call: {str(e)}")
        pass  # Handle streaming errors if needed

    # Start decorators for Ashish (probably for event handlers)
    await Ashish.decorators()

    LOGGER("L2RMUSIC").info("╔═════ஜ۩۞۩ஜ════╗\n  ༄𝐿 2 𝙍.🖤🜲𝐾𝐼𝐍𝐺❦︎ 𝆺𝅥⃝🍷\n╚═════ஜ۩۞۩ஜ════╝")

    # Wait for the bot to idle (keep it running)
    await idle()

    # Stop the app and userbot when idle is done
    await app.stop()
    await userbot.stop()

    LOGGER("L2RMUSIC").info("✨𝗦𝗧𝗢𝗣 𝐿2𝙍 𝗠𝗨𝗦𝗜𝗖🎻 𝗕𝗢𝗧🍒...")


if __name__ == "__main__":
    # Use asyncio's event loop to run the init function
    asyncio.get_event_loop().run_until_complete(init())
