import threading
import asyncio
import urllib.parse
import re
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
from pyrogram import Client
from configs import Config

# Flask Server Setup for Health Check
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Successfully!"

def run_web():
    app.run(host="0.0.0.0", port=8080, threaded=True)

# Flask Server Run in Background
threading.Thread(target=run_web, daemon=True).start()

# Telethon Clients
tbot = TelegramClient('mdisktelethonbot', Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
client = TelegramClient(StringSession(Config.USER_SESSION_STRING), Config.API_ID, Config.API_HASH)

# Pyrogram Client with Plugins Support
Bot = Client(
    "PrimeBotz",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

async def get_user_join(user_id):
    if Config.FORCE_SUB == "False":
        return True
    try:
        await tbot(GetParticipantRequest(channel=int(Config.UPDATES_CHANNEL), participant=user_id))
        return True
    except UserNotParticipantError:
        return False

@tbot.on(events.NewMessage(incoming=True))
async def message_handler(event):
    try:
        if event.message.post or event.text.startswith("/"):
            return

        print(f"\nMessage Received: {event.text}\n")

        # Force Subscription Check
        if not await get_user_join(event.sender_id):
            haha = await event.reply(
                f"**Hey! {event.sender.first_name if event.sender else 'User'} 😃**\n\n"
                "**You Have To Join Our Update Channel To Use Me ✅**\n\n"
                "**Click Below Button To Join Now.👇🏻**",
                buttons=Button.url('🍿Updates Channel🍿', f'https://t.me/{Config.UPDATES_CHANNEL_USERNAME}')
            )
            await asyncio.sleep(Config.AUTO_DELETE_TIME)
            return await haha.delete()

        args = event.text
        if not args:
            return

        txt = await event.reply(f'**Searching for "{args}" 🔍**')

        search_results = []
        CHANNEL_ID = Config.CHANNEL_ID

        async for msg in client.iter_messages(CHANNEL_ID, limit=5, search=args):
            search_results.append(msg)

        if not search_results:
            answer = f'''** Sorry {event.sender.first_name if event.sender else 'User'} No Results Found For {event.text}**

**Please check the spelling on** [Google](http://www.google.com/search?q={event.text.replace(' ', '%20')}%20Movie) 🔍
**Click On The Help To Know How To Watch**
    '''
            newbutton = [Button.url('Help🙋', f'https://t.me/postsearchbot?start=Watch')]

            await txt.delete()
            result = await event.reply(answer, buttons=newbutton, link_preview=False)
            await asyncio.sleep(Config.AUTO_DELETE_TIME)
            return await result.delete()

        answer = f"**Search Results for '{args}':**\n\n"
        for index, msg in enumerate(search_results, start=1):
            answer += f"✅ **Result {index}:** {msg.text.splitlines()[0]}\n\n"

        answer += f"\n\n**Uploaded By @{Config.UPDATES_CHANNEL_USERNAME}**"
        
        newbutton = [Button.url('How To Watch ❓', f'https://t.me/postsearchbot?start=Watch')]

        await txt.delete()
        result = await event.reply(answer, buttons=newbutton, link_preview=False)
        await asyncio.sleep(Config.AUTO_DELETE_TIME)
        return await result.delete()

    except Exception as e:
        print(f"Error: {e}")

async def escape_url(string):
    return urllib.parse.quote(string)

async def main():
    await client.start()
    await tbot.start()
    print("\n-------------------- Bot Started Successfully --------------------\n")
    await tbot.run_until_disconnected()
    await client.run_until_disconnected()

if __name__ == "__main__":
    # Start Pyrogram Bot
    Bot.start()

    print(f"""
 _____________________________________________   
|                                             |  
|          Deployed Successfully              |  
|              Join @{Config.UPDATES_CHANNEL_USERNAME}                 |
|_____________________________________________|
    """)

    asyncio.run(main())

    print("\n------------------------ Stopped Services ------------------------")
    Bot.stop()
    
