import atexit
from datetime import date, timedelta
from typing import Callable

import dataset
from fints.client import NeedTANResponse, FinTS3PinTanClient
import logging

# Erstellt einen neuen FinTS3PinTanClient
# mit den übergebenen Bankdaten.
from fin.Caml52Parser import parseCaml52
from util.DictUtils import dict_without

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("fints").setLevel(logging.WARNING)

def create_client(blz, login_name, banking_pin, hbci_url):
    return FinTS3PinTanClient(
        blz,  # Your bank's BLZ
        login_name,  # Your login name
        banking_pin,  # Your banking PIN
        hbci_url
    )


# Diese Methode muss um alle
# Methoden des FinTS-Clients gelegt werden
# da für jede Aktion eine TAN erforderlich sein könnte.
def wrap_tan(client: FinTS3PinTanClient, execute_fn: Callable[[FinTS3PinTanClient], None]):
    response = execute_fn(client)

    if not isinstance(response, NeedTANResponse):
        return response

    tan = input('Enter TAN: ')

    return client.send_tan(response, tan)


class FinTSClient():
    def __init__(self, db, blz, login_name, banking_pin, hbci_url):
        self.db_transactions = db.get_table("transactions", primary_id="id", primary_type=db.types.integer)
        self.db_balances = db.get_table("balances", primary_id="id", primary_type=db.types.integer)
        self.client = create_client(blz, login_name, banking_pin, hbci_url)

    def __enter__(self):
        self.client.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.__exit__(exc_type, exc_val, exc_tb)

    def _get_transactions_xml(self, account):
        transactions_xml = wrap_tan(self.client,
                                    lambda client: client.get_transactions_xml(account,
                                                                               date.today() - timedelta(days=30),
                                                                               date.today()))
        # Es kann auch kein XML zurückkommen.
        if len(transactions_xml[0]) == 0:
            return None

        parsed_xml = parseCaml52(
            transactions_xml[0][0].decode("ISO-8859-1").replace('encoding="ISO-8859-1"', 'encoding="utf-8"'))

        return parsed_xml

    def insert_new_transactions_into_database(self):
        client = self.client

        accounts = wrap_tan(client, lambda client: client.get_sepa_accounts())

        for account in accounts:
            parsed_xml = self._get_transactions_xml(account)

            if parsed_xml is None:
                continue

            # Wir zeichen jede Abfrage auf.
            self.db_balances.insert(dict_without(parsed_xml, "entries"))

            new_transactions = []
            for entry in parsed_xml["entries"]:
                existing_row = self.db_transactions.find_one(unique_id=entry["unique_id"])
                if existing_row is None:
                    # Die Transaktion gibt es noch nicht in der Datenbank.
                    self.db_transactions.insert({"iban": account.iban, **entry, "sent_to_user": False})


    # Alle Transaktionen, die dem Benutzer noch nicht
    # gezeigt wurden.
    def get_all_new_transactions(self):
        return list(self.db_transactions.find(sent_to_user={"=", False}))

    def set_transaction_sent(self, transaction_unique_id):
        return self.db_transactions.update({"unique_id": transaction_unique_id, "sent_to_user": True}, ["unique_id"])

    def get_transactions_in_range(self, range_begin: date, range_end: date, account):
        return self.db_transactions.find(iban={"=": account.iban}, valuta_date={"between": [range_begin, range_end]})

    def get_transactions_from_begin(self, range_begin: date, account):
        return self.get_transactions_in_range(range_begin, date.today(), account)

    def get_accounts(self):
        client = self.client

        accounts = wrap_tan(client, lambda client: client.get_sepa_accounts())

        return accounts

    def get_old_account_balance(self, account):
        client = self.client

        transactions = self._get_transactions_xml(account)

        if transactions is None:
            return None

        return transactions["balance_closing"]

#
# db = dataset.connect('sqlite:///main.db')
#
# fints = FinTSClient(db)
# with fints:
#     fints.insert_new_transactions_into_database()
#
