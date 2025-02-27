import re
from configs import Config
import json
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from TeamTeleRoid.database import db
import requests

# Async Iter Helper Class
class AsyncIter:    
    def __init__(self, items):    
        self.items = items    

    async def __aiter__(self):    
        for item in self.items:    
            yield item    

#####################  Make link to hyperlink (Fixed) ####################
async def link_to_hyperlink(string):
    # Extract all links
    http_links = await extract_link(string)
    
    # Replace only the raw links with hyperlinked format
    for link in http_links:
        if f"[{link}]({link})" not in string:  # Prevent duplicate replacements
            string = string.replace(link, f"[{link}]({link})")
    
    return string


async def extract_link(string):
    """
    Extracts all URLs from a given text
    """
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
    return urls

##################### Validate Query ####################
async def validate_q(q):
    query = q.strip()
    
    # Check if length is too short
    if len(query) < 2:
        return False

    # Disallow certain characters and links
    if re.findall(r"((^\/|^,|^:|^\.|^[\U0001F600-\U000E007F]).*)", query) or ("https://" in query or "http://" in query):
        return False

    # Remove unnecessary words
    query = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|gib)(\sme)?)|new|hd|||dedo|print|fulllatest|br((o|u)h?)*um(o)*|aya((um(o)*)?|any(one)|with\ssk)*ubtitle(s)?)", "", query.lower(), flags=re.IGNORECASE)
    
    return query.strip()


##################### Main Converter Handler ####################
async def main_convertor_handler(c: Client, message: Message, type: str, edit_caption: bool = False):
    METHODS = {
        "mdisk": replace_mdisk_link,
    }

    user_method = type
    method_func = METHODS.get(user_method, None)

    if not method_func:
        return await message.reply_text("Invalid conversion type!")

    # If message has buttons (reply_markup)
    if message.reply_markup:
        txt = str(message.text or message.caption or "")
        reply_markup = json.loads(str(message.reply_markup))
        buttons = []

        for markup in reply_markup["inline_keyboard"]:
            button_row = []
            for button in markup:
                text = button["text"]
                url = button["url"]
                url = await method_func(url)  # Convert URL
                button_row.append(InlineKeyboardButton(text, url=url))
            buttons.append(button_row)

        # Convert text links
        txt = await method_func(txt)

        # Edit or reply based on the message type
        if edit_caption:
            return await message.edit_caption(txt, reply_markup=InlineKeyboardMarkup(buttons))

        if message.text:
            await message.reply(text=txt, reply_markup=InlineKeyboardMarkup(buttons))
        elif message.photo:
            await message.reply_photo(photo=message.photo.file_id, caption=txt, reply_markup=InlineKeyboardMarkup(buttons))
        elif message.document:
            await message.reply_document(document=message.document.file_id, caption=txt, reply_markup=InlineKeyboardMarkup(buttons))

    # If message is a plain text message
    elif message.text:
        link = await method_func(message.text)
        if edit_caption:
            return await message.edit(f"{link}")
        await message.reply_text(f"**{link}**")

    # If message contains media
    elif message.photo:
        fileid = message.photo.file_id
        text = await method_func(message.caption or "")
        if edit_caption:
            return await message.edit_caption(f"{text}")
        await message.reply_photo(fileid, caption=f"{text}")

    elif message.document:
        fileid = message.document.file_id
        text = await method_func(message.caption or "")
        if edit_caption:
            return await message.edit_caption(f"{text}")
        await message.reply_document(fileid, caption=f"{text}")


##################### Make Bold Function ####################
async def make_bold(string):
    string = string.replace("<p>", "<p><strong>").replace("</p>", "</strong></p>")
    string = string.replace("<h1>", "<p><strong>").replace("</h1>", "</strong></p>")
    return string


##################### Mdisk Convertor (Fixed) ####################
async def get_mdisk(link, api=Config.MDISK_API):
    url = 'https://diskuploader.mypowerdisk.com/v1/tp/cp'
    param = {'token': api, 'link': link}
    res = requests.post(url, json=param)

    try:
        shareLink = res.json()
        return shareLink.get("sharelink", link)  # Return the new link if available
    except:
        return link  # If any error, return the original link

async def replace_mdisk_link(text, api=Config.MDISK_API):
    links = re.findall(r'https?://mdisk.me[^\s]+', text)
    for link in links:
        mdisk_link = await get_mdisk(link, api)
        text = text.replace(link, mdisk_link)
    return text


##################### Group Link Convertor ####################
async def group_link_convertor(group_id, text):
    api = await db.get_api_id(group_id)
    if api:
        return await replace_mdisk_link(text, str(api['api']))
    return text
	
