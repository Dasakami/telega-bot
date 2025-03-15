import logging
import sqlite3
from googletrans import Translator
from aiogram import Bot, types, Router, Dispatcher
from aiogram.filters import Command
from filters.chat_types import ChatTypeFilter
import requests  # Для работы с API Datamuse

# Инициализация бота и базы данных
logging.basicConfig(level=logging.INFO)

translator = Translator()

# База данных для статистики
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    user_id INTEGER PRIMARY KEY,
    words_learned INTEGER DEFAULT 0
)
""")
conn.commit()

# Установка языка группы (по умолчанию en-ru)
group_languages = {}

# Создаем роутер для команд
tran_group_router = Router()

# Обработчик команды /setlang
@tran_group_router.message(Command("setlang"))
async def set_language(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Используйте: /setlang en-ru (например, для перевода с английского на русский)")
        return
    group_languages[message.chat.id] = args[1]
    await message.reply(f"Язык группы установлен на {args[1]}")

# Обработчик команды /word
@tran_group_router.message(Command("word"))
async def translate_word(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Используйте: /word слово")
        return
    word = args[1]
    lang = group_languages.get(message.chat.id, "en-ru").split("-")
    translation = translator.translate(word, src=lang[0], dest=lang[1]).text
    
    # Обновление статистики
    user_id = message.from_user.id
    cursor.execute("INSERT INTO stats (user_id, words_learned) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET words_learned = words_learned + 1", (user_id, 1))
    conn.commit()
    
    await message.reply(f"{word} - {translation}")

# Обработчик команды /text
@tran_group_router.message(Command("tran"))
async def translate_text(message: types.Message):
    reply = message.reply_to_message
    lang = group_languages.get(message.chat.id, "en-ru").split("-")

    # Если это ответ на сообщение, то переводим текст
    if reply and reply.text:
        translation = translator.translate(reply.text, src=lang[0], dest=lang[1]).text
        await message.reply(f"Перевод: {translation}")
    # Если текст написан сразу в чате, то переводим этот текст
    elif message.text:
        text_to_translate = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else ''
        if text_to_translate:
            translation = translator.translate(text_to_translate, src=lang[0], dest=lang[1]).text
            await message.reply(f"Перевод: {translation}")
        else:
            await message.reply("Укажите текст для перевода. Например: /text Привет!")

# Обработчик команды /stats
@tran_group_router.message(Command("stats"))
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT words_learned FROM stats WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    words_count = result[0] if result else 0
    await message.reply(f"Вы выучили {words_count} слов(-а)!")

# Обработчик команды /currentlang
@tran_group_router.message(Command("currentlang"))
async def current_language(message: types.Message):
    current_lang = group_languages.get(message.chat.id, "en-ru")
    await message.reply(f"Текущий язык перевода: {current_lang}")

# Команда для поиска синонимов
@tran_group_router.message(Command("wordsyn"))
async def word_synonyms(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Используйте: /wordsyn слово")
        return
    word = args[1]

    # Запрос к API Datamuse для получения синонимов
    url = f"https://api.datamuse.com/words?rel_syn={word}&max=5"
    response = requests.get(url)
    synonyms = response.json()

    if synonyms:
        synonym_text = ", ".join([syn["word"] for syn in synonyms])
        await message.reply(f"Синонимы для слова '{word}':\n{synonym_text}")
    else:
        await message.reply(f"Синонимы для слова '{word}' не найдены.")

# Команда для поиска антонимов
@tran_group_router.message(Command("wordayn"))
async def word_antonyms(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Используйте: /wordayn слово")
        return
    word = args[1]

    # Запрос к API Datamuse для получения антонимов
    url = f"https://api.datamuse.com/words?rel_ant={word}&max=5"
    response = requests.get(url)
    antonyms = response.json()

    if antonyms:
        antonym_text = ", ".join([ant["word"] for ant in antonyms])
        await message.reply(f"Антонимы для слова '{word}':\n{antonym_text}")
    else:
        await message.reply(f"Антонимы для слова '{word}' не найдены.")


@tran_group_router.message(Command("wordrel"))
async def word_related(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Используйте: /wordrel слово")
        return
    word = args[1]

    # Запрос к API Datamuse для получения родственных слов
    url = f"https://api.datamuse.com/sug?s={word}"
    response = requests.get(url)
    related_words = response.json()

    if related_words:
        related_text = ", ".join([rel["word"] for rel in related_words])
        await message.reply(f"Родственные слова для '{word}':\n{related_text}")
    else:
        await message.reply(f"Родственные слова для '{word}' не найдены.")
