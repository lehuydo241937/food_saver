import json
import requests
import configparser
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

def getProxy():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return {config.get('proxy', 'proxyMethod') : config.get('proxy', 'proxySock')}

def getSender(req):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if req in ('SENDER_ADDRESS', 'SENDER_PASS', 'BOT_TOKEN'):
        res = config.get('sender',req)
        return res
    else:
        raise Exception(f'INVALID SENDER ELEMENT: {req}. \nElement must be "SENDER_ADDRESS", "SENDER_PASS" or "BOT_TOKEN"')

def telegram_send_mesage(chat_id, content, bot_token):
    '''
    use the telegram message created to send it via a Telegram chat bot
    '''
    api_telegram = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    header = {'Content-Type': 'application/json'}
    body_tele = {
        "chat_id": chat_id,
        "text": content
    }
    data = json.dumps(body_tele)
    req = requests.post(api_telegram, data=data, headers=header, timeout=180)
    result = req.json()
    status = result['ok']
    error = result['description'] if not status else ''
    return status , error

def df_to_mess(df):
    mess = ''
    for i, row in df.iterrows():
        mess += f'{i+1}. {row["NAME"]} - {row["CAT"]}\n{row["LINK"]}\n'
    return mess

# proxy_dict = getProxy()
BOT_TOKEN = getSender('BOT_TOKEN')
chat_id = '-1002197429285'
CSV_FILE_PATH = "menu.csv"
# chat_id = '-909763603' #test

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def initialize_csv():
    try:
        df = pd.read_csv(CSV_FILE_PATH, sep='|')
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Item"])
        df.to_csv(CSV_FILE_PATH, index=False)

async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        df = pd.read_csv(CSV_FILE_PATH, sep='|')
        if df.empty:
            await update.message.reply_text("Menu rỗng không à!")
        else:
            await update.message.reply_text(f"{df_to_mess(df)}")
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        await update.message.reply_text("Lỗi rồi :((((.")

async def add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("add menu called", context)
    try:
        # Ensure the user provided all necessary arguments
        if len(context.args) < 3:
            await update.message.reply_text("Sai rùi. Thử lại đi!\n/sendmenu@PTDL_AR_bot <Tên quán> - <Cơ sở> - <Link>")
            return

        input = " ".join(context.args).split('-')
        name = input[0].strip()
        cat = input[1].strip()
        link = input[2].strip()

        # Read the existing CSV file
        df = pd.read_csv(CSV_FILE_PATH, delimiter="|")

        # Append the new row
        new_row = {"NAME": name, "CAT": cat, "LINK": link}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.drop_duplicates(inplace=True)
        # Save the updated DataFrame back to the CSV file
        df.to_csv(CSV_FILE_PATH, index=False, sep="|")

        # Notify the user of success
        await update.message.reply_text(f"Đã thêm {name} vào menu. Nhớ đặt lịch đi ăn đó!!!!")
    except Exception as e:
        logger.error(f"Error updating CSV: {e}")
        await update.message.reply_text("Sai rùi. Thử lại đi!\n/sendmenu@PTDL_AR_bot <Tên quán> - <Cơ sở> - <Link>")


async def delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Ensure the user provided the name of the item to delete
        if len(context.args) < 1:
            await update.message.reply_text("Sai rùi. Thử lại đi!\n/deletemenu@PTDL_AR_bot <NAME>")
            return

        # Get the name of the item to delete
        name_to_delete = " ".join(context.args)

        # Read the existing CSV file
        df = pd.read_csv(CSV_FILE_PATH, delimiter="|")

        # Check if the item exists in the menu
        if not df[df["NAME"] == name_to_delete].empty:
            # Remove the row(s) with the given name
            df = df[df["NAME"] != name_to_delete]

            # Save the updated DataFrame back to the CSV file
            df.to_csv(CSV_FILE_PATH, index=False, sep="|")

            # Notify the user of success
            await update.message.reply_text(f"Món '{name_to_delete}' đã bay màu khỏi menu.")
        else:
            # Notify the user if the item was not found
            await update.message.reply_text(f"Không tìm thấy món '{name_to_delete}' đâu cả :D.")

    except Exception as e:
        logger.error(f"Error deleting item from CSV: {e}")
        await update.message.reply_text("Không tìm thấy món '{name_to_delete}' đâu cả :D.")



def main():
    initialize_csv()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("sendmenu", send_menu))
    application.add_handler(CommandHandler("addmenu", add_menu))
    application.add_handler(CommandHandler("deletemenu", delete_menu))
    application.run_polling()

if __name__ == '__main__':
    main()
