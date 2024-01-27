from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
from tbot import db
import subprocess
import requests
import asyncio
import os


max_inpg_running = asyncio.Semaphore(1)
ip = requests.get('https://checkip.amazonaws.com').text.strip()                                                         # отримання своєї ip - адреси
storage = MemoryStorage()
load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher(bot=bot, storage=storage)
video_queue = asyncio.Queue()


class RegistrationStates(StatesGroup):
    CONTACT = State()
    FULL_NAME = State()


async def process_video(user_id):
    async with max_inpg_running:
        command = ["python3", "instant-ngp/process_input_video_step_by_step.py", "--input_video", f"videos/{user_id}/input_video.mp4", "--output_path", f"{user_id}"]
        process = await asyncio.create_subprocess_exec(*command)
        await process.communicate()
        result_file_path = f"django3d/viewer/templates/viewer/sfm/{user_id}/sfm_output.html"                                # Відправляємо результат роботи користувачу
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
    django_process = subprocess.Popen(["python3", "django3d/manage.py", "runserver", "0.0.0.0:8080"])                   # запуск django сайту
    asyncio.ensure_future(video_processing_handler())


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
    await message.answer('Якщо бот не відправляє реконструкцію, почекайте, користувачів багато, а сервер повільний. Якщо станеться помилка, ми її Вам відправимо')


@dp.message_handler(commands=['unreg'])
async def unreg_cmd(message: types.Message):
    await db.unregister(message.from_user.id)
    await message.answer("Усі дані про Вас очищено, а посилання на моделі зламано")
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
    await message.reply("Ваше відео додане в чергу. Не відправляйте нових відео поки Ви у черзі, бо це перезапише старе відео")
    await video_queue.put(message.from_user.id)

if __name__ == '__main__':

    executor.start_polling(dp, on_startup=startup, skip_updates=True)
