import threading
import urllib.request
from urllib.parse import quote

from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from time import sleep, ctime
import os
import signal

# path = "/home/flo/PycharmProjects/Privat/"
#path = "/home/pi/"
#path = "/app/files/"
path = "files/"


def pc_started():
    while not return_to_updater:
        global mutex
        sleep(10)
        mutex.acquire()
        f = open(path + "status.txt", "r")
        if f.read(1) != "1":
            f.close()
            os.system("truncate -s 0 status.txt")
            f = open(path + "status.txt", "w")
            f.write("1")
            text = "Pc started normal"
            urllib.request.urlopen(
                f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={user_id}&text={quote(text)}")
            log("PC started (normal)")
            f.close()
        else:
            f.close()
        mutex.release()


def log(message):
    log_path = path + "telegram_bot.log"
    f = open(log_path, "a")
    f.write(str(ctime()) + f" {message}\n")
    f.close()
    print(message)


# Program start
try:
    help_message = '''The following functions are available:
        /help -> Help message.
        /stop -> End bot.
        /awake -> Check if bot is still running.

        /apache_res -> Restart apache2 service.
        /start_pc -> Start PC Innsbruck.
        '''
    api_key = os.environ['TELEGRAM_API_KEY']
    user_id = os.environ['TELEGRAM_USER_ID']
    # https://api.telegram.org/bot5184299088:AAHmvs1-caQXm4FnkkIqxpD0RUgx7H4DZ-I/sendMessage?chat_id=66513226&text=hi

    start_text = f"Bot started.\n\n {help_message}"
    urllib.request.urlopen(
        f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={user_id}&text={quote(start_text)}")
    log("Bot started.")

    updater = Updater(api_key, use_context=True)
    return_to_updater = False

    mutex = threading.Lock()
    thread = threading.Thread(target=pc_started)
    thread.start()


    # Functions Bot
    def start(update: Update, context: CallbackContext):
        update.message.reply_text(
            "Bot started.")


    def help(update: Update, context: CallbackContext):
        update.message.reply_text(help_message)


    def apache2_restart(update: Update, context: CallbackContext):
        out = os.system("systemctl restart apache2")
        log(f"Return code apache restart: {out}")
        if out != 0:
            update.message.reply_text("Apache2: Restart failed.")
            log("Apache2: Restart failed.")
        else:
            update.message.reply_text("Apache2: Restarting.")
            log("Apache2: Restarting.")


    def unknown_text(update: Update, context: CallbackContext):
        update.message.reply_text(
            "Sorry I can't recognize you , you said '%s'" % update.message.text)


    def unknown(update: Update, context: CallbackContext):
        update.message.reply_text(
            "Sorry '%s' is not a valid command" % update.message.text)


    def stop(update: Update, context: CallbackContext):
        update.message.reply_text("Bot stopped.")
        log("Bot stopped.")
        os.kill(os.getpid(), signal.SIGTERM)


    def rtu(update: Update, context: CallbackContext):
        return_to_updater = True
        update.message.reply_text("Aborted all loops.")
        return_to_updater = False


    def awake(update: Update, context: CallbackContext):
        log("Still awake.")
        update.message.reply_text("Still awake...")


    def start_pc(update: Update, context: CallbackContext):  # evt ssh into router und dort ping blockieren
        global mutex
        log("Start PC")
        mutex.acquire()
        out = os.system("echo 0 > /proc/sys/net/ipv4/icmp_echo_ignore_all")
        log(f"Return code ping block: {out}")
        # print(f"Return code ping block: {out}")
        if out != 0:
            log("Ping block failed.")
            update.message.reply_text("Ping block failed.")
        else:
            log("Ping block successfull")
            while return_to_updater != True:
                f = open(path + "status.txt", "r")
                if f.read(1) != "1":
                    f.close()
                    break
                else:
                    f.close()
                    sleep(1)
            os.system("truncate -s 0 status.txt")
            f = open(path + "status.txt", "w")
            f.write("1")
            f.close()
            out = os.system("echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_all")
            log("PC started")
            update.message.reply_text("Pc started")
        mutex.release()


    def network_restart(update: Update, context: CallbackContext):
        log("Restart network")
        out = os.system("ifdown eth0 wlan0 && ifup eth0 wlan0")  # anderes interface noch einfügen
        if out != 0:
            log("Network restart failed.")
            update.message.reply_text("Network restart failed.")
        else:
            log("Network restart successful.")
            update.message.reply_text("Network restart successful.")


    def pi_restart(update: Update, context: CallbackContext):
        log("Restart pi")
        out = os.system("reboot")
        if out != 0:  # sollte nicht erreicht werden, da zuvor reboot
            log("Pi restart failed.")
            update.message.reply_text("Pi restart failed.")
        else:
            log("Pi restart successful.")
            update.message.reply_text("Pi restart successful.")


    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('stop', stop))
    updater.dispatcher.add_handler(CommandHandler('rtu', rtu))
    updater.dispatcher.add_handler(CommandHandler('awake', awake))

    updater.dispatcher.add_handler(CommandHandler('apache_res', apache2_restart))
    updater.dispatcher.add_handler(CommandHandler('network_res', network_restart))

    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler('start_pc', start_pc))

    updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))  # unknown command
    updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))  # unknown text

    # https://api.telegram.org/bot{api_key}/sendMessage?chat_id=5184299088&text=started
    # urllib.request.urlopen(f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={user_id}&text={start_text}")

    # bot.getUpdates

    # 5184299088
    # print("Bot started.")
    updater.start_polling()
except Exception as e:
    urllib.request.urlopen(f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={user_id}&text={e}")
    log(e)