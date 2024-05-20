import re
import os
import logging
import paramiko
import psycopg2
import subprocess

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
HOST = os.getenv('RM_HOST')
PORT = os.getenv('RM_PORT')
USER = os.getenv('RM_USER')
PASS = os.getenv('RM_PASSWORD')

logging.basicConfig(
    level=logging.INFO, filename='TelegramBot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}!')
    logging.info(f'Начата работа с пользователем {user.username}')

def find_phone_number(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров')
    return 'find_phone_number_input'

def find_phone_number_input(update: Update, context):
    logging.info("Запрос на поиск номер телефона - find_phone_number")
    
    user_input = update.message.text 
    phoneNumRegex = re.compile(r'((?:\+7|8)[- ]?(?:\(\d{3}\)|\d{3})[- ]?\d{3}[- ]?\d{2}[- ]?\d{2})\b')
    phoneNumberList = phoneNumRegex.findall(user_input) 

    if not phoneNumberList:
        update.message.reply_text('Номера телефонов не найдены')
        return ConversationHandler.END
    else:
        return ask_to_save(update, context, 'number', phoneNumberList)

def save_data_to_db(data_type, data_list):
    connection = None
    try:
        connection = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_DATABASE')
        )
        cursor = connection.cursor()
        for data in data_list:
            if data_type == "number":
                cursor.execute("INSERT INTO phonenumbers (number) VALUES (%s);", (data,))
            elif data_type == "email":
                cursor.execute("INSERT INTO emails (email) VALUES (%s);", (data,))
        connection.commit()
        logging.info("Данные сохранены в БД")
        return "Данные успешно сохранены."
    except (Exception) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        return "Ошибка при сохранении данных."
    finally:
        if connection:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")

def ask_to_save(update: Update, context: CallbackContext, data_type, data_list):
    if not data_list:
        update.message.reply_text('Данные для сохранения не найдены')
        return ConversationHandler.END

    update.message.reply_text(f'Найденные {data_type}:\n' + '\n'.join(f'{i+1}. {data}' for i, data in enumerate(data_list)))
    update.message.reply_text('Желаете сохранить эти данные? Ответьте "да" или "нет"')
    context.user_data['data_type'] = data_type
    context.user_data['data_list'] = data_list
    return 'save_data'

def save_data(update: Update, context: CallbackContext):
    user_input = update.message.text.lower()
    if user_input == 'да':
        result = save_data_to_db(context.user_data['data_type'], context.user_data['data_list'])
        update.message.reply_text(result)
    else:
        update.message.reply_text('Сохранение отменено.')
    return ConversationHandler.END

def find_email(update: Update, context: CallbackContext):
    update.message.reply_text('Введите текст для поиска email-адресов')
    return 'find_email_input'

def find_email_input(update: Update, context: CallbackContext):
    logging.info("Запрос на поиск email-адресов")
    user_input = update.message.text
    emailRegex = re.compile(
        r'(?<!\S)(?:[A-Za-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.(?!$)[A-Za-z0-9!#$%&\'*+/=?^_`{|}~-]+)*|'
        r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@'
        r'(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}'
    )
    emailList = emailRegex.findall(user_input)
    
    if not emailList:
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END
    else:
        return ask_to_save(update, context, 'email', emailList)

def checkPass(update: Update, context):
    update.message.reply_text("Введите пароль для проверки")
    return 'verify_password'

def verify_password(update: Update, context):
    logging.info("Запрос на проверку надежности пароля - verify_password")
    user_input = update.message.text
    passRegex = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$')

    if not passRegex.match(user_input):
        update.message.reply_text("Пароль слабый")
        return ConversationHandler.END

    update.message.reply_text("Пароль сильный")
    return ConversationHandler.END

def ssh_command(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=HOST, username=USER, password=PASS, port=PORT)
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()
        client.close()
        return str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    except Exception as e:
        logging.error(f"SSH Error: {str(e)}")
        return str(e)

def get_release(update: Update, context):
    logging.info("Запрос информации о релизе")
    result = ssh_command('cat /etc/*release')
    update.message.reply_text(result)

def get_uname(update: Update, context):
    logging.info("Запрос информации о системе")
    result = ssh_command('uname -a')
    update.message.reply_text(result)

def get_uptime(update: Update, context):
    logging.info("Запрос времени работы системы")
    result = ssh_command('uptime')
    update.message.reply_text(result)

