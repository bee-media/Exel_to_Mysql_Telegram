# 📅 on_friday_avr — Бот для загрузки графика дежурств

> Telegram-бот для автоматизации загрузки графика дежурств в базу данных MySQL.  
> Отправляет напоминание админам о необходимости загрузить график за день до окончания месяца.

---

## 🧰 Функционал

- ✅ Загрузка Excel-файла `chs.xlsx` с расписанием.
- 🗂 Сохранение данных из файла в MySQL.
- 🧹 Очистка таблицы перед обновлением данных.
- 🕒 Автоматическое ежемесячное напоминание администраторам (через APScheduler).
- 🤖 Поддержка команд: `/start`, `/status`, `/show`.
- 🛡 Проверка прав доступа: только администраторы могут взаимодействовать с ботом.

---

## 🛠 Технологии

- Python 3.8+
- [`telebot`](https://github.com/eternnoir/pyTelegramBotAPI)  — для работы с Telegram API
- [`mysql-connector-python`](https://dev.mysql.com/doc/connector-python/en/)  — для работы с MySQL
- [`pandas`](https://pandas.pydata.org/)  — для обработки Excel-файлов
- [`apscheduler`](https://apscheduler.readthedocs.io/)  — для планирования задач
- [`python-dotenv`](https://github.com/theskumar/python-dotenv)  — для хранения секретов
- [`pytz`](https://pypi.org/project/pytz/)  — работа с часовыми поясами
