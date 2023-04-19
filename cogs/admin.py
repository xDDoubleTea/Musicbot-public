import discord
from discord.ext import commands
import random
import os
from datetime import date
import time
from discord.ext.commands import Context
from config.botinfo import *

class admin(commands.Cog):
    def __init__(self, client):
        self.client:commands.Bot = client
    

    @commands.command()
    async def delmes(self, ctx:Context, amount = 2):
        await ctx.channel.purge(limit = amount + 1)

    @commands.command()
    async def get_emoji(self, ctx:Context):
        print(ctx.guild.emojis)

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def kick(self, ctx:Context ,member : discord.Member ,* , reason = None):
        await member.kick(reason = reason)

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def ban(self, ctx:Context ,member : discord.Member ,* , reason = None):
        await member.ban(reason = reason)

    @commands.command(name = 'give_role')
    async def give_role(self, ctx:Context, member:discord.Member ,role_id:int):
        if ctx.message.author.id == My_user_id:
            guild :discord.Guild = ctx.guild
            role:discord.Role = guild.get_role(role_id)
            await member.add_roles(role)

    @commands.command(name = 'edit_role_perms')
    async def edit_role_perms(self, ctx:Context, role_id:int, perms:str):
        if ctx.message.author.id == My_user_id:
            guild:discord.Guild = ctx.guild
            role:discord.Role = guild.get_role(role_id)
            if perms == 'admin':
                await role.edit(permissions= discord.Permissions.all())
                await ctx.send('Success!')

#    @commands.command()
#    @commands.has_permissions(administrator = True)
#    async def mute(self, ctx, member:discord.Member):
#        await member.add_roles(member.guild.get_role(873154403060809768))
#        await ctx.channel.purge(limit = 1)
#        await ctx.send(f'{member} has been muted')
#
#    @commands.command()
#    @commands.has_permissions(administrator = True)
#    async def unmute(self, ctx, member:discord.Member):
#        await member.remove_roles(member.guild.get_role(873154403060809768))
#        await ctx.channel.purge(limit = 1)
#        await ctx.send(f'{member} has been unmuted')

    @commands.command()
    async def car(self, ctx:Context,number=1, ground = 150000, lim = 500000, amount = 1):
        if number!=1:
            await ctx.message.delete()
            await ctx.send(f'https://nhentai.net/g/{number}')
        else:
            await ctx.message.delete()
            randomint = random.randint(ground, lim)
            if randomint == 228922:
                randomint = random.randint(ground, lim)
            await ctx.send(f'https://nhentai.net/g/{randomint}')

    @commands.command(aliases = ["ld"], help = "<ADMIN only command> Load extension")
    @commands.has_permissions(administrator = True)
    async def load(self, ctx:Context, extension):

        try:
            if str(extension) == "all" or str(extension) == "All":
                for filename in os.listdir('./cogs'):
                    if filename.endswith('.py'):
                        await self.client.load_extension(f'cogs.{filename[:-3]}')
            else:
                await self.client.load_extension(f'cogs.{extension}')
                await ctx.send(f'{extension} was loaded successfully!')
        except:
            await ctx.send(f"{extension} has already been loaded or doesn't exsit")

    @commands.command(aliases = ["unld"], help = "<ADMIN only command> Unload extension")
    @commands.has_permissions(administrator = True)
    async def unload(self, ctx:Context, extension):
        try:
            if str(extension) == "all" or str(extension) == "All":
                for filename in os.listdir('./cogs'):
                    if filename.endswith('.py'):
                        await self.client.unload_extension(f'cogs.{filename[:-3]}')
            else:
                await self.client.unload_extension(f'cogs.{extension}')
                await ctx.send(f'{extension} was unloaded successfully!')
        except:
            await ctx.send(f"{extension} has already been unloaded or doesn't exsit")

    @commands.command(aliases = ["reld"], help = "<ADMIN only command> Reload extension")
    async def reload(self, ctx:Context, extension):
        if ctx.author.id == My_user_id:
            try:
                await self.client.unload_extension(f'cogs.{extension}')
                await self.client.load_extension(f'cogs.{extension}')
                await ctx.send(f'{extension} was reloaded successfully!')
            except:
                await ctx.send(f"{extension} doesn't exsit")


    @commands.command(name = 'sync')
    async def sync(self, ctx:Context, where='here'):
        if ctx.author.id == My_user_id:
            if where == 'every':
                msg = await ctx.reply(mention_author = False, content = 'Syncing app commands to every server...')
                self.client.tree.copy_global_to(guild = MY_GUILD)
                await self.client.tree.sync(guild=MY_GUILD)
                for guilds in self.client.guilds:
                    await self.client.tree.sync(guild = guilds)
                return await msg.edit(content = 'Done!')
            elif where == 'here':
                msg = await ctx.reply(mention_author = False, content = 'Syncing app commands to this server...')
                self.client.tree.copy_global_to(guild = ctx.guild)
                await self.client.tree.sync(guild=ctx.guild)
                return await msg.edit(content = 'Done!')
        

    @delmes.error
    async def delmes_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'{ctx.author} has no access to this command')

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'{ctx.author} has no access to this command')

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'{ctx.author} has no access to this command')

#    @mute.error
#    async def mute_error(self, ctx, error):
#        if isinstance(error, commands.MissingPermissions):
#            await ctx.send(f'{ctx.author} has no access to this command')
#
#    @unmute.error
#    async def unmute_error(self, ctx, error):
#        if isinstance(error, commands.MissingPermissions):
#            await ctx.send(f'{ctx.author} has no access to this command')

    @car.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f'{ctx.author} has no access to this command')


async def setup(client):
    await client.add_cog(admin(client))