def get_df(update: Update, context):
    logging.info("Запрос информации о состоянии файловой системы")
    result = ssh_command('df -h')
    update.message.reply_text(result)

def get_free(update: Update, context):
    logging.info("Запрос информации о состоянии оперативной памяти")
    result = ssh_command('free -h')
    update.message.reply_text(result)

def get_mpstat(update: Update, context):
    logging.info("Запрос информации о производительности системы")
    result = ssh_command('mpstat')
    update.message.reply_text(result)

def get_w(update: Update, context):
    logging.info("Запрос информации о работающих пользователях")
    result = ssh_command('w')
    update.message.reply_text(result)

def get_auths(update: Update, context):
    logging.info("Запрос последних 10 входов в систему")
    result = ssh_command('last -n 10')
    update.message.reply_text(result)

def get_critical(update: Update, context):
    logging.info("Запрос последних 5 критических событий")
    result = ssh_command(f'echo {PASS} | sudo -S grep CRITICAL /var/log/syslog | tail -n 5')
    update.message.reply_text(result)

def get_ps(update: Update, context):
    logging.info("Запрос информации о запущенных процессах")
    result = ssh_command('ps aux --sort=-\%cpu | head -n 20')
    update.message.reply_text(result)

def get_ss(update: Update, context):
    logging.info("Запрос информации об используемых портах")
    result = ssh_command('ss -tuln')
    update.message.reply_text(result)

def get_services(update: Update, context):
    logging.info("Запрос информации о запущенных сервисах")
    result = ssh_command('systemctl list-units --type=service --state=running')
    update.message.reply_text(result)

def get_apt_list(update: Update, context):
    logging.info("Запрос информации об установленных пакетах")
    args = context.args
    if args:
        package_name = ' '.join(args)
        command = f'apt list --installed | grep {package_name}'
    else:
        command = 'apt list --installed | head -n 20'

    result = ssh_command(command)
    update.message.reply_text(result or "Пакеты не найдены или команда выполнена с ошибкой.")

def get_repl_logs(update: Update, context):
    logging.info("Запрос логов репликации БД")
    #result = ssh_command(f'echo {PASS} | sudo -S cat /var/log/postgresql/postgresql-15-main.log | grep -iE "repl|connect" | tail -n 20')
    
    cat_process = subprocess.Popen(['cat', '/var/log/postgresql/postgresql-15-main.log'], stdout=subprocess.PIPE)
    grep_process = subprocess.Popen(['grep', '-iE', 'repl|connect'], stdin=cat_process.stdout, stdout=subprocess.PIPE)
    tail_process = subprocess.Popen(['tail', '-n', '20'], stdin=grep_process.stdout, stdout=subprocess.PIPE)
    output, _ = tail_process.communicate()
    result = output.decode('utf-8')    

    update.message.reply_text(result)

def select_bd_info(table):
    try:
        connection = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_DATABASE')
        )

        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table};")
        data = cursor.fetchall()
        answer = ""
        for row in data:
            answer += ' '.join(map(str, row)) + "\n" 
        if connection is not None:
            cursor.close()
            connection.close()
        return answer
    except (Exception) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        return error

def get_emails(update: Update, context):
    logging.info("Запрос сохраненных email-адресов")
    result = select_bd_info("emails")
    update.message.reply_text(result)

def get_phone_numbers(update: Update, context):
    logging.info("Запрос сохраненных номеров телефонов")  
    result = select_bd_info("phonenumbers")
    update.message.reply_text(result)
    
def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    find_phone_number_handler = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_number)],
        states={
            'find_phone_number_input': [MessageHandler(Filters.text & ~Filters.command, find_phone_number_input)],
            'save_data': [MessageHandler(Filters.text & ~Filters.command, save_data)]
        },
        fallbacks=[]
    )

    find_email_handler = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_email)],
        states={
            'find_email_input': [MessageHandler(Filters.text & ~Filters.command, find_email_input)],
            'save_data': [MessageHandler(Filters.text & ~Filters.command, save_data)]
        },
        fallbacks=[]
    )

    checkPassHandler = ConversationHandler(
        entry_points = [CommandHandler('verify_password', checkPass)],
        states = {
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks = []
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(find_phone_number_handler)
    dp.add_handler(find_email_handler)
    dp.add_handler(checkPassHandler)

    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()













