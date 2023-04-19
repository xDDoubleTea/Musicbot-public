from datetime import datetime
import math
import time
import discord
from typing import List,  Dict, Union
from discord.ext import commands
from discord import  FFmpegPCMAudio,  Guild,VoiceChannel, User, app_commands, Interaction,VoiceClient, Client, TextChannel, ButtonStyle
from discord.ext.commands import Context
from discord.ui import View, button, Button
import yt_dlp
import os
from discord.ext import tasks
from typing import Optional
from config.botinfo import get_embed, My_user_id, PLAY, REWIND, PAUSE, FORWARD, SHUFFLE, LOOP, STOP
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
import threading
from view.Page_turning_ui import PageTurningSys
import random

class VidNotFound(Exception):
    def __init__(self):
        super().__init__()

class VolumeError(Exception):
    def __init__(self):
        super().__init__()

def TrueFalseToWord(test):
    if test:
        return "開啟"
    else:
        return "關閉"

class music(commands.Cog):
    def __init__(self, client):
        self.client:commands.Bot = client
        self.vcs:List[Dict[str, VoiceClient, Guild, MusicPlayer]] = []        
        self.music_control:Union[int, Music_control] = 0

    def get_vc_in_guild(self, guild):
        has_vc = False
        return_vc = None
        for vc in self.vcs:
            if vc["guild"] == guild:
                has_vc = True
                return_vc = vc
                break
        return (has_vc, return_vc)

    async def dconnect(self, guild:Guild):
        done = False
        dc = 0
        for vc in self.vcs:
            voice:VoiceClient = vc["voice_client"]
            if vc["guild"] == guild:
                dc = vc
                voice.cleanup()
                await voice.disconnect()
                done = True
                self.vcs.remove(dc)
                await asyncio.sleep(1)
                for files in os.listdir('.\\songs'):
                    os.remove(f".\\songs\\{files}")
        if guild.voice_client != None:
            await guild.voice_client.disconnect()
            done = True
        return done

    async def join_channel(self, voice_channel:VoiceChannel, text_channel:TextChannel):
        vc = await voice_channel.connect(timeout = 3600, reconnect=True, self_deaf=True)
        player = MusicPlayer(client = self.client, voice_client=vc, cmd_channel=text_channel, main = self)
        self.vcs.append({"voice_client":vc, "guild":text_channel.guild, "player":player})
        return (vc, player)

    @commands.command(name = 'music', aliases = ['m'])
    async def music(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc:
            msg = await ctx.send(embed = await get_embed(client = self.client, title = 'Loading...'))
            view = Music_control(main = self, player = vc["player"], guild = ctx.guild, voice_client=vc["voice_client"], attached_msg=msg)
            self.music_control = view
            embed = await view.new_embed(client = self.client)
            await msg.edit(embed = embed ,view = view)
        else:
            return await ctx.send('還未加入語音頻道！')


    @app_commands.command(name='connect', description='Connects to voice channel')
    async def join(self, interaction:Interaction, channel:Optional[VoiceChannel]):
        if channel == None and interaction.user.voice == None:
            return await interaction.response.send_message('請加入某語音頻道或指定語音頻道讓機器人加入。',ephemeral=True)

        if channel == None:
            channel = interaction.user.voice.channel
        has_vc, vc = self.get_vc_in_guild(guild = interaction.guild)
        text_channel = interaction.channel
        if has_vc and vc["voice_client"].channel != channel:
            await vc["voice_client"].move_to(channel)
            return await interaction.response.send_message(f'已連接語音！\n頻道：{channel.mention}\n發送訊息使用者：{interaction.user.display_name}', ephemeral=True)
        elif has_vc and vc["voice_client"].channel == channel:
            return await interaction.response.send_message('已經連接到此語音頻道！',ephemeral=True)
        elif not has_vc:
            vc, player = await self.join_channel(voice_channel=channel, text_channel = text_channel)
            await interaction.response.send_message(f'已連接語音！\n頻道：{channel.mention}\n發送訊息使用者：{interaction.user.display_name}', ephemeral=True)
            return 
        else:return
            
    
    @app_commands.command(name = 'disconnect', description='Disconnects from a voice channel')
    async def dis(self, interaction:Interaction):
        done = await self.dconnect(guild = interaction.guild)
        if not done:
            return await interaction.response.send_message('未連接至語音頻道！',ephemeral=True)
        else:
            return await interaction.response.send_message('已斷開連接！',ephemeral=True)

    @commands.command(name = 'play')
    async def play(self, ctx:Context, link=""):
        async with ctx.channel.typing():
            if link == "":
                return await ctx.send('請提供youtube影片的連結！')
            other_vids_dl:List[threading.Thread] = []
            has_vc , vc = self.get_vc_in_guild(guild = ctx.guild)
            msg = discord.Message
            player =0
            song_name = ""
            if has_vc and (vc["voice_client"].is_playing() or vc["voice_client"].is_paused()):
                if "playlist" in link:
                    player:MusicPlayer = vc["player"]
                    links:list = await player.get_playlist_vid_url_list(link)

                    other_vids_dl = []       
                    for li in links:
                        t = threading.Thread(target=get_other_vids, args=(player, ctx.author, li))
                        other_vids_dl.append(t)
                    await ctx.send(f'將{len(other_vids_dl)}首歌曲加入歌單！')
                else:
                    player:MusicPlayer = vc["player"]
                    try:
                        song_name , thumbnail_url ,desc ,local_path= await player.single_vid(vc = vc, author = ctx.author, link = link)
                    except VidNotFound:
                        return await ctx.send('影片連結有誤！請再檢查一次！')
                    embed = await get_embed(client = self.client, title = '✅歌曲加入歌單！', desc = f'**加入歌曲：**\n{song_name}')
                    await ctx.send(embed=embed)
            elif has_vc and vc["voice_client"].is_connected():
                player:MusicPlayer = vc["player"]
                if 'playlist' in link:
                    other_vids_dl = await player.get_playlist_first_vid(vc = vc, author = ctx.author, link = link)
                    player.play_source(voice_client=vc["voice_client"])
                else:
                    try:
                        await player.single_vid(vc = vc, author = ctx.author, link = link)
                    except VidNotFound:
                        return await ctx.send('影片連結有誤！請再檢查一次！')

                player.play_source(voice_client=vc["voice_client"])
                await ctx.send(embed = await player.get_now_playing_embed())            
            else:
                if ctx.author.voice == None:
                    return await ctx.send('請加入某語音頻道或指定語音頻道讓機器人加入。')

                channel = ctx.channel
                vc, player = await self.join_channel(voice_channel=ctx.author.voice.channel, text_channel = channel)
                if 'playlist' in link:
                    vc_pack = {"voice_client":vc, "player":player}
                    msg = await ctx.send('Loading vidoes...')
                    other_vids_dl = await player.get_playlist_first_vid(vc=vc_pack, author = ctx.author, link = link)
                    await msg.delete()
                else:
                    try:
                        song_name , thumbnail_url,desc ,duration,local_path = player.get_vid(link = link)
                        player.queue.append({"user":ctx.author, "song_name":song_name, "yt_url":link,"thumbnail_url":thumbnail_url ,"desc":desc,"duration":duration, "local_path":local_path})
                    except VidNotFound:
                        return await ctx.send('影片連結有誤！請再檢查一次！')
                    except:
                        return await ctx.send('發生了神奇的錯誤！')
                player.play_source(voice_client=vc)
                await ctx.send(embed = await player.get_now_playing_embed())
            for i in other_vids_dl:
                i.start()
            
    @commands.command(name='pause')
    async def pause(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and vc["voice_client"].is_playing():
            vc["voice_client"].pause()
            return await ctx.send('已將播放中的音樂暫停！')
        elif has_vc and vc["voice_client"].is_paused():
            return await ctx.send('音樂已經是暫停的狀態了，使用?resume來繼續播放。')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')
        
    @commands.command(name='resume', aliases = ['res'])
    async def resume(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and vc["voice_client"].is_paused():
            vc["voice_client"].resume()
            return await ctx.send('繼續播放音樂！')
        elif has_vc and vc["voice_client"].is_playing():
            return await ctx.send('音樂已經正在播放的狀態了')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')

    @commands.command(name = 'now_playing', aliases =['np'])
    async def now_playing(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            return await ctx.send(embed = await player.get_now_playing_embed())
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')
        
    @commands.command(name = 'queue', aliases = ['q'])
    async def queue(self, ctx:Context):
        has_vc , vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            embed, page_data = await player.get_queue_embed()
            embed.description = 'Loading...'
            msg = await ctx.send(embed = embed)
            view = PageTurningSys(data = page_data, attached_msg=msg)
            embed = await view.new_page(client = self.client)
            embed.set_footer(text=f"Developed by {self.client.get_user(My_user_id).name}", icon_url=embed.footer.icon_url)
            embed.description = f"**Queue length: **{len(page_data)}\n**Loop: **{player.loop}\n**Now Playing song: **({player.now_playing_idx+1}){player.queue[player.now_playing_idx]['song_name']}"
            new_msg = await msg.edit(embed = embed, view = view)
            view.attached_msg = new_msg
            return 
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')

    @commands.command(name = 'stop')
    async def stop(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc:
            done = await self.dconnect(guild = ctx.guild)
            if not done:
                return await ctx.send('未連接至語音頻道！')
            else:
                return await ctx.send('已斷開連接！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')

    @commands.command(name = 'loop')
    async def loop(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            if player.loop:
                player.loop = False
            else:
                player.loop = True
            return await ctx.send(f'將循環播放設定為{TrueFalseToWord(test = player.loop)}')
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')
        
    @commands.command(name = 'next', aliases = ['skip'])
    async def next(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            org_song = player.song_idx
            player.vc.stop()
            now_song = player.song_idx
            if now_song - org_song != 0:
                return await ctx.send('已跳過目前歌曲！')
            else:
                await ctx.send('已經是最後一首了！')
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')
        
    @commands.command(name = 'prev', aliases = ['last'])
    async def prev(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            org_song = player.song_idx
            player.vc.pause()
            player.prev_song()
            now_song = player.song_idx
            if now_song - org_song != 0:
                await ctx.send('已回到上一首歌曲！')
                return await ctx.send(embed = await player.get_now_playing_embed())
            else:
                await ctx.send('已經是第一首了！')
                player.vc.resume()
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')
        
    @commands.command(name = 'shuffle', aliases = ['random'])
    async def shuffle(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            new_queue = []
            new_queue.append(player.queue[player.now_playing_idx])
            player.queue.pop(player.now_playing_idx)
            random.shuffle(player.queue)
            player.queue = new_queue + player.queue
            player.song_idx = 0
            player.now_playing_idx = 0
            await ctx.send('已隨機排序歌曲！')
            embed , page_data = await player.get_queue_embed()
            embed.description = 'Loading...'
            msg = await ctx.send(embed = embed)
            view = PageTurningSys(data = page_data, attached_msg=msg)
            embed = await view.new_page(client = self.client)
            embed.set_footer(text=f"Developed by {self.client.get_user(My_user_id).name}", icon_url=embed.footer.icon_url)
            embed.description = f"**Queue length: **{len(page_data)}\n**Loop: **{player.loop}\n**Now Playing song: **({player.now_playing_idx+1}){player.queue[player.now_playing_idx]['song_name']}"
            new_msg = await msg.edit(embed = embed, view = view)
            view.attached_msg = new_msg
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')

    @commands.command(name = 'volume', aliases = ['vol'])
    async def volume(self, ctx:Context, volume:str):
        try:
            volume = int(volume)
            if volume <= 1 or volume > 100:
                raise VolumeError
        except ValueError:
            return await ctx.send('請輸入數字！')
        except VolumeError:
            return await ctx.send('請輸入1~100間的數字')

        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            player.set_volume(volume = volume)
            return await ctx.send(f'音量已調整為{volume}%')
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')
    @commands.command(name = 'remove')
    async def remove(self, ctx:Context, index:str):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc and (vc["voice_client"].is_paused() or vc["voice_client"].is_playing()):
            player:MusicPlayer = vc["player"]
            try:
                index = int(index)
                if index < 1 or index > len(player.queue):
                    raise ValueError
                index -=1
            except:
                return await ctx.send(f'請輸入1~{len(player.queue)}')
            if index == player.now_playing_idx:
                return await ctx.send('請等到播放完畢後再移除！')
            popped_song = player.queue[index]["song_name"]
            song_url = player.queue[index]["yt_url"]
            local_path = player.queue[index]["local_path"]
            os.remove(local_path)
            player.queue.pop(index)
            embed = await get_embed(client = self.client, title = f'移除了{popped_song}', desc=f'**影片連結：**{song_url}')
            return await ctx.send(embed = embed)
        elif has_vc and vc["voice_client"].is_connected():
            return await ctx.send('沒有在播放音樂，使用?play來加入音樂！')
        else:
            return await ctx.send('還沒有連結到任何語音頻道！')

    @commands.command(name = 'output_queue', aliases = ['out_q'])
    async def output_queue(self, ctx:Context):
        has_vc, vc = self.get_vc_in_guild(guild = ctx.guild)
        if has_vc:
            player:MusicPlayer = vc["player"]
            if len(player.queue) == 0:
                return await ctx.send('沒有在播放音樂')
            write_data = '------\n'     
            write_data += f'檔案開始生成時間：{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}\n'
            for i,song in enumerate(player.queue):
                name = song["song_name"]
                url = song["yt_url"]
                write_data += f"{i+1}. Song Name:{name}\nurl: {url}\n\n"

            with open('Queue.txt', 'w', encoding='utf-8') as file:
                file.write(str(write_data))
                file.close()

            with open('Queue.txt', 'rb') as file:
                result = discord.File(fp = file, filename = 'Queue.txt')
                await ctx.send(file = result)
            return os.remove("Queue.txt")
        else:
            return await ctx.send('沒有在播放音樂')

class MusicPlayer:
    def __init__(self, main:music ,client:Client, voice_client:VoiceClient, cmd_channel:TextChannel):
        self.queue:List[Dict[User,str, str, str]] = []
        #user, song_name, yturl, thumbnail_url, local path
        self.loop = False
        self.main = main
        self.client:Client = client
        self.vc:VoiceClient = voice_client
        self.song_idx = 0
        self.now_playing_idx = 0
        self.cmd_channel:TextChannel = cmd_channel
        self.org_source = self.vc.source
        self.volume = 1
        self.time_elapse = -10

    @tasks.loop(seconds = 10)
    async def update_time_elapse(self):
        duration = self.queue[self.now_playing_idx]["duration"]
        duration = duration.split(':')
        if len(duration) == 2:
            #means no hour
            minute = int(duration[0])
            second = int(duration[1])
            duration = minute*60+second
        elif len(duration) == 3:
            hour = int(duration[0])
            minute = int(duration[1])
            second = int(duration[2])
            duration = hour*3600+minute*60+second
        if duration - self.time_elapse > 10:
            self.time_elapse += 10
        else:
            self.time_elapse = duration-1
        if self.main.music_control != 0:
            new_embed = await self.main.music_control.new_embed(client = self.main.client)
            if self.time_elapse > 0:
                new_name = f"{self.seconds_to_h_m_s(duration = self.time_elapse)}/{self.queue[self.now_playing_idx]['duration']}"
            else:
                new_name = f"00:00/{self.queue[self.now_playing_idx]['duration']}"
            new_embed.add_field(name = f'🎵{new_name}', value = self.main.music_control.get_progress_bar())
            self.main.music_control.attached_msg = await self.main.music_control.attached_msg.edit(embed= new_embed)
    
    async def get_now_playing_embed(self):
        desc = self.queue[self.now_playing_idx]["desc"]
        embed = await get_embed(client = self.client, title=f'🎶Now Playing🎶\n{self.queue[self.now_playing_idx]["song_name"]}', desc =f'**影片長度：**{self.queue[self.now_playing_idx]["duration"]}\n**影片說明欄(前150字)：**\n{desc[:150]}...')
        url = self.queue[self.now_playing_idx]["yt_url"]
        thumbnail_url = self.queue[self.now_playing_idx]["thumbnail_url"]
        if url != '':
            embed.url = url
        embed.set_thumbnail(url = thumbnail_url)
        return embed
    
    async def get_queue_embed(self):
        embed = await get_embed(client = self.client, title = '📃Queue list')
        page_data = []
        for idx, song in enumerate(self.queue):
            song_name = song["song_name"]
            user:User = song["user"]
            url = song["yt_url"]
            page_data.append({"name":f'({idx+1}){song_name}',"value":f"{url}, added by {user.mention}"})
        return (embed, page_data)
    
    async def send_now_playing(self):
        embed = await self.get_now_playing_embed()
        await self.cmd_channel.send(embed = embed)
        if self.main.music_control != 0:
            update = await self.main.music_control.new_embed(client = self.client)
            await self.main.music_control.attached_msg.edit(embed = update)

    def get_recommend_select(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options = options, executable_path="C:\\chromedriver.exe")
        driver.get(url)
        time.sleep(0.5)
        links=[]
        titles = []
        xpath = By.XPATH
        elements = driver.find_elements(by = xpath, value = '//*[@class="yt-simple-endpoint style-scope ytd-compact-video-renderer"]')
        for l in elements:
            if l.get_attribute('href') != None and ("radio" not in l.get_attribute('href')) and ("shorts" not in l.get_attribute('href')):
                links.append("https://youtu.be/" + l.get_attribute('href').strip('https://www.youtube.com/watch?v')[1:12])
        elements = driver.find_elements(by = xpath , value = '//*[@id="video-title"]')
        for title in elements:
            titles.append(title.get_attribute('title'))
        for i in range(5):
            selectopts = discord.SelectOption(label = titles[i], value = links[i])
        sel = discord.ui.Select(placeholder="推薦影片",options=selectopts)
        return sel

    def set_volume(self, volume):
        if self.vc.source != None:
            self.vc.source.volume = volume/100
            self.volume = volume/100

    def next_song(self):
        if self.song_idx == len(self.queue)-1 and self.loop:
            self.song_idx = 0
            self.now_playing_idx = 0 
        elif self.song_idx == len(self.queue)-1 and not self.loop:
            return
        else:
            self.song_idx += 1
            self.now_playing_idx = self.song_idx
        ''' print(self.song_idx)
        print(self.now_playing_idx)'''
        self.time_elapse = -10
        self.play_source(voice_client=self.vc)
        self.client.loop.create_task(self.send_now_playing())
    
    def prev_song(self):
        self.vc.pause()
        if self.song_idx == 0 and self.loop:
            self.song_idx = len(self.queue)-1
            self.now_playing_idx = len(self.queue) -1
        elif self.song_idx == 0 and not self.loop:
            return
        else:
            self.song_idx -= 1
            self.now_playing_idx = self.song_idx
        
        '''print(self.song_idx)
        print(self.now_playing_idx)'''
        self.play_source(voice_client=self.vc)

    def play_source(self,voice_client:VoiceClient):
        source = FFmpegPCMAudio(self.queue[self.song_idx]["local_path"])
        voice_client.play(source, after = lambda e: print('Player error: %s' % e) if e else self.next_song())
        self.vc.source = discord.PCMVolumeTransformer(original=self.vc.source, volume = self.volume)
        if not self.update_time_elapse.is_running():
            self.update_time_elapse.start()
        if self.main.music_control != 0:
            new_view = Music_control(main = self.main, player = self, guild = self.cmd_channel.guild, voice_client=self.vc, attached_msg=self.main.music_control.attached_msg)
            self.client.loop.create_task(self.main.music_control.attached_msg.edit(view = new_view))

    def seconds_to_h_m_s(self, duration):
        hour = math.floor(duration/3600)
        minute = math.floor(duration/60)
        seconds = duration%60
        if hour > 0:
            hour = f"{hour}:"
        else:
            hour = ""
        if minute < 10 and minute > 0:
            minute = f"0{minute}:"
        elif minute == 0:
            minute = "00:"
        else:
            minute = f"{minute}:"
        if seconds == 0:
            seconds = f"00"
        elif seconds < 10 and seconds > 0:
            seconds = f"0{seconds}"
        duration = f"{hour}{minute}{seconds}"
        return duration

    def get_vid(self, link:str):
        options = {
            "outtmpl":".\\songs\\%(title)s.%(ext)s", 
            "format":"mp3/bestaudio",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
            }]
        }
        song_name = ""
        local_path = ""
        try:
            with yt_dlp.YoutubeDL(options) as ytdl:
                vid_info = ytdl.extract_info(url = link, download = True)
                song_name = vid_info["title"]
                thumbnail_url = vid_info["thumbnail"]
                desc = vid_info["description"]
                local_path=vid_info.get("requested_downloads")[0].get("filepath")
                duration = self.seconds_to_h_m_s(vid_info.get("duration"))
        except:
            raise VidNotFound
        return (song_name, thumbnail_url, desc, duration, local_path)


    async def single_vid(self, vc:dict, author:User, link:str):
        try:
            player:MusicPlayer=vc["player"]
            song_name , thumbnail_url,desc,duration ,local_path = player.get_vid(link = link)
            player.queue.append({"user":author, "song_name":song_name, "yt_url":link,"thumbnail_url":thumbnail_url ,"desc":desc,"duration":duration, "local_path":local_path})
        except VidNotFound:
            raise VidNotFound
        return (song_name , thumbnail_url ,desc ,local_path)

    async def get_playlist_vid_url_list(self, link:str):
        links = []
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options = options, executable_path="C:\\chromedriver.exe")
        # 搜尋的網址
        driver.get(link)
        await asyncio.sleep(0.5)
        xpath = By.XPATH
        for link in driver.find_elements(by = xpath, value = '//*[@id="video-title"]'):
            if link.get_attribute('href') != None:
                links.append("https://youtu.be/" + link.get_attribute('href').strip('https://www.youtube.com/watch?v')[1:12])
        driver.quit()
        return links

    async def get_playlist_first_vid(self, vc:dict, author:User, link:str):
        links:list = await self.get_playlist_vid_url_list(link)
        player:MusicPlayer = vc["player"]
        song_name , thumbnail_url,desc, duration, local_path= player.get_vid(links[0])
        player.queue.append({"user":author, "song_name":song_name, "yt_url":links[0],"thumbnail_url":thumbnail_url ,"desc":desc,"duration":duration, "local_path":local_path})
        links.pop(0)
        threads = []        
        for li in links:
            t = threading.Thread(target=get_other_vids, args=(player, author, li))
            threads.append(t)
        return threads

def get_other_vids(player:MusicPlayer, author:User, link:str):
    song_name , thumbnail_url,desc ,duration ,local_path = player.get_vid(link)
    player.queue.append({"user":author, "song_name":song_name, "yt_url":link,"thumbnail_url":thumbnail_url ,"desc":desc,"duration":duration, "local_path":local_path})


class Music_control(View):
    def __init__(self, main:music, player:MusicPlayer, guild:Guild, voice_client:VoiceClient, attached_msg:discord.Message):
        super().__init__(timeout=None)
        self.main = main
        self.player = player
        self.guild = guild
        self.voice_client = voice_client
        self.attached_msg = attached_msg
        if self.player.vc.is_playing() or self.player.vc.is_paused():
            sel = self.player.get_recommend_select(url = self.player.queue[self.player.now_playing_idx]["yt_url"])
            self.add_item(item = sel)
            self.main.client.loop.create_task(self.attached_msg.edit(view=self))
    
    async def on_timeout(self):
        embed = await get_embed(client = self.main.client, title = '請再使用一次?m')
        await self.attached_msg.edit(view = None)
        self.main.music_control = 0

    def get_progress_bar(self):
        duration = self.player.queue[self.player.now_playing_idx]["duration"]
        duration = duration.split(':')
        if len(duration) == 2:
            #means no hour
            minute = int(duration[0])
            second = int(duration[1])
            duration = minute*60+second
        elif len(duration) == 3:
            hour = int(duration[0])
            minute = int(duration[1])
            second = int(duration[2])
            duration = hour*3600+minute*60+second
        ratio = self.player.time_elapse/duration
        length = 25
        initial = "🔴"
        for i in range(length-1):
            initial += '▬'
        if ratio < 0.95:
            idx = math.floor(round(ratio,1)*length)
        else:
            idx = length-1
        new_str = ""
        for i in range(length):
            if i == idx:
                new_str+="🔴"
            else:
                new_str+="▬"
        new_str += '◀'
        tmp = "▶"
        new_str = tmp+new_str
        return new_str

    async def new_embed(self, client):
        embed = await get_embed(client = client, title = '音樂功能')
        status = ""
        await asyncio.sleep(1)
        if self.player.vc.is_playing():
            status = '播放中'
        elif self.player.vc.is_paused():
            status = "暫停中"
        elif self.player.vc.is_connected():
            status = "沒有在播放音樂"
        else:
            status = "已經斷開連結"
        desc = f"播放狀態：{status}\n"
        if self.player.vc.is_playing() or self.player.vc.is_paused():
            now_playing = await self.player.get_now_playing_embed()
            desc += f"目前播放歌曲：[{now_playing.title.splitlines()[1]}]({now_playing.url})\n"
            desc += f"歌單長度：{len(self.player.queue)}\n"
            desc += f"循環播放：{TrueFalseToWord(self.player.loop)}\n"
        embed.description = desc
        return embed

    @button(style=ButtonStyle.red, emoji = PAUSE)
    async def pause(self, interaction:Interaction, button:Button):
        if self.voice_client.is_playing():
            self.voice_client.pause()
            await interaction.message.edit(embed = await self.new_embed(client=interaction.client))
            return await interaction.response.send_message(content=f'音樂已被{interaction.user.display_name}暫停了')
        elif self.voice_client.is_paused():
            return await interaction.response.send_message('音樂已經是暫停的狀態了！', ephemeral=True)
        else:
            return await interaction.response.send_message('沒有在播放音樂', ephemeral=True)

    @button(style=ButtonStyle.red, emoji = STOP)
    async def stop(self, interaction:Interaction, button:Button):
        done = await self.main.dconnect(guild = interaction.guild)
        if not done:
            return await interaction.response.send_message('未連接至語音頻道！', ephemeral=True)
        else:
            await interaction.message.edit(embed = await self.new_embed(client = interaction.client))
            return await interaction.response.send_message('已斷開連接！')

    @button(style = ButtonStyle.green, emoji = PLAY)
    async def resume(self, interaction:Interaction, button:Button):
        if self.voice_client.is_paused():
            self.voice_client.resume()
            await interaction.message.edit(embed = await self.new_embed(client=interaction.client))
            return await interaction.response.send_message(content=f'音樂已被{interaction.user.display_name}繼續播放')
        elif self.voice_client.is_paused():
            return await interaction.response.send_message('音樂已經是播放中的狀態了！', ephemeral=True)
        else:
            return await interaction.response.send_message('沒有在播放音樂', ephemeral=True)
        
    @button(style= ButtonStyle.blurple, emoji = REWIND)
    async def prev(self, interaction:Interaction, button:Button):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            org_song = self.player.song_idx
            self.player.vc.pause()
            self.player.prev_song()
            await asyncio.sleep(0.5)
            now_song = self.player.song_idx
            if now_song - org_song != 0 or (now_song - org_song == 0 and self.player.loop):
                await interaction.message.edit(embed = await self.new_embed(client=interaction.client))
                return await interaction.response.send_message('已回到上一首')
            else:
                return await interaction.response.send_message('已經是第一首了！')
        elif self.voice_client.is_connected():
            return await interaction.response.send_message('沒有在播放音樂，使用?play來加入音樂')
        else:
            return await interaction.response.send_message('還沒有連結到任何語音頻道！')

    @button(style= ButtonStyle.blurple, emoji = FORWARD)
    async def next(self, interaction:Interaction, button:Button):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            org_song = self.player.song_idx
            self.player.vc.stop()
            await asyncio.sleep(0.5)
            now_song = self.player.song_idx
            if now_song - org_song != 0 or (now_song - org_song == 0 and self.player.loop):
                await interaction.message.edit(embed = await self.new_embed(client=interaction.client))
                return await interaction.response.send_message('已跳過目前歌曲！')
            else:
                return await interaction.response.send_message('已經是最後一首了！')

        elif self.voice_client.is_connected():
            return await interaction.response.send_message('沒有在播放音樂，使用?play來加入音樂')
        else:
            return await interaction.response.send_message('還沒有連結到任何語音頻道！')

    @button(style = ButtonStyle.primary, label = '加入語音頻道', emoji = '👋', row = 2)
    async def join(self, interaction:Interaction, button:Button):
        channel = interaction.user.voice.channel
        has_vc, vc = self.main.get_vc_in_guild(guild = interaction.guild)
        text_channel = interaction.channel
        if has_vc and vc["voice_client"].channel != channel:
            await vc["voice_client"].move_to(channel)
            return await interaction.response.send_message(f'已連接語音！\n頻道：{channel.mention}\n發送訊息使用者：{interaction.user.display_name}', ephemeral=True)
        elif has_vc and vc["voice_client"].channel == channel:
            return await interaction.response.send_message('已經連接到此語音頻道！',ephemeral=True)
        elif not has_vc:
            vc, player = await self.main.join_channel(voice_channel=channel, text_channel = text_channel)
            await interaction.response.send_message(f'已連接語音！\n頻道：{channel.mention}\n發送訊息使用者：{interaction.user.display_name}', ephemeral=True)
            return 
        else:return

    @button(style = ButtonStyle.gray, label = '傳送新訊息', row = 2)
    async def new_message(self, interaction:Interaction,button:Button):
        await interaction.response.send_message(embed= await get_embed(client= interaction.client, title = 'Loading...'))
        msg = await interaction.original_response()
        await interaction.message.delete()
        view = Music_control(main = self.main, player = self.player, guild = interaction.guild, voice_client=self.voice_client, attached_msg=msg)
        self.main.music_control = view
        embed = await view.new_embed(client = interaction.client)
        return await msg.edit(embed = embed, view = view)        

    @button(style = ButtonStyle.green, emoji = LOOP)
    async def loop(self, interaction:Interaction, button:Button):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            player:MusicPlayer = self.player
            if player.loop:
                player.loop = False
            else:
                player.loop = True
            await interaction.message.edit(embed = await self.new_embed(client=interaction.client))
            return await interaction.response.send_message(f'將循環播放設定為{TrueFalseToWord(test = player.loop)}')
        elif self.voice_client.is_connected():
            return await interaction.response.send_message('沒有在播放音樂，使用?play來加入音樂')
        else:
            return await interaction.response.send_message('還沒有連結到任何語音頻道！')
        
    @button(style = ButtonStyle.green, emoji = SHUFFLE)
    async def shuffle(self, interaction:Interaction, button:Button):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            player:MusicPlayer = self.player
            new_queue = []
            new_queue.append(player.queue[player.now_playing_idx])
            player.queue.pop(player.now_playing_idx)
            random.shuffle(player.queue)
            player.queue = new_queue + player.queue
            player.song_idx = 0
            player.now_playing_idx = 0
            await interaction.response.send_message('已隨機排序歌曲！')
            embed , page_data = await player.get_queue_embed()
            embed.description = 'Loading...'
            msg = await interaction.channel.send(embed = embed)
            view = PageTurningSys(data = page_data, attached_msg=msg)
            embed = await view.new_page(client = interaction.client)
            embed.set_footer(text=f"Developed by {interaction.client.get_user(My_user_id).name}", icon_url=embed.footer.icon_url)
            embed.description = f"**Queue length: **{len(page_data)}\n**Loop: **{player.loop}\n**Now Playing song: **({player.now_playing_idx+1}){player.queue[player.now_playing_idx]['song_name']}"
            new_msg = await msg.edit(embed = embed, view = view)
            view.attached_msg = new_msg
        elif self.voice_client.is_connected():
            return await interaction.response.send_message('沒有在播放音樂，使用?play來加入音樂')
        else:
            return await interaction.response.send_message('還沒有連結到任何語音頻道！')

    @button(label = "查看歌單",style = ButtonStyle.gray, emoji = '📃', row = 1)
    async def queue(self, interaction:Interaction, button:Button):
        embed, page_data = await self.player.get_queue_embed()
        view = PageTurningSys(data = page_data)
        embed = await view.new_page(client = self.main.client)
        embed.set_footer(text=f"Developed by {self.main.client.get_user(My_user_id).name}", icon_url=embed.footer.icon_url)
        embed.description = f"**Queue length: **{len(page_data)}\n**Loop: **{self.player.loop}\n**Now Playing song: **({self.player.now_playing_idx+1}){self.player.queue[self.player.now_playing_idx]['song_name']}"
        await interaction.response.send_message(embed = embed, view = view)
        view.attached_msg= await interaction.original_response()
        return

async def setup(client):
    await client.add_cog(music(client))