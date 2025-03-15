from string import punctuation
from datetime import timedelta
from aiogram.types import InputFile

from aiogram import F, Bot, types, Router, Dispatcher
from aiogram.filters import Command
from googletrans import Translator 

from filters.chat_types import ChatTypeFilter
from common.restricted_words import restricted_words
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import folium
import random
import os
import logging
import http.client
import json
import wikipediaapi  # Импортируем библиотеку для работы с Wikipedia API

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))
user_group_router.edited_message.filter(ChatTypeFilter(["group", "supergroup"]))


@user_group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()


def clean_text(text: str):
    return text.translate(str.maketrans("", "", punctuation))


@user_group_router.message(Command("mute"))
async def mute_user(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение!")
        return

    # Убедимся, что пользователь может выполнять эту команду
    admins_list = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.reply("У вас нет прав для использования этой команды!")
        return

    # Мутим пользователя на 5 минут
    user_to_mute = message.reply_to_message.from_user.id
    until_date = message.date + timedelta(minutes=5)
    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=user_to_mute,
        permissions=types.ChatPermissions(),
        until_date=until_date,
    )
    await message.reply(f"Пользователь {message.reply_to_message.from_user.first_name} замучен на 5 минут!")

@user_group_router.message(Command('porn'))
async def bot_info(message: types.Message):
    await message.reply(f"Ислам тебе сюда надо? 'https://rt.pornhub.com/video/search?search=pornohub")


@user_group_router.message(Command("info"))
async def bot_info(message: types.Message):
    bot_info_text = """
    Привет! Я бот Son-Gin-Wu dsk.
    Мой создатель: Den Dasakami.
    Email: dendasakami@gmail.com.
    
    Я помогу вам с администрированием групп и выполнением различных команд!
    """
    await message.reply(bot_info_text)



current_language = 'ru'

# Обработчик команды для изменения языка
@user_group_router.message(Command("wikilang"))
async def set_language(message: types.Message):
    global current_language

    # Извлекаем текст после команды "/set_language"
    language_code = message.text[len("/wikilang "):].strip().lower()

    # Проверяем, допустим ли язык
    if language_code in ['en', 'ru', 'fr', 'de']:  # Можете добавить больше языков
        current_language = language_code
        await message.reply(f"Язык поиска изменен на: {language_code.upper()}")
    else:
        await message.reply("Неверный код языка. Доступные языки: en, ru, fr, de.")


# Обработчик команды для поиска в Википедии
@user_group_router.message(Command("wiki"))
async def get_wiki_info(message: types.Message):
    global current_language

    # Извлекаем запрос пользователя после команды
    query = message.text[len("/wiki "):].strip()
    if not query:
        await message.reply("Пожалуйста, укажите запрос для поиска на Википедии.")
        return

    # Создаем объект Wikipedia API для текущего языка
    wiki_wiki = wikipediaapi.Wikipedia(user_agent='MyProjectDsk (dendasakami@gmail.com)', language=current_language)

    # Пытаемся найти статью
    page = wiki_wiki.page(query)

    if not page.exists():
        await message.reply(f"Статья по запросу '{query}' не найдена.")
        return

    # Получаем первые 500 символов из статьи
    summary = page.summary[:500] + "..." if len(page.summary) > 500 else page.summary
    await message.reply(f"Информация о '{query}':\n\n{summary}")


@user_group_router.message(Command("calc"))
async def calculate_expression(message: types.Message):
    if len(message.text.split()) < 2:
        await message.reply("Напишите выражение после команды, например: /calc 2+2")
        return

    expression = message.text.split(" ", 1)[1]
    try:
        result = eval(expression)
        await message.reply(f"Результат: {result}")
    except Exception:
        await message.reply("Не удалось посчитать выражение. Убедитесь, что оно корректное.")




@user_group_router.message(Command("greet_new_member"))
async def greet_new_member(message: types.Message):
    # Проверяем, есть ли новые участники чата
    if message.new_chat_members:
        new_member = message.new_chat_members[0]
        await message.reply(f"Приветствуем нового участника: {new_member.full_name}!")
    else:
        await message.reply("В чате нет новых участников.")



@user_group_router.message(Command("bot_info"))
async def bot_info(message: types.Message):
    info = "Я — бот для управления вашим чатом! Вот что я могу делать:\n"
    info += "- Закреплять сообщения\n"
    info += "- Удалять сообщения\n"
    info += "- Играть в города\n"
    info += "- Давать статистику пользователей\n"
    await message.reply(info)



