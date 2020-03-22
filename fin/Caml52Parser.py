from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TextIO, Union

import dateutil.parser
from bs4 import BeautifulSoup


def CREDIT():
    return "CRDT"

def DEBIT():
    return "DBIT"


def parseCaml52(input_xml: Union[str, TextIO]):
    bs = BeautifulSoup(input_xml, "xml")

    rpt = bs.BkToCstmrAcctRpt.Rpt
    date_of_request = dateutil.parser.isoparse(rpt.CreDtTm.string)
    account_iban = str(rpt.Acct.Id.IBAN.string)
    account_owner = str(rpt.Ownr.Nm.string)

    def opening_filter(element):
        return element.name == "Bal" and str(element.Tp.CdOrPrtry.Cd.string) == "PRCD"
    def closing_filter(element):
        return element.name == "Bal" and str(element.Tp.CdOrPrtry.Cd.string) == "CLBD"

    balance_opening = int(Decimal(str(rpt.find(opening_filter).Amt.string)) * 100)
    balance_closing = int(Decimal(str(rpt.find(closing_filter).Amt.string)) * 100)

    entries = []
    for entry in rpt.find_all("Ntry"):
        ntry_xml = str(entry)
        amount = int(Decimal(str(entry.Amt.string)) * 100)
        booking_date = dateutil.parser.isoparse(entry.BookgDt.Dt.string).date()
        valuta_date = dateutil.parser.isoparse(entry.ValDt.Dt.string).date()
        unique_id = str(entry.AcctSvcrRef)
        credit = str(entry.CdtDbtInd.string)

        pties = entry.NtryDtls.TxDtls.RltdPties
        creditor = str(pties.Cdtr.Nm.string)
        creditor_iban = str(pties.CdtrAcct.Id.IBAN.string)
        debitor = str(pties.Dbtr.Nm.string)
        debitor_iban = str(pties.DbtrAcct.Id.IBAN.string)

        reasons = []
        for r in entry.NtryDtls.RmtInf.find_all("Ustrd"):
            reasons.append(str(r.string))

        entries.append({
            "ntry_xml": ntry_xml,
            "amount": amount,
            "booking_date": booking_date,
            "valuta_date": valuta_date,
            "unique_id": unique_id,
            "credit": credit,
            "creditor": creditor,
            "creditor_iban": creditor_iban,
            "debitor": debitor,
            "debitor_iban": debitor_iban,
            "reason": reasons[0] if len(reasons) > 0 else "",
            "additional_reason": reasons[1] if len(reasons) > 1 else ""
        })

    return {
        "date_of_request": date_of_request,
        "account_iban": account_iban,
        "account_owner": account_owner,
        "balance_opening": balance_opening,
        "balance_closing": balance_closing,
        "entries": entries
    }


