import discord
from pathlib import Path
from settings import DISCORD_API_KEY, DISCORD_CHANNEL_ID, RESULTS_DIR


def send_message(msg: str) -> bool:
    if DISCORD_API_KEY is None or DISCORD_CHANNEL_ID is None:
        return False
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(int(DISCORD_CHANNEL_ID))
        await channel.send(msg)
        if RESULTS_DIR:
            await channel.send(file=discord.File(Path(RESULTS_DIR) / "valuations.png"))
            await channel.send(file=discord.File(f"{Path(RESULTS_DIR).name}.zip"))
        await client.close()

    client.run(DISCORD_API_KEY)
    return True