@user_group_router.message(Command("random_fact"))
async def random_fact(message: types.Message):
    facts = [
        "В Японии есть остров, населённый только кроликами.",
        "Слоны — единственные животные, которые не могут прыгать.",
        "Медузы существуют уже более 500 миллионов лет, что делает их старейшими животными на Земле."
    ]
    
    fact = random.choice(facts)
    await message.reply(f"Случайный факт: {fact}")




# Путь к файлу для хранения команд
HELP_FILE_PATH = "help_commands.txt"

# Функция для загрузки команд из файла
def load_help_commands():
    if os.path.exists(HELP_FILE_PATH):
        with open(HELP_FILE_PATH, "r",  encoding="utf-8") as file:
            return file.readlines()
    return []

# Функция для сохранения команд в файл
def save_help_commands(commands):
    with open(HELP_FILE_PATH, "w",  encoding="utf-8") as file:
        file.writelines(commands)

# Загружаем команды при старте
help_commands = load_help_commands()

@user_group_router.message(Command("help"))
async def help_command(message: types.Message):
    help_text = "Привет! Вот список доступных команд:\n\n" + "".join(help_commands)
    await message.reply(help_text)

@user_group_router.message(Command("addhelp"))
async def add_help_command(message: types.Message):
    # Получаем новый текст команды
    new_command = message.text[8:].strip()  # Ожидается, что команда будет в виде /addhelp <команда>
    
    if new_command:
        help_commands.append(new_command + "\n")  # Добавляем новую команду в список
        save_help_commands(help_commands)  # Сохраняем изменения в файл
        await message.answer(f'Команда {new_command}')
    else:
        await message.reply("Пожалуйста, укажите команду для добавления.")

@user_group_router.message(Command("setgroupname"))
async def set_group_name(message: types.Message):
    # Проверка, является ли пользователь администратором
    if message.chat.type == "group" or message.chat.type == "supergroup":
        if message.from_user.id in [admin.user.id for admin in await message.chat.get_administrators()]:
            # Получаем новое название группы из сообщения
            new_name = message.text[13:].strip()  # Ожидается, что команда будет в виде /setgroupname <новое название>
            
            if new_name:
                try:
                    # Меняем название группы
                    await message.chat.set_title(new_name)
                    await message.answer(f"Название группы успешно изменено на: {new_name}")
                except Exception as e:
                    await message.answer(f"Произошла ошибка при изменении названия группы: {e}")
            else:
                await message.reply("Пожалуйста, укажите новое название для группы.")
        else:
            await message.reply("У вас нет прав для изменения названия группы.")

@user_group_router.message(Command("make_admin"))
async def make_admin(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение пользователя, которого хотите сделать администратором.")
        return

    # Убедимся, что пользователь может выполнять эту команду
    admins_list = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.reply("У вас нет прав для назначения администраторов!")
        return

    user_to_promote = message.reply_to_message.from_user.id
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user_to_promote,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_invite_to_group=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_manage_topics=True
        )
        await message.reply(f"Пользователь {message.reply_to_message.from_user.first_name} теперь администратор!")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")


@user_group_router.message(Command("discussion"))
async def start_discussion(message: types.Message):
    topics = [
        "Какие ваши любимые фильмы?",
        "Как вы проводите свободное время?",
        "Какие книги вы порекомендуете?",
        "Какую музыку вы предпочитаете?"
    ]
    topic = random.choice(topics)
    await message.reply(f"Тема для обсуждения: {topic}")


from aiogram import types
from aiogram.filters import Command



