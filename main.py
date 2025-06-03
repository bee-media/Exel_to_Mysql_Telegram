import pandas as pd
import mysql.connector
import telebot
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import calendar
import pytz

# данные для подключения к базе данных
db_config = {
    'host': '10.10.10.10',
    'database': 'duty',
    'user': 'admin',
    'password': 'admin'
}
table_name = 'on_friday_avr'

# список администраторов (Telegram user IDs)
admins = [01010101]  # замените на реальные user IDs администраторов

# создайте экземпляр бота
bot_token = 'TOKEN'  # токен бота
bot = telebot.TeleBot(bot_token)

# функция для отправки уведомления админу
def send_schedule_reminder():
    try:
        for admin_id in admins:
            bot.send_message(admin_id, "Напоминание!\nПожалуйста, загрузите новый график на следующий месяц.\nНазвание файла обязательно 'chs.xlsx'")
    except Exception as e:
        notify_admins(f"Ошибка при отправке напоминания: {str(e)}")

# функция для уведомления администраторов об ошибке
def notify_admins(error_message):
    for admin_id in admins:
        bot.send_message(admin_id, f"Произошла ошибка: {error_message}")

# функция для определения последнего дня месяца
def get_last_day_of_month():
    today = datetime.now(pytz.timezone('Europe/Moscow'))  # текущее время с локализацией
    last_day = calendar.monthrange(today.year, today.month)[1]  # последний день месяца
    return today.replace(day=last_day, hour=12, minute=0, second=0, microsecond=0)  # 12:00 последнего дня

# Планировщик для отправки сообщения
def schedule_job():
    try:
        scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))  # указание временной зоны для планировщика

        # Определяем время для выполнения задачи в этом месяце
        next_run_time = get_last_day_of_month()

        # Если текущее время уже прошло, планируем на следующий месяц
        if datetime.now(pytz.timezone('Europe/Moscow')) > next_run_time:
            # Переходим на следующий месяц
            next_month = next_run_time.replace(day=1) + timedelta(days=calendar.monthrange(next_run_time.year, next_run_time.month + 1)[1])
            next_run_time = next_month.replace(day=calendar.monthrange(next_month.year, next_month.month)[1], hour=12, minute=0)

        # Устанавливаем задачу на выполнение
        scheduler.add_job(send_schedule_reminder, 'date', run_date=next_run_time)
        
        # Запуск планировщика
        scheduler.start()
    except Exception as e:
        notify_admins(f"Ошибка в планировщике: {str(e)}")

# функция для записи данных из Excel в базу данных
def write_to_db(excel_file_path):
    try:
        # чтение данных из файла Excel
        data = pd.read_excel(excel_file_path, engine='openpyxl')

        # установка соединения с базой данных
        db_connection = mysql.connector.connect(**db_config)
        db_cursor = db_connection.cursor()

        # очистка таблицы перед добавлением новых данных
        db_cursor.execute(f"TRUNCATE TABLE `{table_name}`")

        # добавление данных в таблицу
        for _, row in data.iterrows():
            sql = f"INSERT INTO `{table_name}` (`name`, `date`, `time`, `money`) VALUES (%s, %s, %s, %s)"
            values = (row.iloc[0], row.iloc[1].strftime("%Y-%m-%d"), row.iloc[2], row.iloc[3])
            db_cursor.execute(sql, values)

        # коммит изменений
        db_connection.commit()

        # закрытие соединения
        db_cursor.close()
        db_connection.close()

        return "Данные успешно загружены в базу данных!"
    except Exception as e:
        notify_admins(f"Ошибка при загрузке данных в базу: {str(e)}")
        return f"Ошибка при загрузке данных: {str(e)}"

# функция для чтения всех данных из базы данных и форматирования их для отправки
def read_from_db():
    try:
        # установка соединения с базой данных
        db_connection = mysql.connector.connect(**db_config)
        db_cursor = db_connection.cursor()

        # выполнение запроса для получения всех данных из таблицы
        db_cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = db_cursor.fetchall()

        # форматирование данных для отправки
        data_str = "Текущие данные в базе:\n\n"
        for row in rows:
            data_str += f"ID: {row[0]}, Имя: {row[1]}, Дата: {row[2]}, Время: {row[3]}, Оплата: {row[4]}\n"

        # закрытие соединения
        db_cursor.close()
        db_connection.close()

        return data_str
    except Exception as e:
        notify_admins(f"Ошибка при чтении данных из базы: {str(e)}")
        return f"Ошибка при чтении данных: {str(e)}"

# обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id

    # проверка, является ли пользователь администратором
    if user_id not in admins:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return

    bot.reply_to(message, "Привет! Отправьте файл Excel с именем 'chs.xlsx' для загрузки данных в базу.")

# обработчик команды /status
@bot.message_handler(commands=['status'])
def send_status(message):
    user_id = message.from_user.id

    # проверка, является ли пользователь администратором
    if user_id not in admins:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return

    bot.reply_to(message, "Привет! Я живой! Отправь мне файл. Файл должен называться так: chs.xlsx")

# обработчик файлов
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id

    # проверка, является ли пользователь администратором
    if user_id not in admins:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return

    # получение файла
    document = message.document
    file_name = document.file_name

    # проверка имени и расширения файла
    if file_name != 'chs.xlsx':
        bot.reply_to(message, "Пожалуйста, отправьте файл с именем 'chs.xlsx'")
        return

    # скачивание файла
    try:
        file_info = bot.get_file(document.file_id)
        file_path = f"./{file_name}"  # использовать текущую рабочую директорию
        downloaded_file = bot.download_file(file_info.file_path)

        # запись файла на диск
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # загрузка данных в базу
        status = write_to_db(file_path)

        # удаление файла после использования
        os.remove(file_path)

        # отправка статуса выполнения
        bot.reply_to(message, status)

        # чтение данных из базы и отправка их администратору
        data_message = read_from_db()
        for admin_id in admins:
            bot.send_message(admin_id, data_message)

    except Exception as e:
        notify_admins(f"Ошибка при обработке файла: {str(e)}")
        bot.reply_to(message, f"Ошибка при обработке файла: {str(e)}")

# запуск бота и планировщика
if __name__ == '__main__':
    try:
        print("Бот запущен")
        
        # Запуск планировщика напоминаний
        schedule_job()
        
        # Запуск бота
        bot.polling(none_stop=True)

    except Exception as e:
        notify_admins(f"Ошибка при запуске бота: {str(e)}")
