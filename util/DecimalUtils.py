from decimal import Decimal


def from_cents(num: int):
    return Decimal(num) / 100

def to_cents(num: Decimal):
    return int(num * 100)