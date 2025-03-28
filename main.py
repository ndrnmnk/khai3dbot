from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
from process_video import process_vid, process_splat
import subprocess
import requests
import asyncio
import os
import db


max_inpg_running = asyncio.Semaphore(1)
storage = MemoryStorage()
load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot=bot, storage=storage)
video_queue = asyncio.Queue()
ip = requests.get("https://ifconfig.me").text.strip()

GSPLAT_TRAINER = os.getenv('GSPLAT_TRAINER')
GSPLAT_VENV = os.getenv('GSPLAT_VENV')
print(GSPLAT_VENV)
print(GSPLAT_TRAINER)


class RegistrationStates(StatesGroup):
    CONTACT = State()
    FULL_NAME = State()


async def process_video_sfm(user_id):
    async with max_inpg_running:
         process_vid(user_id)
         result_file_path = f"htmls/{user_id}.html" # Відправляємо результат роботи користувачу
         await bot.send_document(user_id, types.InputFile(result_file_path))
         await db.rm_dir(user_id, 0)
         await bot.send_message(user_id, text="50% готово! Ще через хвилину прилетить повноцінна 3Д модель")


async def process_video_splat(user_id):
    async with max_inpg_running:
        command = [GSPLAT_VENV, GSPLAT_TRAINER, "default", "--data-dir", os.path.abspath("temp/"), "--result-dir", os.path.abspath("temp/res")]
        process = await asyncio.create_subprocess_exec(*command)
        await process.communicate()
        process_splat(user_id, ip)
        result_ply = f"temp/res/ply/point_cloud_1000.ply"
        result_html = f"temp/res.html" # Відправляємо результат роботи користувачу
        await bot.send_document(user_id, types.InputFile(result_ply))
        await bot.send_document(user_id, types.InputFile(result_html))
        await bot.send_message(user_id, text="Ось і повноціння модель")
        await bot.send_message(user_id, text="Примітка: html-файл відкриває лише останню модель, щоб відкрити стару, перетягни ply файл у вкладку з відкритим html файлом")


async def video_processing_handler():
    while True:
        user_id = await video_queue.get()
        await process_video_sfm(user_id)
        await process_video_splat(user_id)
        video_queue.task_done()


async def startup(_):
    print("Bot started!")
    splat_server = subprocess.Popen(
        ["python3", "splat_server.py"])  # start server hosting splat files
    asyncio.ensure_future(video_processing_handler())


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
    await db.id_init(message.from_user.id, message.from_user.username)

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = types.KeyboardButton("Відправити контакт", request_contact=True)
    markup.row(button)
    await message.answer('Привіт! Для початку зареєструємось (бо ми не хочемо щоб хтось використовував наші ресурси без відома). Просто натисніть кнопку Відправити контакт, щоб продовжити', reply_markup=markup)
    await RegistrationStates.CONTACT.set()


@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.answer("Інструкція як відправити відео: 1. Обери невеличкий об'єкт. 2. Постав на контрастну поверхню. 3. Зніми предмет з усіх боків на відео (до 30 секунд). Якщо бот каже відправити контакт, а кнопки нема, просто відправте йому якийсь текст, і вона з'явиться. Якщо бот не відправляє реконструкцію, почекайте, користувачів багато, а сервер повільний. Якщо станеться помилка, ми її виправимо")


@dp.message_handler(commands=['unreg'])
async def unreg_cmd(message: types.Message):
    await db.unregister(message.from_user.id)
    await message.answer("Усі дані про тебе очищено, а посилання на моделі зламано")
    await message.answer("Щоб продовжити користуватись ботом, зареєструйтесь знову")
    await db.id_init(message.from_user.id, message.from_user.username)
    await RegistrationStates.CONTACT.set()


@dp.message_handler(lambda message: not message.contact, state=RegistrationStates.CONTACT)
async def add_contact(message: types.Message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = types.KeyboardButton("Відправити контакт", request_contact=True)
    markup.row(button)
    await message.answer("Ти маєш відправити саме контакт, щоб продовжити", reply_markup=markup)


@dp.message_handler(content_types=types.ContentType.CONTACT, state=RegistrationStates.CONTACT)
async def phone_reg(message: types.Message, state: FSMContext):
    num = message.contact.phone_number
    await db.phone_init(message.from_user.id, num)
    await message.reply("Добре, тепер введи своє прізвище та ім'я")
    await RegistrationStates.FULL_NAME.set()


@dp.message_handler(lambda message: not message.contact, state=RegistrationStates.FULL_NAME)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text
    creds = "_".join(full_name.split())
    await db.save_full_name(message.from_user.id, creds)
    await state.finish()
    await message.reply("Реєстрація завершена! Можеш відправляти відео для реконструкції: 1. Обери невеличкий об'єкт. 2. Постав на контрастну поверхню. 3. Зніми предмет з усіх боків на відео (до 30 секунд)")


@dp.message_handler(content_types=types.ContentType.VIDEO)
async def handle_video(message: types.Message):
    print("got video")
    await db.rm_dir(message.from_user.id, 0)
    video_path = f"videos/{message.from_user.id}/input_video.mp4"
    await message.video.download(video_path)
    await message.reply("Твоє відео додане в чергу. Не відправляй нових відео поки воно у черзі, бо це перезапише старе відео. Реконструкція займає не менше 2 хвилин. Тому доведеться трохи зачекати :)")
    await video_queue.put(message.from_user.id)

if __name__ == '__main__':

    executor.start_polling(dp, on_startup=startup, skip_updates=True)
