import logging
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from fin.Caml52Parser import CREDIT, DEBIT
from util.DecimalUtils import from_cents

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def transactions_between(transactions, date_start, date_end):
    return list(filter(lambda it: date_start <= it['valuta_date'] <= date_end, transactions))


def calculate_balance_at_opening_of(date_opening_of, transactions, latest_balance: int):
    latest_balance = from_cents(latest_balance)
    logging.debug(f"Es soll der Kontostand zum {date_opening_of} berechnet werden.")
    transactions_to_apply = list(filter(lambda it: it['valuta_date'] >= date_opening_of, transactions))

    logging.debug(f"{str(latest_balance).rjust(10)} | Aktueller Kontostand")
    logging.debug(f"")

    new_balance = latest_balance
    for t in transactions_to_apply:
        amount = from_cents(t["amount"])

        change = ((-amount) if t["credit"] == CREDIT() else amount)

        logging.debug(f'{str(change).rjust(10)} | {t["creditor"] if change > 0 else t["debitor"]} ')
        new_balance = new_balance + change

    logging.debug(f"{str(new_balance).rjust(10)} | Endstand")

    return new_balance

def calculate_balance_at_closing_of(date_closing_of, transactions, latest_balance):
    return calculate_balance_at_opening_of(date_closing_of + timedelta(days=1), transactions, latest_balance)

