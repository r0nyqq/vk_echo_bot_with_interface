import re
from viasales_api import AviasalesApi

from_to_re = re.compile(r'^\b[а-яА-Я\-\s]{3,40}\b$')
date_re = re.compile(r"^[\d]{4}-[\d]{2}-[\d]{2}$")


def handle_from_to(text, context):
    match = re.match(from_to_re, text)
    if match:
        context['from_to'] = text
        return True
    else:
        return False


def handle_date(text, context):
    match = re.match(date_re, text)
    if match:
        context['date'] = text
        return True
    else:
        return False


def handle_ways(text, context):
    aviasales = AviasalesApi(from_to=context['from_to'], date=context['date'])
    context['ways'] = aviasales.best_ways
    return True
