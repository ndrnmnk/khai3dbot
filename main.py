from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
from tbot import db
import asyncio
import os
import requests
import subprocess


ip = requests.get('https://checkip.amazonaws.com').text.strip()
storage = MemoryStorage()
load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot=bot, storage=storage)
video_queue = asyncio.Queue()


class RegistrationStates(StatesGroup):
    CONTACT = State()
    FULL_NAME = State()


async def process_video(user_id):
    command = f"python3 instant-ngp/process_input_video_step_by_step.py --input_video videos/{user_id}/input_video.mp4 --output_path '{user_id}'"
    os.system(command)
    # Відправляємо результат роботи користувачу
    result_file_path = f"django3d/viewer/templates/viewer/sfm/{user_id}/sfm_output.html"
    await bot.send_document(user_id, types.InputFile(result_file_path))
    await db.rm_dir(user_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn = types.InlineKeyboardButton('Відкрити модель у браузері', url=f'http://{ip}:8080/sfm/{user_id}')
    markup.add(btn)
    await bot.send_message(user_id, text="Готово!", reply_markup=markup)


async def video_processing_handler():
    while True:
        user_id = await video_queue.get()
        await process_video(user_id)
        video_queue.task_done()


async def startup(_):
    print("Bot started!")
    django_process = subprocess.Popen(["python3", "django3d/manage.py", "runserver", "0.0.0.0:8080"])
    asyncio.ensure_future(video_processing_handler())


# Bot starts here

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
    await db.id_init(message.from_user.id, message.from_user.username)

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = types.KeyboardButton("Відправити контакт", request_contact=True)
    markup.row(button)
    await message.answer('Добрий день! Для початку зареєструємось (бо ми не хочемо щоб хтось використовував наші ресурси без відома). Просто натисніть кнопку Відправити контакт, щоб продовжити', reply_markup=markup)
    await RegistrationStates.CONTACT.set()


@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.answer('Якщо бот не відправляє реконструкцію, почекайте, користувачів багато, а сервер слабкий. Якщо станеться помилка, ми її Вам відправимо')


@dp.message_handler(commands=['unreg'])
async def unreg_cmd(message: types.Message):
    await db.unregister(message.from_user.id)
    await message.answer("Усі дані про Вас очищено, посилання зламано")
    await message.answer("Щоб продовжити користуватись ботом, зареєструйтесь знову")


@dp.message_handler(lambda message: not message.contact, state=RegistrationStates.CONTACT)
async def add_contact(message: types.Message):
    await message.answer("Ви маєте відправити саме контакт, щоб продовжити")


@dp.message_handler(content_types=types.ContentType.CONTACT, state=RegistrationStates.CONTACT)
async def phone_reg(message: types.Message, state: FSMContext):
    num = message.contact.phone_number
    await db.phone_init(message.from_user.id, num)
    await message.reply("Добре, тепер введіть Ваше прізвище та ім'я")
    await RegistrationStates.FULL_NAME.set()


@dp.message_handler(lambda message: not message.contact, state=RegistrationStates.FULL_NAME)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text
    creds = "_".join(full_name.split())
    await db.save_full_name(message.from_user.id, creds)
    await state.finish()
    await message.reply("Реєстрація завершена! Можете відправляти відео для реконструкції")


@dp.message_handler(content_types=types.ContentType.VIDEO)
async def handle_video(message: types.Message):
    print("got video")
    await db.prepare_dj_db(message.from_user.id)
    video_path = f"videos/{message.from_user.id}/input_video.mp4"
    await message.video.download(video_path)
    await message.reply("Ваше відео додане в чергу")
    await video_queue.put(message.from_user.id)

if __name__ == '__main__':

    executor.start_polling(dp, on_startup=startup, skip_updates=True)
