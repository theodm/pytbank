import datetime
from decimal import Decimal

import pytest

from calc.BalanceCalculator import calculate_balance_at_opening_of


def test_answer():
    date_opening_of = dt(2020, 1, 1)
    latest_balance = 100_00
    transactions = [
        {"amount": 1_00, "credit": "DBIT", "creditor": "REWE", "debitor": "Theo", "valuta_date": dt(2020, 1, 1)},
        {"amount": 5_00, "credit": "DBIT", "creditor": "Edeka", "debitor": "Theo", "valuta_date": dt(2019, 1, 1)},
        {"amount": 6_00, "credit": "DBIT", "creditor": "Edeka", "debitor": "Theo", "valuta_date": dt(2020, 5, 5)},
        {"amount": 3_00, "credit": "CRDT", "creditor": "Theo", "debitor": "Beihilfe", "valuta_date": dt(2020, 5, 5) },
    ]

    new_balance = calculate_balance_at_opening_of(date_opening_of, transactions, latest_balance)

    assert new_balance == Decimal(104)


def dt(y, m, d):
    return datetime.datetime(y, m, d).date()
