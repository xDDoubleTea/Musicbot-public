import discord
import json

bot_token = "token"
app_id = 1090294854988337232
MY_GUILD = discord.Object(id = 1039906085626196079)
My_user_id = 398444155132575756

PLAY = "<:play:1093697524403015811>"
PAUSE = "<:pause:1093697559165411491>"
FORWARD = "<:forward:1093697584473849876>"
REWIND = "<:rewind:1093697607781589043>"
SHUFFLE = "<:shuffle:1093704399777439856>"
LOOP = "<:loop:1093705686019485798>"
STOP = "<:stop:1095274936072949781>"

async def get_embed(client:discord.Client, title:str, desc:str=None):
    embed = discord.Embed(
        title = title,
        description = desc,
        color=discord.Colour.blue()
    )
    dev = client.get_user(My_user_id)
    embed.set_author(name = client.user.name, icon_url = client.user.avatar.url)
    embed.set_footer(text = f'Developed by {dev.name}', icon_url = dev.avatar.url)
    return embed