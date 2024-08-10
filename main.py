ai = input("AIによるチャット規制を有効にしますか? y/n :")


log_channel_id = 0  #認証機能を使うときに必要です。新たにボットとあなた以外アクセスできないチャンネルを作成して下さい。
role_id = 0  #認証時につけるロールのid
verify_channel_id = 0  # 認証に使うチャンネルid (この認証は、そのちゃんねるで.verifyと打つとできます。)
bot_token = "" # botのトークン


GREEN = '\033[92m'
YELLOW = "\033[33m"
END = '\033[0m'

import os
from datetime import timedelta, datetime, timezone
import time
import asyncio
import discord
from discord import app_commands

if ai == "y":
    import logging
    import torch
    import tensorflow as tf
    import warnings
    from transformers import pipeline
    from langdetect import detect
    from googletrans import Translator
    
    warnings.filterwarnings("ignore", message="`clean_up_tokenization_spaces` was not set.")
    warnings.filterwarnings("ignore", message="Torch was not compiled with flash attention.")
    warnings.filterwarnings("ignore", message="The name tf.losses.sparse_softmax_cross_entropy is deprecated.")
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    tf.get_logger().setLevel(logging.ERROR)
    translator = Translator()
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        print(f"言語検出エラー: {e}")
        return None

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bad_words.txt")
bad_words = []

with open(file_path, 'r', encoding='utf-8') as f:
    for line in f:
        bad_word = line.strip()
        bad_words.append(bad_word)

domains = [
    ".com", ".jp", ".gg", ".net", ".org", ".edu", ".gov", ".co", ".xyz", ".info", ".biz", ".us",
    ".eu", ".tv", ".name", ".mobi", ".club", ".store", ".pro", ".co.uk", ".org.uk", ".me", ".ws",
    ".cc", ".tv", ".aero", ".museum", ".tel", ".int", ".jobs", ".travel", ".cat", ".coop", ".asia",
    ".tk", ".cf", ".gq", ".ml", ".vn", ".th", ".hk", ".sg", ".my", ".ph", ".id", ".cn", ".kr", ".tw",
    ".jp", ".pk", ".bd", ".np", ".lk", ".in", ".ae", ".sa", ".qa", ".om", ".kw", ".bh", ".il", ".ir", "http"
]

first_message = {}
sent = []
message_count = {}
translations = {}
verified_that_good = []
verified_that_bad = []
mention = []




@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.guilds)} サーバー"))
    await tree.sync()
    print(f"{GREEN}ボットが起動しました。{END}")
    
@client.event
async def on_message(message):
    global log_channel_id
    global role_id
    global first_message,message_count
    global verified_that_good, verified_that_bad


    if message.author.bot and not message.webhook_id:
        return
    
    if message.channel.id == log_channel_id:
        guild_id = message.guild.id

        guild = client.get_guild(guild_id)
        if guild:
            try:
                member = guild.get_member(int(message.content))
                role = discord.utils.get(guild.roles, id=role_id)
                if member and role:
                    await member.add_roles(role)
                    user = await client.fetch_user(int(message.content))
                    await user.send("✅ロールの付与が完了しました。")
                else:
                    print("メンバーかロールが存在しません。")
            except Exception as e:
                print(f"エラー発生: {e}")
        else:
            print("ギルドがない...!?")

    if message.content == ".verify":
        await message.author.send("下のURLをクリックして、reCAPTCHAを解いてください。")
        await message.author.send(f"あなたのサイト/?id={message.author.id}")

    for bad_word in bad_words:
        if bad_word in message.content:
            await message.delete()
            return
        
    for domain in domains:
        if domain in message.content:
            await message.delete()
            await message.author.send(f"このサーバーではurlの送信は許可されていません。")
            return

    if "<@" in message.content:
        await message.delete()
        if message.author.name not in mention:
            await message.author.send(f"このサーバーではメンションが許可されていません。もう一度メンションをすると、タイムアウトになります。")
            mention.append(message.author.name)
            return
        else:
            timeout_duration = datetime.now(timezone.utc) + timedelta(seconds=60)
            await message.author.timeout(timeout_duration, reason="メンション")
            await message.author.send("あなたはメンションスパムによってタイムアウトされました。")
            return

    if message.author.name not in message_count:
        message_count[message.author.name] = 0
        first_message[message.author.name] = time.time()
    message_count[message.author.name] += 1

    if time.time() - first_message[message.author.name] >= 5:
        first_message[message.author.name] = time.time()
        message_count[message.author.name] = 0

        
    if message_count[message.author.name] >= 3:
        await message.delete()
        if message.author.name in sent:
            return
        timeout_duration = datetime.now(timezone.utc) + timedelta(seconds=30)
        await message.author.timeout(timeout_duration, reason="スパム")
        await message.author.send("あなたはスパムによってタイムアウトされました。")
        sent.append(message.author.name)
        message_count[message.author.name] = 0
        await asyncio.sleep(1)
        return

    if ai == "y":

        language = detect_language(message.content)

        if language == "ja":

            if message.content in verified_that_good:
                return
            if message.content in verified_that_bad:
                await message.delete()
                return

            translation = translator.translate(message.content, src='ja', dest='en').text
            classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
            results = classifier(translation)[0]
            score = results['score']
            if score >= 0 and score <= 0.2:
                verified_that_good.append(message.content)
            else:
                await message.delete()
                verified_that_bad.append(message.content)
            

            classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
            results = classifier(translation)[0]
            score = results['score']
            
            if score >= 0 and score <= 0.2:
                verified_that_good.append(message.content)
            else:
                await message.delete()
                verified_that_bad.append(message.content)
        else:
            for verified_that_goo in verified_that_good:
                if message.content == verified_that_goo:
                    return
                
            for verfied_that_ba in verified_that_bad:
                if verfied_that_ba == message.content:
                    await message.delete()
                    return
                
            classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
            results = classifier(message.content)[0]
            score = results['score']
            
            print(f"{GREEN}{message.content}{END}")
            print(f"{YELLOW}{score}{END}")

            if score >= 0 and score <= 0.2:
                verified_that_good.append(message.content)
            else:
                verified_that_bad.append(message.content)
                await message.delete()


client.run(bot_token)
