import asyncio # FloodWait के लिए रुकने के लिए (sleep) इसकी जरूरत है
from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode

import config

from ..logging import LOGGER


class Ashish(Client):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot...")
        super().__init__(
            name="L2RMUSIC",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        LOGGER(__name__).info("Attempting to connect to Telegram...")
        
        # --- FIX: Safe Login Loop with FloodWait Handler ---
        while True:
            try:
                # super().start() ही वह जगह है जहाँ auth.ImportBotAuthorization होता है
                await super().start()
                break  # अगर login सफल होता है, तो loop से बाहर निकलें
                
            except errors.FloodWait as e:
                wait_time = e.value
                LOGGER(__name__).warning(
                    f"⚠️ Telegram FloodWait during login. Waiting for {wait_time} seconds before retrying..."
                )
                # Telegram के बताए गए समय के लिए रुकें
                await asyncio.sleep(wait_time)
                
            except Exception as ex:
                # Login के दौरान आने वाली किसी भी अन्य fatal error को handle करें
                LOGGER(__name__).error(
                    f"Bot failed to start due to a non-FloodWait error: {type(ex).__name__} - {ex}"
                )
                exit()
        # --- END FIX ---
        
        # Login सफल होने के बाद, bot info सेट करें
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        # Logger ID checks (Original logic preserved)
        try:
            await self.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b><u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "Bot has failed to access the log group/channel. Make sure that you have added your bot to your log group/channel."
            )
            exit()
        except Exception as ex:
            LOGGER(__name__).error(
                f"Bot has failed to access the log group/channel.\n  Reason : {type(ex).__name__}."
            )
            exit()

        a = await self.get_chat_member(config.LOGGER_ID, self.id)
        if a.status != ChatMemberStatus.ADMINISTRATOR:
            LOGGER(__name__).error(
                "Please promote your bot as an admin in your log group/channel."
            )
            exit()
            
        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
