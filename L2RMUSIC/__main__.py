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
        LOGGER(__name__).error("♦️𝐒𝐭𝐫𝐢𝐧𝐠 𝐒𝐞𝐬𝐬𝐢𝐨𝐧 𝐍𝐨𝐭 𝐅𝐢𝐥𝐥𝐞𝐝, 𝐏𝐥𝐞𝐚𝐬𝐞 𝐅𝐢𝐥𝐥 𝐀 𝐏𝐲𝐫𝐨𝐠𝐫𝐚𝐦 𝐒𝐞𝐬𝐬𝐢𝐨𝐧 🍃...")
        exit()

    # Initialize sudo permissions
    await sudo()

    # Load banned users into the BANNED_USERS set
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)

        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception as e:
        LOGGER(__name__).warning(f"Failed to load banned users: {e}")

    # Start the Pyrogram app
    await app.start()

    # Dynamically import all modules
    for module in ALL_MODULES:
        try:
            importlib.import_module(f"L2RMUSIC.plugins.{module}")
        except ImportError as e:
            LOGGER(__name__).warning(f"Failed to import module {module}: {e}")
    
    LOGGER("L2RMUSIC.plugins").info("👻𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲❣️...")

    # Start the userbot and Ashish (Music call)
    await userbot.start()
    await Ashish.start()

    try:
        # Attempt to start streaming a video file
        await Ashish.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("L2RMUSIC").error("🙏𝗣𝗹𝗭 𝗦𝗧𝗔𝗥𝗧 𝗬𝗢𝗨𝗥 𝗟𝗢𝗚 𝗚𝗥𝗢𝗨𝗣 𝗩𝗢𝗜𝗖𝗘𝗖𝗛𝗔𝗧\𝗖𝗛𝗔𝗡𝗡𝗘𝗟\n\n𝗠𝗨𝗦𝗜𝗖 𝗕𝗢𝗧 𝗦𝗧𝗢𝗣✨........")
        exit()
    except Exception as e:
        LOGGER("L2RMUSIC").error(f"Error occurred while starting stream: {e}")

    # Register decorators for Ashish
    await Ashish.decorators()

    LOGGER("L2RMUSIC").info("╔═════ஜ۩۞۩ஜ════╗\n  ༄𝐿 2 𝙍.🖤🜲𝐊𝐈𝐍𝐆❦︎ 𝆺𝅥⃝🍷\n╚═════ஜ۩۞۩ஜ════╝")

    # Wait indefinitely until app is manually stopped
    await idle()

    # Stop the bot services gracefully
    await app.stop()
    await userbot.stop()
    LOGGER("L2RMUSIC").info("✨𝗦𝗧𝗢𝗣 𝐿2𝙍 𝗠𝗨𝗦𝗜𝗖🎻 𝗕𝗢𝗧🍒...")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
