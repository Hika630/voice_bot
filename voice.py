import discord
import json
import requests
import wave
from discord.ext import tasks
import pytchat
from datetime import datetime

class VoicevoxConnect():
    async def generate_wav_file(self, text, speaker, filepath):
        audio_query = requests.post(f'http://127.0.0.1:50021/audio_query?text={text}&speaker={speaker}')
        headers = {'Content-Type': 'application/json',}
        synthesis = requests.post(
            f'http://127.0.0.1:50021/synthesis?speaker={speaker}',
            headers=headers,
            data=json.dumps(audio_query.json())
        )
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(synthesis.content)
        wf.close()

# guild_id, livechat, filepath, voice_client
livechatdata = []

# guild_id, message_channel
voice_channel_data = []

# guild_id, speaker
guild_speaker = []

voicevoxConnect = None

# チェンジスピーカーフラグ
cs_flag = 0

# ボイスの種類
speakers = [ "0:四国めたん、あまあま"
            ,"1:ずんだもん、あまあま"
            ,"2:四国めたん、ノーマル"
            ,"3:ずんだもん、ノーマル"
            ,"4:四国めたん、セクシー"
            ,"5:ずんだもん、セクシー"
            ,"6:四国めたん、ツンツン"
            ,"7:ずんだもん、ツンツン"
            ,"8:春日部つむぎ、ノーマル"
            ,"9:波音リツ、ノーマル"
            ]
@tasks.loop(seconds=5)
async def youtube_text_to_speech():
    for i in range(len(livechatdata)):
        livechat = livechatdata[i][1]
        speaker = 0
        for j in range(len(guild_speaker)):
            if guild_speaker[j][0] == livechatdata[i][0]:
                speaker = guild_speaker[j][1]
                break
        filepath = livechatdata[i][2]
        voice_client = livechatdata[i][3]
        if livechat.is_alive():
            # チャットデータの取得
            chatdata = livechat.get()
            for c in chatdata.items:
                print(f"{c.datetime} {c.author.name} {c.message} {c.amountString}")
                await voicevoxConnect.generate_wav_file(c.author.name + "、" + c.message, speaker, filepath)
                source = await discord.FFmpegOpusAudio.from_probe(filepath, before_options="-channel_layout mono")
                try:
                    voice_client.play(source)
                except Exception as e:
                    print(datetime.now().strftime("%Y/%m/%d %H:%M:%S - ") + str(e))
        else:
            livechatdata.pop(i)
            return

class MyClient(discord.Client):
    @youtube_text_to_speech.before_loop
    async def before_youtube_text_to_speech():
        print('waiting...')
        await client.wait_until_ready()

    async def on_ready(self):
        global voicevoxConnect
        print(f'{self.user}がログインしました。')
        voicevoxConnect = VoicevoxConnect()

    async def on_message(self, message):
        global voicevoxConnect
        global livechatdata
        global voice_channel_data
        global cs_flag

        if message.author.bot:
            return
        if message.content == '.hi':
            if message.author.voice is None:
                await message.channel.send('ボイスチャンネルに入ってません')
            else:
                if message.guild.voice_client is None:
                    await message.author.voice.channel.connect()
                    voice_channel_data.append([message.guild.id, message.channel])
                    guild_speaker.append([message.guild.id, 8])
                    await message.channel.send("参加")
                else:
                    await message.channel.send("既に参加済みです")
            return

        if message.content == '.bye':
            if message.guild.voice_client is None:
                await message.channel.send("ボイスチャンネルに参加していません")
                return
            else:
                for i in range(len(voice_channel_data)):
                    if voice_channel_data[i][0] == message.guild.id:
                        voice_channel_data.pop(i)
                        await message.guild.voice_client.disconnect()
                        await message.channel.send("退室")
                        return
                return

        if cs_flag == 1:
            if len(message.content) == 1:
                if message.content.isdecimal():
                    speaker = int(message.content)
                    for i in range(len(guild_speaker)):
                        if guild_speaker[i][0] == message.guild.id:
                            guild_speaker[i][1] = speaker
                            await message.channel.send("ボイスを「" + speakers[speaker] + "」に変えました")
                            cs_flag = 0
                            return
                    await message.channel.send("ボイスチャットに入っていないからボイスは変えられないよ")
                    return
                else:
                    await message.channel.send("1桁の数字で入力してね")
                    return
            else:
                await message.channel.send("1桁の数字で入力してね")
                return

        # チェンジスピーカー、ボイスを変更したい時
        if message.content == '.cs':
            for i in range(len(guild_speaker)):
                if guild_speaker[i][0] == message.guild.id:
                    if cs_flag == 0:
                        cs_flag = 1
                        await message.channel.send(
                            speakers[0] + "\n"
                            + speakers[1] + "\n"
                            + speakers[2] + "\n"
                            + speakers[3] + "\n"
                            + speakers[4] + "\n"
                            + speakers[5] + "\n"
                            + speakers[6] + "\n"
                            + speakers[7] + "\n"
                            + speakers[8] + "\n"
                            + speakers[9] + "\n"
                            + "どれにするか数字で選んでください"
                             )
                        return
            await message.channel.send("ボイスチャットに入っていないからボイスは変えられません")
            return

      # YouTube読み上げ開始
        if message.content.startswith("https://www.youtube.com/watch?v="):
            message.content = message.content.replace('https://www.youtube.com/watch?v=', '')
            if len(message.content) != 11:
                await message.channel.send("YouTubeのリンクがおかしいです")
                return
            else:
                guild_id = message.guild.id
                livechat = pytchat.create(video_id = message.content)
                filepath = message.content + '.wav'
                voice_client = message.guild.voice_client
                livechatdata.append([guild_id, livechat, filepath, voice_client])
                await message.channel.send("YouTube読み上げを開始します")
            return

        # YouTube読み上げ停止
        if message.content == 'すとっぷ' or message.content == 'ストップ' or message.content == 'stop':
            for i in range(len(livechatdata)):
                if livechatdata[i][0] == message.guild.id:
                    await message.channel.send("YouTube読み上げを停止します")
                    livechatdata.pop(i)
                    return
            await message.channel.send("YouTube読み上げは現在行われていません")
            return

        # YouTube読み上げ中はdiscordのチャットに反応しない
        for i in range(len(livechatdata)):
            if livechatdata[i][0] == message.guild.id:
                return

        # ボイスチャットに入っていない場合はdiscordのチャットに反応しない
        if message.guild.voice_client is None:
            return
        else:
            # ボイスチャットに入っている場合はdiscordのチャットに反応する
            for i in range(len(voice_channel_data)):
                if voice_channel_data[i][0] == message.guild.id:
                    if voice_channel_data[i][1] == message.channel:
                        for i in range(len(guild_speaker)):
                            if guild_speaker[i][0] == message.guild.id:
                                speaker = guild_speaker[i][1]
                                filepath = str(message.guild.id) + '.wav'
                                if (message.guild.voice_client.is_playing()):
                                    return
                                await voicevoxConnect.generate_wav_file(message.content, speaker, filepath)
                                source = await discord.FFmpegOpusAudio.from_probe(filepath, before_options="-channel_layout mono")
                                try:
                                    message.guild.voice_client.play(source)
                                except Exception as e:
                                    print(datetime.now().strftime("%Y/%m/%d %H:%M:%S - ") + str(e))
                                return

client = MyClient()
youtube_text_to_speech.start()
client.run('OTAyNDgxMjk5NTI3MzE1NDU3.YXfDNQ.9HOLDFB-B5wJFmlbt6ysh15VgjE')