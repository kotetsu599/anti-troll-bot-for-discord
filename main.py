import discord
import os
import warnings
from langdetect import detect
from googletrans import Translator
from datetime import timedelta
from discord.utils import utcnow 
from transformers import pipeline
import torch
import tensorflow as tf
import logging
import time
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
    ".jp", ".pk", ".bd", ".np", ".lk", ".in", ".ae", ".sa", ".qa", ".om", ".kw", ".bh", ".il", ".ir"
]
first_message = {}
messages = []
message_count = {}
translations = {}
verified_that_good = []
verified_that_bad = []
GREEN = '\033[92m'
YELLOW = "\033[33m"
END = '\033[0m'
mention = {}
warnings.filterwarnings("ignore", message="`clean_up_tokenization_spaces` was not set.")
warnings.filterwarnings("ignore", message="Torch was not compiled with flash attention.")
warnings.filterwarnings("ignore", message="The name tf.losses.sparse_softmax_cross_entropy is deprecated.")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
tf.get_logger().setLevel(logging.ERROR)

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=discord.Intents.all())

translator = Translator()

def detect_language(text):
    try:
        return detect(text)
    except:
        return None

@client.event
async def on_ready():
    print("Bot is ready.")

@client.event
async def on_message(message):
    global first_message, messages, message_count
    global translations, verified_that_good, verified_that_bad
    messages.append(message)

    for bad_word in bad_words:
        if bad_word in message.content:
            await message.delete()
            return
    for domain in domains:
        if domain in message.content:
            await message.delete()
            await message.channel.send(f"このサーバーではurlの送信は許可されていません。")
            return

    if "<@" in message.content:
        await message.delete()
        if message.author.name not in mention:
            await message.channel.send(f"このサーバーではメンションが許可されていません。もう一度メンションをすると、タイムアウトになります。")
        try:
            mention[message.author.name] += 1
        except:
            mention[message.author.name] = 1
        if mention[message.author.name]>=2:
            timeout_duration = utcnow() + timedelta(seconds=60)
            await message.author.timeout(timeout_duration, reason="メンション")


    if message.author.bot:
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
        timeout_duration = utcnow() + timedelta(seconds=30)
        await message.author.timeout(timeout_duration, reason="スパム")
        message_count[message.author.name] = 0
        return


    message_content = message.content
    language = detect_language(message_content)

    if language == "ja":
        print("detected that it is ja")
        if message.content not in translations:
            for verified_that_goo in verified_that_good:
                if verified_that_goo in message.content:
                    return
            for verfied_that_ba in verified_that_bad:
                if verfied_that_ba in message.content:
                    await message.delete()
                    return
            translation = translator.translate(message_content, src='ja', dest='en').text
            translations[message.content]=translation
            classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
            results = classifier(translation)[0]
            score = results['score']
            print(f"{GREEN}{translation}{END}")
            print(f"{YELLOW}{score}{END}")
            if score >= 0 and score <= 0.1:
                verified_that_good.append(message.content)
            else:
                await message.delete()

                verified_that_bad.append(message.content)

        else:
            for verified_that_goo in verified_that_good:
                if verified_that_goo in message.content:
                    return
            for verfied_that_ba in verified_that_bad:
                if verfied_that_ba in message.content:
                    await message.delete()
                    return
            translation = translations[message.content]
            classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
            results = classifier(translation)[0]
            score = results['score']
            print(f"{GREEN}{translation}{END}")
            print(f"{YELLOW}{score}{END}")
            if score >= 0 and score <= 0.1:
                verified_that_good.append(message.content)
            else:
                await message.delete()

                verified_that_bad.append(message.content)


    else:
        for verified_that_goo in verified_that_good:
            if verified_that_goo in message.content:
                return
        for verfied_that_ba in verified_that_bad:
            if verfied_that_ba in message.content:
                await message.delete()
                return
        translation = message_content
        classifier = pipeline("text-classification", model="unitary/toxic-bert", device=0 if torch.cuda.is_available() else -1)
        results = classifier(translation)[0]
        score = results['score']
        
        print(f"{GREEN}{translation}{END}")
        print(f"{YELLOW}{score}{END}")
        if score >= 0 and score <= 0.1:
            verified_that_good.append(message.content)
        else:
            verified_that_bad.append(message.content)
            await message.delete()
       

client.run("token here")