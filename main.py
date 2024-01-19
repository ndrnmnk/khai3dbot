import telebot
import os
import glob
import sqlite3
import time


def clear_dir(path):
    files = glob.glob(path)
    for f in files:
        os.remove(f)


bot = telebot.TeleBot('6722988693:AAGEc14l61QHXCY8R8gEcTKw3_QrcooLK_o')
num = ''


@bot.message_handler(commands=['start'])
def main(message):
    conn = sqlite3.connect('targets.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS targets(id int, nickname text, phone text, creds text)")
    cur.execute("INSERT OR REPLACE INTO targets VALUES(?,?,?,?)", (message.from_user.id, "none", "none", "none"))
    conn.commit()
    cur.close()
    conn.close()

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = telebot.types.KeyboardButton("Відправити контакт", request_contact=True)
    markup.row(button)

    bot.send_message(message.chat.id, 'Добрий день! Для початку зареєструємось (бо ми не хочемо щоб хтось використовував наші ресурси без нашого відома). Просто натисніть кнопку Відправити контакт, щоб продовжити', reply_markup=markup)
    bot.register_next_step_handler(message, phone_reg)


def phone_reg(message):
    global num
    try:
        num = message.contact.phone_number
    except AttributeError:
        bot.send_message(message.chat.id, "Ви маєте відправити саме контакт. Спробуйте знову")
        bot.register_next_step_handler(message, phone_reg)
    else:
        bot.send_message(message.chat.id, "Добре, тепер введіть ваше прізвище та ім'я")
        bot.register_next_step_handler(message, creds_reg)


def creds_reg(message):
    creds = message.text
    creds_n = "_".join(creds.split())
    conn = sqlite3.connect('targets.db')
    cur = conn.cursor()
    if message.from_user.username is not None:
        cur.execute("UPDATE targets SET nickname=?, phone=?, creds=? WHERE id=?", (message.from_user.username, num, creds_n, message.from_user.id))
    else:
        cur.execute("UPDATE targets SET nickname=?, phone=?, creds=? WHERE id=?", ("none", num, creds_n, message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, "Успішно зареєстровано! Можете відправляти фото об'єктів для реконструкції")


@bot.message_handler(commands=['help'])
def main(message):
    bot.send_message(message.chat.id, 'Якщо бот не відправляє реконструкцію, почекайте, таких як ви багато, а сервер слабкий')


@bot.message_handler(commands=['unreg'])
def main(message):
    clear_dir(f'video/{message.chat.id}')

    conn = sqlite3.connect('targets.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM targets WHERE id = ?", (message.from_user.id, ))
    conn.commit()
    cur.close()
    conn.close()

    conn = sqlite3.connect('django3d/db.sqlite3')
    cur = conn.cursor()
    cur.execute("DELETE FROM viewer_modelmodel WHERE id = ?", (message.from_user.id, ))
    cur.execute("DELETE FROM viewer_litemodelmodel WHERE id = ?", (message.from_user.id,))
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, 'Данні про вас успішно очищено')


@bot.message_handler(content_types=['video'])
def get_video(message):
    conn = sqlite3.connect('django3d/db.sqlite3')
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO viewer_modelmodel (id) VALUES (?)", (int(message.from_user.id),))
    cur.execute("INSERT OR REPLACE INTO viewer_litemodelmodel (id) VALUES (?)", (int(message.from_user.id),))
    conn.commit()
    cur.close()
    conn.close()
    file_id = message.video.file_id
    file_path = bot.get_file(file_id).file_path
    file_name = file_path.split("/")[-1]

    folder_path = f'videos/{message.chat.id}'

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with open(os.path.join(folder_path, file_name), "wb") as code:
        code.write(bot.download_file(file_path))

    bot.reply_to(message, 'Завантажую відео...')
    time.sleep(1)
    bot.edit_message_text(chat_id=message.chat.id, text='Нарізка на кадри...', message_id=message.id+1)
    time.sleep(3)
    bot.edit_message_text(chat_id=message.chat.id, text='Запуск швидкої моделі (приблизно 20с на 1 запит)', message_id=message.id+1)
    time.sleep(5)
    bot.edit_message_text(chat_id=message.chat.id, text='Відправляю .obj ...', message_id=message.id+1)
    time.sleep(1)
    file = open("./requirements.txt")
    bot.send_document(message.chat.id, file)

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    btn = telebot.types.InlineKeyboardButton('Відкрити модель у браузері', url=f'http://127.0.0.1:8080/sfm/{message.from_user.id}')
    markup.add(btn)

    bot.send_message(message.chat.id, 'Готово! Якщо посилання зламане, 3д модель можна відкрити на сайті https://3dviewer.net/', reply_markup=markup)
    bot.reply_to(message, f'ID: {message.from_user.id}')


bot.polling(none_stop=True)
