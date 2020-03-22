import calendar
from datetime import date, timedelta, datetime


def dt(y, m, d):
    return datetime(y, m, d).date()

def remaining_days_of_month(relevant_date: date):
    return calendar.monthrange(relevant_date.year, relevant_date.month)[1] - relevant_date.day + 1

def get_current_month_range():
    today = date.today()
    start_of_month = today.replace(day=1)

    return (start_of_month, today)


def get_last_month_range():
    end_of_last_month = date.today().replace(day=1) - timedelta(days=1)
    start_of_last_month = end_of_last_month.replace(day=1)

    return (start_of_last_month, end_of_last_month)

