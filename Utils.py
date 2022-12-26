import datetime

def is_date_string(text: str) -> bool:
    try:
        datetime.datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return False
    else:
        return True