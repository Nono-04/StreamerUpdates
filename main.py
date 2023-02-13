import os

from discord_webhook import AsyncDiscordWebhook
from dotenv import load_dotenv
from twitchio.ext import commands

load_dotenv()
streamer = os.getenv('STREAMER')
streamerInChat = str(os.getenv('STREAMER_IN_CHAT')).split(',')
chatMessagesWebhook = os.getenv('CHAT_MESSAGES_WEBHOOK')
otherStreamerWebhook = os.getenv('OTHER_STREAMERS_WEBHOOK')
accessToken = "sdgf0yaagyx1umwjlbb7syh0czexb4"
clientSecret = "8l1g01lh2go6xmeopu9ytck2tbwve4"

async def send_embed_webhook(webhook, title: str, description: str, color: int):
    hook = AsyncDiscordWebhook(url=webhook, embeds=[{"title": title, "description": description, "color": color}])
    await hook.execute()


async def send_message_webhook(webhook, message: str):
    hook = AsyncDiscordWebhook(url=webhook, content=message)
    await hook.execute()

oldData = {
    "title": "",
    "game": "",
    "live": None,
}

class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token=accessToken, initial_channels=[streamer], prefix="yourmom!", client_secret=clientSecret)

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        print("Joining other channels...")
        await self.join_channels(streamerInChat)

    async def event_message(self, message):
        if message.echo:
            return

        if message.author.name.lower() == streamer.lower():
            if message.channel.name.lower() != streamer.lower():
                await send_message_webhook(otherStreamerWebhook, f"{message.author.name}: {message.content}")
            else:
                await send_message_webhook(chatMessagesWebhook, f"{message.content}")

        if message.author.name.lower() in streamerInChat:
            await send_message_webhook(otherStreamerWebhook, f"{message.author.name}: {message.content}")

    async def subscribe_channel_update(self, data):
        if oldData["title"] == "":
            oldData["title"] = data.title
        if oldData["game"] == "":
            oldData["game"] = data.category_name

        if oldData["title"] != data.title:
            await send_embed_webhook(otherStreamerWebhook, f"{data.broadcaster_name} changed their title!",
                                     f"**Old Title:** {oldData['title']}\n**New Title:** {data.title}", 0x00ff00)
            oldData["title"] = data.title

        if oldData["game"] != data.category_name:
            await send_embed_webhook(otherStreamerWebhook, f"{data.broadcaster_name} changed their game!",
                                     f"**Old Game:** {oldData['game']}\n**New Game:** {data.category_name}", 0x00ff00)
            oldData["game"] = data.category_name

    async def subscribe_stream_online(self, data):
        if data.broadcaster.name.lower() != streamer.lower():
            return

        if oldData["live"] == None:
            oldData["live"] = data.type

        if data.type == "live" and oldData["live"] != data.type:
            await send_embed_webhook(otherStreamerWebhook, f"{data.broadcaster_name} is now live!",
                                     f"**Game:** {data.category_name}\n**Title:** {data.title}", 0x00ff00)
            oldData["live"] = data.type


bot = Bot()
bot.run()
