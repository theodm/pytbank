import logging
import sys
import dataset
from decimal import Decimal

import requests
import telegram
from telegram import ParseMode
from telegram.ext import Updater, run_async, CallbackContext, CommandHandler

from calc.RemainingCalculator import calc_remaining_in_month
from fin.Caml52Parser import CREDIT, DEBIT
from util.DateUtils import get_current_month_range
from util.DecimalUtils import from_cents

from fin.FinTS import FinTSClient

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_id = 239559072

db = dataset.connect('sqlite:///main.db')

telegram_token = sys.argv[1]

updater = Updater(token=telegram_token, use_context=True)
dispatcher = updater.dispatcher

def create_fints_client():
    return FinTSClient(db, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

def search_new_transactions(context: CallbackContext):
    print("Suche nach neuen Transaktionen...")

    fints = create_fints_client()
    with fints:
        fints.insert_new_transactions_into_database()

        transactions = fints.get_all_new_transactions()

        print(f"Folgende Transaktionen wurden gefunden: {transactions}")

        for transaction in transactions:
            message = ""

            message += "\n"
            message += f'*{"Gutschrift" if transaction["credit"] == CREDIT() else "Abbuchung"}*: {transaction["debitor"] if transaction["credit"] == CREDIT() else transaction["creditor"]}\n'
            message += "\n"
            message += f'Betrag: *{from_cents(transaction["amount"])} EUR*\n'
            message += f'Datum: *{transaction["valuta_date"]}*\n'
            message += "\n"

            message += f'Verwendungszweck 1: *{transaction["reason"]}*\n'
            message += f'Verwendungszweck 2: *{transaction["additional_reason"]}*\n'
            message += "\n"

            updater.bot.send_message(
                chat_id=user_id, text=message, parse_mode=ParseMode.MARKDOWN
            )

            fints.set_transaction_sent(transaction["unique_id"])

        if not transactions:
            return
        #
        # month_begin, today = get_current_month_range()
        # remaining_result = calc_remaining_in_month(fints, month_begin, today)
        #
        # message = ""
        # message += f'Verbleibend in diesem Monat: *{max(remaining_result.remaining, Decimal(0))}* EUR\n'
        # message += f'Verbleibend in diesem Monat pro Tag: *{max(remaining_result.remaining_per_day, Decimal(0))}* EUR\n'
        # message += ""
        #
        # updater.bot.send_message(
        #     chat_id=user_id, text=message, parse_mode=ParseMode.MARKDOWN
        # )

        message = ""
        message += f'Neuer Kontostand: *{from_cents(fints.get_old_account_balance(fints.get_accounts()[0]))}* EUR'
        message += ""

        updater.bot.send_message(
            chat_id=user_id, text=message, parse_mode=ParseMode.MARKDOWN
        )

search_new_transactions(None)



#
# updater.job_queue.run_repeating(search_new_transactions, interval=5, first=0)
#
# updater.start_polling()
