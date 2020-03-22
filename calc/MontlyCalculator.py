import logging
from decimal import Decimal
from functools import partial

from calc.BalanceCalculator import calculate_balance_at_closing_of, calculate_balance_at_opening_of, \
    transactions_between
from fin.Caml52Parser import CREDIT, DEBIT
from util.DecimalUtils import from_cents


def transaction_amount(t):
    return from_cents(t["amount"] if t["credit"] == CREDIT() else (-t["amount"]))


def other_party(t):
    return t["debitor"] if t["credit"] == CREDIT() else t["creditor"]


def transactions_balance(transactions, filter_fn):
    ftransactions = list(filter(filter_fn, transactions))

    sum = Decimal(0)
    for t in ftransactions:
        sum = sum + transaction_amount(t)

    return sum, [x for x in transactions if x not in ftransactions], ftransactions


all_categories = [
    {"category": "Gehalt / Lohn", "amount": "positive", "contains": ["gehalt"]},

    {"category": "Miete, Gas & Strom", "amount": "negative", "contains": ["lichtblick", "eswe", "miete", "kaution"]},
    {"category": "Versicherungen", "amount": "negative", "contains": ["krankenvers."]},
    {"category": "Lebensmittel", "amount": "negative", "contains": ["rewe", "real", "edeka", "lidl", "kaufland"]},
    {"category": "Online-Shopping", "amount": "negative", "contains": ["amazon", "alibaba", "aliexpress", "paypal"]},
    {"category": "Tanken", "amount": "negative", "contains": ["tanken", "tankstelle", "esso", "aral", "jet"]},
    {"category": "Restaurant & Liefern", "amount": "negative",
     "contains": ["restaurant", "burger king", "burger-king", "mcdonalds"]},
    {"category": "Telefon, Internet & Fernsehen", "amount": "negative",
     "contains": ["vodafone", "congstar", "telekom", "unitymedia", "rundfunk"]},
    {"category": "Möbel & Baumarkt", "amount": "negative", "contains": ["ikea", "baumarkt", "obi", "hornbach"]},
    {"category": "Lifestyle", "amount": "negative", "contains": ["friseur"]},
    {"category": "Sonstiges Einkaufen", "amount": "negative", "contains": ["saturn", "galeria", "karstadt"]},
    {"category": "Sparen", "amount": "negative", "contains": ["onvista"]},
    {"category": "Barabhebung", "amount": "negative", "contains": ["abhebung"]}
]


def get_categories_balances(relevant_transactions):
    def filter_method(cat, t):
        str = (other_party(t) + " " + t["reason"] + " " + t["additional_reason"]).lower()

        if (transaction_amount(t) < Decimal(0) and t["amount"] == "positive") or (
                transaction_amount(t) >= Decimal(0) and t["amount"] == "negative"):
            return False

        if any(substr in str for substr in cat["contains"]):
            return True

        return False

    result = []

    remaining_transactions = relevant_transactions
    for cat in all_categories:
        balance, remaining_transactions, used_transactions = transactions_balance(remaining_transactions,
                                                                                  partial(filter_method, cat))

        result.append((cat["category"], balance, used_transactions))

    remaining_expenses_balances, remaining_transactions, used_transactions = transactions_balance(
        remaining_transactions, lambda t: transaction_amount(t) <= Decimal(0))
    result.append(("Sonstige Ausgaben", remaining_expenses_balances, used_transactions))

    remaining_income_balances, remaining_transactions, used_transactions = transactions_balance(remaining_transactions,
                                                                                                lambda
                                                                                                    t: transaction_amount(
                                                                                                    t) > Decimal(0))
    result.append(("Sonstige Einnahmen", remaining_income_balances, used_transactions))

    return result


def calculate_range(fints, account, range_begin, range_end):
    current_account_balance = fints.get_old_account_balance(account)

    if current_account_balance is None:
        logging.debug(f"Could not fetch all_transactions_to_start for account {account.iban}")
        return None

    all_transactions_to_start = list(fints.get_transactions_from_begin(range_begin, account))

    # Alle Transaktionen innerhalb des abgefragten Zeitraums
    relevant_transactions = transactions_between(all_transactions_to_start, range_begin, range_end)

    incoming = transactions_balance(relevant_transactions, lambda t: t["credit"] == CREDIT())[0]
    outcoming = transactions_balance(relevant_transactions, lambda t: t["credit"] == DEBIT())[0]

    start_last_month_balance = calculate_balance_at_opening_of(range_begin, all_transactions_to_start,
                                                               current_account_balance)
    end_last_month_balance = calculate_balance_at_closing_of(range_end, all_transactions_to_start,
                                                             current_account_balance)

    logging.debug(f"Account {account.iban}: ")
    logging.debug(f"Current Account Balance: ${from_cents(current_account_balance)}")
    logging.debug(f"Saldo am Beginn: ${start_last_month_balance})")
    logging.debug(f"Saldo am Ende: ${end_last_month_balance})")

    categories_balances = sorted(get_categories_balances(relevant_transactions),
                                 key=lambda x: (("AA" if x[1] > 0 else "BB"), x[0]))

    logging.debug("")
    logging.debug(f"Eingänge: {incoming}")
    logging.debug(f"Ausgänge: {outcoming}")
    logging.debug("")

    for cat, bal, trans in categories_balances:
        logging.debug(f"{cat}: {bal}")

#
# db = dataset.connect('sqlite:///main.db')
#
# fints = FinTSClient(db)
#
# with fints:
#     fints.insert_new_transactions_into_database()
#     calculate_range(fints, fints.get_accounts()[0], datetime(2020, 3, 1).date(), datetime(2020, 3, 18).date())