@user_group_router.message(Command("ban"))
async def ban_user(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение, которое хотите забанить!")
        return
    
    # Проверка прав пользователя (администратор или выше)
    admins_list = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.reply("У вас нет прав для использования этой команды!")
        return
    
    # Баним пользователя
    user_to_ban = message.reply_to_message.from_user.id
    await bot.ban_chat_member(
        chat_id=message.chat.id,
        user_id=user_to_ban
    )
    await message.reply(f"Пользователь {message.reply_to_message.from_user.first_name} был забанен!")
warnings = {}

@user_group_router.message(Command("warn"))
async def warn_user(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение, которое хотите предупредить.")
        return
    
    # Получаем ID пользователя, которому даём предупреждение
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    
    # Добавляем предупреждение
    if user_id in warnings:
        warnings[user_id] += 1
    else:
        warnings[user_id] = 1

    # Отправляем сообщение о предупреждении
    await message.reply(f"Пользователю {user_name} выдано предупреждение! ({warnings[user_id]} предупреждений)")

    # Если предупреждений больше 3, кидаем пользователя
    if warnings[user_id] >= 3:
        await message.reply(f"Пользователь {user_name} был забанен за 3 предупреждения!")
        # Код для кика пользователя, если необходимо
        # await bot.kick_chat_member(chat_id=message.chat.id, user_id=user_id)

@user_group_router.message(Command("kick"))
async def kick_user(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение, которое хотите кикнуть.")
        return
    
    # Проверка прав пользователя (администратор или выше)
    admins_list = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.reply("У вас нет прав для использования этой команды!")
        return
    
    # Кикаем пользователя
    user_to_kick = message.reply_to_message.from_user.id
    await bot.kick_chat_member(
        chat_id=message.chat.id,
        user_id=user_to_kick
    )
    await message.reply(f"Пользователь {message.reply_to_message.from_user.first_name} был кикнут!")



translator = Translator()

# Функция для получения случайной шутки
async def get_random_joke(category=None):
    conn = http.client.HTTPSConnection("jokeapi-v2.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': "42d64a47c1mshf800a3639f57c06p1e9d1cjsn5001b6c4c8ce",
        'x-rapidapi-host': "jokeapi-v2.p.rapidapi.com"
    }

    # Формируем URL в зависимости от категории
    if category:
        url = f"/joke/Any?format=json&contains={category}"
    else:
        url = "/joke/Any?format=json"

    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()

    if res.status == 200:
        joke_data = json.loads(data.decode("utf-8"))

        if 'type' in joke_data:
            if joke_data['type'] == 'single':
                joke_text = joke_data['joke']
            elif joke_data['type'] == 'twopart':
                joke_text = f"{joke_data['setup']} - {joke_data['delivery']}"
            else:
                joke_text = "Не удалось распознать шутку."
        else:
            joke_text = "Ошибка: в ответе нет поля 'type'."
    else:
        joke_text = f"Ошибка: не удалось получить данные от API. Код: {res.status}"

    conn.close()
    return joke_text

# Обработчик команды /joke с категорией
@user_group_router.message(Command("joke"))
async def joke(message: types.Message):
    args = message.text.split(maxsplit=1)  # Разделяем команду и аргумент
    category = args[1] if len(args) > 1 else None  # Берем категорию, если есть

    joke = await get_random_joke(category)
    await message.reply(joke, parse_mode='Markdown')



async def get_random_quote():
    url = "https://api.forismatic.com/api/1.0/"
    params = {
        "method": "getQuote",
        "format": "json",
        "lang": "ru"  # Можно заменить на "en" для английских цитат
    }

    try:
        response = requests.get(url, params=params)
        response.encoding = "utf-8"  # Исправляем кодировку
        if response.status_code == 200:
            quote_data = response.json()

            quote_text = f"💬 {quote_data['quoteText']}\n— {quote_data['quoteAuthor'] or 'Неизвестный автор'}"
            return quote_text
        else:
            return f"❌ Ошибка API: код {response.status_code}"
    except Exception as e:
        logging.error(f"Ошибка при запросе API: {e}")
        return "❌ Ошибка при получении цитаты."
    
@user_group_router.message(Command('quote'))
async def send_quote(message: types.Message):
    quote = await get_random_quote()
    await message.reply(quote, parse_mode="Markdown")


import urllib.parse
async def search_anime(query):
    # Кодируем запрос для корректной работы с русскими символами
    query_encoded = urllib.parse.quote(query)
    
    conn = http.client.HTTPSConnection("api.jikan.moe")

    # Формируем запрос к API с закодированным запросом
    url = f"/v4/anime?q={query_encoded}&limit=1"  # Ограничиваем поиск до 1 результата

    conn.request("GET", url)
    res = conn.getresponse()
    data = res.read()

    if res.status == 200:
        anime_data = json.loads(data.decode("utf-8"))
        
        if "data" in anime_data and len(anime_data["data"]) > 0:
            anime = anime_data["data"][0]
            anime_name = anime.get("title", "Не найдено аниме")
            anime_synopsis = anime.get("synopsis", "Нет описания")
            anime_image_url = anime.get("images", {}).get("jpg", {}).get("image_url", "Нет изображения")
            
            return f"Название аниме: {anime_name}\nОписание: {anime_synopsis}\nИзображение: {anime_image_url}"
        else:
            return "Не удалось найти аниме по запросу."
    else:
        return f"Ошибка: не удалось получить данные от API. Код: {res.status}"

    conn.close()

# Обработчик команды для поиска аниме
@user_group_router.message(Command("anime"))
async def anime(message: types.Message):
    args = message.text.split(maxsplit=1)  # Разделяем команду и запрос
    query = args[1] if len(args) > 1 else None  # Берем запрос

    if query:
        result = await search_anime(query)
        await message.reply(result, parse_mode='Markdown')
    else:
        await message.reply("Пожалуйста, укажите запрос для поиска аниме.")


async def get_random_meme():
    url = "https://api.imgflip.com/get_memes"
    response = requests.get(url).json()
    meme = random.choice(response["data"]["memes"])  # Выбираем случайный мем
    return meme["url"]

# Обработчик команды для отправки случайного мема
@user_group_router.message(Command("meme"))
async def meme(message: types.Message):
    meme_url = await get_random_meme()
    await message.reply_photo(meme_url)  # Отправка картинки напрямую
@user_group_router.message(Command("poll"))
async def poll(message: types.Message):
    # Проверка прав администратора
    admins_list = [admin.user.id for admin in await message.bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.answer("У вас нет прав для использования этой команды!")
        return

    poll_data = message.text[len("/poll "):]
    if not poll_data:
        await message.answer("Пожалуйста, укажите вопрос для опроса.")
        return

    # Разделение на вопрос и варианты
    try:
        question, *options = poll_data.split('|')
        if len(options) < 2:
            await message.answer("Минимум два варианта ответа.")
            return

        # Создание кнопок для вариантов
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for option in options:
            keyboard.add(KeyboardButton(option.strip()))

        # Отправка опроса
        await message.answer(question.strip(), reply_markup=keyboard)

    except Exception as e:
        await message.answer("Ошибка при создании опроса. Убедитесь, что разделили вопрос и варианты с помощью символа '|'.")
        print(str(e))


# Команда для закрепления сообщения
@user_group_router.message(Command("pin"))
async def pin_message(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение, которое хотите закрепить!")
        return

    # Проверка прав пользователя (администратор или выше)
    admins_list = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.reply("У вас нет прав для закрепления сообщений!")
        return

    # Закрепляем сообщение
    await bot.pin_chat_message(
        chat_id=message.chat.id,
        message_id=message.reply_to_message.message_id,
        disable_notification=False  # Можно включить или отключить уведомление о закреплении
    )
    await message.reply("Сообщение успешно закреплено!")

@user_group_router.message(Command("delete"))
async def delete_message(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Эту команду нужно использовать в ответ на сообщение, которое хотите удалить!")
        return

    # Проверка прав пользователя (администратор или выше)
    admins_list = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.reply("У вас нет прав для удаления сообщений!")
        return

    # Удаляем сообщение
    await bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.reply_to_message.message_id )
    await message.reply("Сообщение успешно удалено!")

@user_group_router.message(Command("stats"))
async def stats(message: types.Message, bot: Bot):
    # Пример получения статистики о пользователе (например, сколько сообщений он написал)
    user_stats = {
        'messages_sent': 20,  # Примерный показатель
        'last_active': "2025-02-11 14:32"  # Пример времени последней активности
    }
    
    await message.reply(f"Статистика пользователя:\n"
                         f"Сообщений отправлено: {user_stats['messages_sent']}\n"
                         f"Последняя активность: {user_stats['last_active']}")
    
tasks = []

@user_group_router.message(Command("add_task"))
async def add_task(message: types.Message):
    task = message.text[len("/add_task "):]
    if task:
        tasks.append(task)
        await message.reply(f"Задача '{task}' добавлена в список.")
    else:
        await message.reply("Пожалуйста, укажите задачу после команды.")


@user_group_router.message(Command("remove_task"))
async def remove_task(message: types.Message):
    try:
        task_number = int(message.text[len("/remove_task "):]) - 1
        if 0 <= task_number < len(tasks):
            task = tasks.pop(task_number)
            await message.reply(f"Задача '{task}' удалена.")
        else:
            await message.reply("Неверный номер задачи.")
    except ValueError:
        await message.reply("Пожалуйста, укажите номер задачи.")


@user_group_router.message(Command("list_tasks"))
async def list_tasks(message: types.Message):
    if tasks:
        task_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
        await message.reply(f"Ваши задачи:\n{task_list}")
    else:
        await message.reply("У вас нет задач.")

# @user_group_router.message(Command("ban"))
# async def ban_user(message: types.Message):
#     if not message.reply_to_message:
#         await message.answer("Эту команду нужно использовать в ответ на сообщение, которое хотите забанить.")
#         return
    
#     # Проверка прав администратора
#     admins_list = [admin.user.id for admin in await message.bot.get_chat_administrators(message.chat.id)]
#     if message.from_user.id not in admins_list:
#         await message.answer("У вас нет прав для использования этой команды!")
#         return

#     user_to_ban = message.reply_to_message.from_user.id
#     await message.bot.ban_chat_member(
#         chat_id=message.chat.id,
#         user_id=user_to_ban
#     )
#     await message.answer(f"Пользователь {message.reply_to_message.from_user.first_name} был забанен!")


@user_group_router.message(Command("unban"))
async def unban_user(message: types.Message):
    if not message.reply_to_message:
        await message.answer("Эту команду нужно использовать в ответ на сообщение, которое хотите разбанить.")
        return
    
    # Проверка прав администратора
    admins_list = [admin.user.id for admin in await message.bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.answer("У вас нет прав для использования этой команды!")
        return

    user_to_unban = message.reply_to_message.from_user.id
    await message.bot.unban_chat_member(
        chat_id=message.chat.id,
        user_id=user_to_unban
    )
    await message.answer(f"Пользователь {message.reply_to_message.from_user.first_name} был разбанен!")

@user_group_router.message(Command("clear_warnings"))
async def clear_warnings(message: types.Message):
    if not message.reply_to_message:
        await message.answer("Эту команду нужно использовать в ответ на сообщение пользователя.")
        return

    # Проверка прав администратора
    admins_list = [admin.user.id for admin in await message.bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins_list:
        await message.answer("У вас нет прав для использования этой команды!")
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name

    if user_id in warnings:
        del warnings[user_id]
        await message.answer(f"Все предупреждения для пользователя {user_name} были удалены.")
    else:
        await message.answer(f"У пользователя {user_name} нет предупреждений.")


@user_group_router.message(Command("set_description"))
async def set_description(message: types.Message, bot: Bot):
    # Получаем текст команды, который будет новым описанием
    description = message.text[len("/set_description "):]

    if not description:
        await message.reply("Пожалуйста, укажите описание после команды.")
        return

    # Отправляем команду на обновление описания чата
    try:
        await bot.set_chat_description(chat_id=message.chat.id, description=description)
        await message.reply(f"Описание чата успешно обновлено на: {description}")
    except Exception as e:
        await message.reply(f"Произошла ошибка при обновлении описания: {e}")





def get_info_by_ip(ip='127.0.0.1'):
    try:
        response = requests.get(url=f'http://ip-api.com/json/{ip}').json()

        data = {
            '[IP]': response.get('query'),
            '[Int prov]': response.get('isp'),
            '[Org]': response.get('org'),
            '[Country]': response.get('country'),
            '[Region Name]': response.get('regionName'),
            '[City]': response.get('city'),
            '[ZIP]': response.get('zip'),
            '[Lat]': response.get('lat'),
            '[Lon]': response.get('lon'),
        }

        info_text = "\n".join([f'{k} : {v}' for k, v in data.items()])

        lat = response.get('lat')
        lon = response.get('lon')

        if lat is not None and lon is not None:
            # If lat and lon are valid, create the map
            area = folium.Map(location=[lat, lon])
        else:
            # If lat or lon is None, use a default location (e.g., 0, 0)
            area = folium.Map(location=[0, 0])  # Default location

        # Create a folder to save the HTML files if it doesn't exist
        folder_path = 'ip_maps'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Save the map HTML file inside the folder
        file_path = os.path.join(folder_path, f'{response.get("query")}_{response.get("city")}.html')
        area.save(file_path)

        return info_text

    except requests.exceptions.ConnectionError:
        return '[!] Please check your connection!'
    


# Команда /ip_search
@user_group_router.message(Command("ip_search"))
async def ip_search_command(message: types.Message):
    ip = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None  # Получаем IP из сообщения
    if not ip:
        await message.reply("Пожалуйста, укажите IP-адрес для поиска. Пример: /ip_search 8.8.8.8")
        return

    info = get_info_by_ip(ip)  # Получаем информацию по IP
    await message.reply(info)  # Отправляем пользователю результат





# Ответ на упоминание бота
@user_group_router.message(F.text.contains("@dsk_model_two_bot"))
async def mention_reply(message: types.Message):
    replies = [
        "Привет! Чем могу помочь?",
        "Да, это я, ваш бот!",
        "Оу, кто-то меня звал?",
        "Просто бот сижу тут...",
    ]
    await message.reply(random.choice(replies))


# ниже всех
@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message):
    # Проверяем, что сообщение содержит текст
    if message.text:
        # Преобразуем текст в нижний регистр и проверяем на наличие запрещённых слов
        if restricted_words.intersection(clean_text(message.text.lower()).split()):
            await message.answer(
                f"{message.from_user.first_name}, соблюдайте порядок в чате!"
            )
            await message.delete()
            # await message.chat.ban(message.from_user.id)
