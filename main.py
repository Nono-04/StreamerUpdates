import os

import twitchio
from discord_webhook import AsyncDiscordWebhook
from dotenv import load_dotenv
from twitchio.ext import eventsub, commands, routines

load_dotenv()
streamer = os.getenv('STREAMER')
streamerInChat = str(os.getenv('STREAMER_IN_CHAT')).split(',')
friendsInChat = str(os.getenv('FRIENDS_IN_CHAT')).split(',')

chatMessagesWebhook = os.getenv('CHAT_MESSAGES_WEBHOOK')
otherStreamerWebhook = os.getenv('OTHER_STREAMERS_WEBHOOK')
streamerInOtherChatWebhook = os.getenv('STREAMER_IN_OTHER_CHAT_WEBHOOK')
friendsInChatWebhook = os.getenv('FRIENDS_CHAT_WEBHOOK')

accessToken = "sdgf0yaagyx1umwjlbb7syh0czexb4"
clientSecret = "8l1g01lh2go6xmeopu9ytck2tbwve4"

oldData = {
    "title": None,
    "game": None,
    "live": None,
}

async def send_embed_webhook(webhook, title: str, description: str, color: int):
    hook = AsyncDiscordWebhook(url=webhook, embeds=[{"title": title, "description": description, "color": color}], rate_limit_retry=True)
    await hook.execute()


async def send_message_webhook(webhook, message: str, username="", avatar_url: str = ""):
    hook = AsyncDiscordWebhook(url=webhook, content=message, username=username, avatar_url=avatar_url, rate_limit_retry=True)
    await hook.execute()


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

        message.content = message.content.replace("@everyone", "<@122534190754299905>")
        message.content = message.content.replace("@here", "<@122534190754299905>")

        if message.author.name.lower() == streamer.lower():
            avatar = (await message.author.user()).profile_image
            if message.channel.name.lower() == streamer.lower():
                await send_message_webhook(chatMessagesWebhook, f"{message.content}",
                                           username=message.author.display_name, avatar_url=avatar)
            else:
                await send_message_webhook(streamerInOtherChatWebhook, f"{message.channel.name}: {message.content}",
                                           username=message.author.name, avatar_url=avatar)

        if message.channel.name.lower() == streamer.lower():
            if message.author.name.lower() in streamerInChat:
                avatar = (await message.author.user()).profile_image
                await send_message_webhook(otherStreamerWebhook, f"{message.content}",
                                           username=message.author.display_name, avatar_url=avatar)

            elif message.author.name.lower() in friendsInChat:
                avatar = (await message.author.user()).profile_image
                await send_message_webhook(friendsInChatWebhook, f"{message.content}",
                                           username=message.author.display_name, avatar_url=avatar)

    @routines.routine(seconds=30)
    async def check_stream(self):
        streamerData = await self.fetch_channel(streamer)
        livestreamData = await self.fetch_streams(user_logins=[streamer])
        if len(livestreamData) != 0:
            livestreamData = livestreamData[0]
            if not isinstance(livestreamData, twitchio.Stream):
                return

            isCurrentlyLive = livestreamData.type == "live" and livestreamData.viewer_count > 0 and livestreamData.started_at is not None

            if oldData["live"] is None:
                oldData["live"] = isCurrentlyLive

            if oldData["live"] != isCurrentlyLive:
                if livestreamData.type == "live":
                    try:
                        await send_embed_webhook(chatMessagesWebhook, "Stream started", f"{streamer} is live!", 0x00ff00)
                        await send_message_webhook(chatMessagesWebhook, f"{livestreamData.thumbnail_url.replace('{width}', '1920').replace('{height}', '1080')}")
                    except Exception as e:
                        print(e)
                        pass
                else:
                    try:
                        await send_embed_webhook(chatMessagesWebhook, "Stream ended", f"{streamer} is offline!", 0xff0000)
                    except Exception as e:
                        print(e)
                        pass
                oldData["live"] = isCurrentlyLive

        if oldData.get("title") is None:
            oldData["title"] = streamerData.title

        if oldData.get("game") is None:
            oldData["game"] = streamerData.game_name

        if oldData.get("title") != streamerData.title:
            try:
                await send_embed_webhook(chatMessagesWebhook, "Title changed",
                                         f"Old title: {oldData['title']}\nNew title: {streamerData.title}", 0x00ff00)
            except:
                pass
            oldData["title"] = streamerData.title

        if oldData.get("game") != streamerData.game_name:
            try:
                await send_embed_webhook(chatMessagesWebhook, "Game changed", f"New game: {streamerData.game_name}",
                                         0x00ff00)
            except:
                pass
            oldData["game"] = streamerData.game_name


bot = Bot()
bot.check_stream.start(stop_on_error=False)
bot.run()
