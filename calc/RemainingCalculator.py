import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import dataset

from calc.BalanceCalculator import transactions_between
from calc.MontlyCalculator import other_party, transactions_balance
from fin.FinTS import FinTSClient
from util.DateUtils import remaining_days_of_month
from util.DecimalUtils import from_cents

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)

expected_transactions = [
    {"category": "Gehalt / Lohn", "contains": ["gehalt"], "last_amount": from_cents(264124), "divisor": 1},
    {"category": "Rundfunkbeitrag", "contains": ["rundfunk"], "last_amount": -from_cents(5250), "divisor": 3},
    {"category": "Handy (Congstar)", "contains": ["congstar"], "last_amount": -from_cents(1200), "divisor": 1},
    {"catgeory": "Johanna (Taschengeld)", "contains": ["hemmer"], "last_amount": -from_cents(14000), "divisor": 1},
    {"catgeory": "Krankenversicherung", "contains": ["krankenvers."], "last_amount": -from_cents(22348), "divisor": 1},
    {"catgeory": "Internet (Unitymedia)", "contains": ["vodafone"], "last_amount": -from_cents(998), "divisor": 1},
    {"category": "Miete", "contains": ["mietkonto"], "last_amount": -from_cents(51500), "divisor": 1},
    {"category": "Haftpflichtversicherung", "contains": ["cosmos", "haftpflicht"], "last_amount": -from_cents(4059),
     "divisor": 12},
    {"category": "Strom", "contains": ["strom"], "last_amount": -from_cents(3350), "divisor": 1},
    {"category": "Gas", "contains": ["gas"], "last_amount": -from_cents(5200), "divisor": 1},
    {"category": "Sport (PowerGym)", "contains": ["powergym"], "last_amount": -from_cents(3750), "divisor": 3},
    {"category": "Sparplan", "contains": ["sparen"], "last_amount": -from_cents(50000), "divisor": 1},
]


def calc_remaining(fints, account, range_begin, range_end):
    logging.debug(f"enter calc_remaining: {account} begin {range_begin} end {range_end}")

    all_transactions_to_start = list(fints.get_transactions_from_begin(range_begin, account))

    # Alle Transaktionen innerhalb des abgefragten Zeitraums
    relevant_transactions = transactions_between(all_transactions_to_start, range_begin, range_end)

    logging.debug(f"all relevant transactions {relevant_transactions}")

    remaining_transactions = []
    for rt in relevant_transactions:

        def matches_expected():
            for et in expected_transactions:
                str = (other_party(rt) + " " + rt["reason"] + " " + rt["additional_reason"]).lower()

                if any(substr in str for substr in et["contains"]):
                    logging.debug(f"match found {str} ignoring")
                    return et

            return False

        if not matches_expected():
            remaining_transactions.append(rt)

    logging.debug(f"remaining transactions {remaining_transactions}")

    return transactions_balance(remaining_transactions, lambda t: True)[0]


@dataclass
class RemainingMoneyResult:
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_available: Decimal

    remaining: Decimal
    remaining_per_day: Decimal


def calc_remaining_in_month(fints: FinTSClient, range_start, range_end) -> RemainingMoneyResult:
    result = calc_remaining(fints, fints.get_accounts()[0], range_start, range_end)

    monthly_ins = sum([x['last_amount'] / x['divisor'] for x in expected_transactions if x['last_amount'] > 0])
    monthly_outs = sum([x['last_amount'] / x['divisor'] for x in expected_transactions if x['last_amount'] <= 0])

    logging.debug(f"Monatliche Einnahmen: {monthly_ins} EUR")
    logging.debug(f"Monatliche Ausgaben: {monthly_outs} EUR")
    logging.debug(f"Verfügbar: {monthly_ins + monthly_outs} EUR")

    logging.debug(result)

    return RemainingMoneyResult(monthly_ins, monthly_outs, monthly_ins + monthly_outs, result,
                                result / remaining_days_of_month(range_end))
