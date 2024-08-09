# これは荒らし対策ボットの一例です。これをそのまま荒らし対策に使うとまずいことになるかもしれませんので、計画的にご利用ください。
# 初期設定: 5秒間に3回以上のメッセージでタイムアウト　メンション二回目でタイムアウト　


ai = input("AIによるチャット規制を有効にしますか? y/n ※おすすめしません。荒らされると規制判定に時間がかかりすぎてスパム対策が動かなくなります。:") 
if ai not in ["y","n"]:
    print("🤬🤬🤬🤬🤬")
    exit()
if ai == "y":
    from langdetect import detect
    import warnings
    from googletrans import Translator
    from transformers import pipeline
    import torch
    import tensorflow as tf
import discord
import os
from datetime import timedelta
from discord.utils import utcnow 
import time
import logging
import asyncio
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
    ".jp", ".pk", ".bd", ".np", ".lk", ".in", ".ae", ".sa", ".qa", ".om", ".kw", ".bh", ".il", ".ir","http"
]
first_message = {}
sent = []
messages = []
message_count = {}
translations = {}
verified_that_good = []
verified_that_bad = []
GREEN = '\033[92m'
YELLOW = "\033[33m"
END = '\033[0m'
mention = []
if ai == "y":
    warnings.filterwarnings("ignore", message="`clean_up_tokenization_spaces` was not set.")
    warnings.filterwarnings("ignore", message="Torch was not compiled with flash attention.")
    warnings.filterwarnings("ignore", message="The name tf.losses.sparse_softmax_cross_entropy is deprecated.")

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    tf.get_logger().setLevel(logging.ERROR)
    translator = Translator()

    def detect_language(text):
        try:
            return detect(text)
        except:
            return None

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.guilds)} サーバー"))
    print(f"{GREEN}ボットが起動しました。{END}")

@client.event
async def on_message(message):
    global first_message, messages, message_count
    global translations, verified_that_good, verified_that_bad
    messages.append(message)

    if message.author.bot:
        return 
    
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
            timeout_duration = utcnow() + timedelta(seconds=60)
            await message.author.timeout(timeout_duration, reason="メンション")
            await message.author.send("あなたはメンションスパムによってタイムアウトされました。")
            return

    if message.author.name not in message_count:
        message_count[message.author.name]=0
        first_message[message.author.name] = time.time()
    message_count[message.author.name] += 1

    if time.time()-first_message[message.author.name] >= 5:
        first_message[message.author.name] = time.time()
        message_count[message.author.name] = 0
        messages =[]
        
    if message_count[message.author.name] >= 3:
        await message.delete()
        if message.author.name in sent:
            return
        timeout_duration = utcnow() + timedelta(seconds=30)
        await message.author.timeout(timeout_duration, reason="スパム")
        await message.author.send("あなたはスパムによってタイムアウトされました。")
        sent.append(message.author.name)
        message_count[message.author.name] = 0
        await asyncio.sleep(5)
        return

    if ai == "y":
        message_content = message.content
        language = detect_language(message_content)

        if language == "ja":
            if message.content not in translations:
                for verified_that_goo in verified_that_good:
                    if verified_that_goo == message.content:
                        return
                for verfied_that_ba in verified_that_bad:
                    if verfied_that_ba == message.content:
                        await message.delete()
                        return
                    
                translation = translator.translate(message_content, src='ja', dest='en').text
                translations[message.content]=translation
                classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
                results = classifier(translation)[0]
                score = results['score']
                print(f"{GREEN}{translation}{END}")
                print(f"{YELLOW}{score}{END}")
                
                if score >= 0 and score <= 0.2:
                    verified_that_good.append(message.content)
                else:
                    await message.delete()

                    verified_that_bad.append(message.content)

            else:
                for verified_that_goo in verified_that_good:
                    if verified_that_goo == message.content:
                        return
                    
                for verfied_that_ba in verified_that_bad:
                    if verfied_that_ba == message.content:
                        await message.delete()
                        return
                    
                translation = translations[message.content]
                classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
                results = classifier(translation)[0]
                score = results['score']
                print(f"{GREEN}{translation}{END}")
                print(f"{YELLOW}{score}{END}")

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
            
            print(f"{GREEN}{message_content}{END}")
            print(f"{YELLOW}{score}{END}")

            if score >= 0 and score <= 0.2:
                verified_that_good.append(message.content)
            else:
                verified_that_bad.append(message.content)
                await message.delete()
       
client.run("bot token here")
