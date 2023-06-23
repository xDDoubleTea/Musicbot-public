import discord
from discord.ext import commands
import os
from config.botinfo import MY_GUILD, bot_token

intents = discord.Intents.all()

class Musicbot(commands.Bot):
    def __init__(self,*,intents:discord.Intents):
        super().__init__(command_prefix='?', help_command=None, intents=intents)
    
    async def setup_hook(self):
        for files in os.listdir('./cogs'):
            if files.endswith('.py'):
                await self.load_extension(f'cogs.{files[:-3]}')

client = Musicbot(intents=intents)

@client.event
async def on_ready():
    client.tree.copy_global_to(guild = MY_GUILD)
    await client.tree.sync(guild = MY_GUILD)
    print(f'Bot is ready {client.user}')
    return await client.change_presence(status = discord.Status.idle, activity = discord.Game(name = 'HI'))

client.run(bot_token)
