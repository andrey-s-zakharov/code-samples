'''
This code helps to convert currencies using currencies rates from API of http://fixer.io/
There is a periodic task which updates currency rates every day and
uses data from cache and db for time and request count decrease.
Function currency_price_dict can be used for API if we want return price in several currencies.
Function convert_currency can be used almost everywhere if we know base currency and converted price.
'''

import logging
import requests

from decimal import Decimal
from math import ceil

from django.core.cache import cache
from django.conf import settings

from celery.decorators import periodic_task

from .models import Currency # Example Currency model

logger = logging.getLogger(__name__)


def get_currency_rates():
    """ Get currency rates from cache, DB or fetch new ones """
    rates = get_currency_from_cache()
    if rates:
        return rates
    rates = get_currency_from_db()
    if rates:
        return rates
    logger.error('Get rates with fetch')
    return fetch_currency_data()


def get_currency_from_cache():
    return cache.get(settings.CURRENCY_DATA_CACHE)


def set_currency_to_cache(rates):
    cache.set(settings.CURRENCY_DATA_CACHE, rates, None)


def get_currency_from_db():
    rates = Currency.currency_rates()
    set_currency_to_cache(rates)
    return rates


def fetch_currency_data():
    """ Fetch currency rates from external API """
    response = requests.get('{}{}'.format(settings.CURRENCY_FETCH_URL, settings.CURRENCY_ACCESS_KEY))
    response_rates = response.json().get("rates")
    response_rates['EUR'] = 1.0
    return response_rates


def update_currencies():
    """ Update currencies and set it to cache and DB """
    rates = fetch_currency_data()
    set_currency_to_cache(rates)
    for name, rate in rates.items():
        Currency.objects.update_or_create(name=name, defaults={'rate': rate})
    return rates


@periodic_task(run_every=(crontab(hour="18", minute="30", day_of_week="*")))
def update_day_currency():
    """ Periodic celery task for updating currency rates """
    now = datetime.now()
    logger.info("Start currency task at {}, {}:{}".format(now.day, now.hour, now.minute))
    update_currencies()
    now = datetime.now()
    logger.info("Finish currency task at {}, {}:{}".format(now.day, now.hour, now.minute))


def convert_currency(amount, currency_from, currency_to, currency_rates=None):
    """ Convert price to another currency """
    if not currency_rates:
        currency_rates = get_currency_rates()
    if amount == None:
        amount = 0
    return ceil(
        Decimal(amount) * (Decimal(currency_rates.get(currency_to)) / Decimal(currency_rates.get(currency_from)))
    )


def currency_price_dict(currency, unit_price, currency_rates=None):
    """ Return converted prices in dictionary for API """
    if not currency_rates:
        currency_rates = get_currency_rates()
    price_dict = {}
    if not unit_price:
        unit_price = 0
    if currency_rates.get(Currency.EUR):
        price_dict[Currency.EUR] = convert_currency(
            unit_price, currency, Currency.EUR, currency_rates=currency_rates)
    if currency_rates.get(Currency.USD):
        price_dict[Currency.USD] = convert_currency(
            unit_price, currency, Currency.USD, currency_rates=currency_rates)
    if currency_rates.get(Currency.GBP):
        price_dict[Currency.GBP] = convert_currency(
            unit_price, currency, Currency.GBP, currency_rates=currency_rates)
    if currency_rates.get(Currency.RUB):
        price_dict[Currency.RUB] = convert_currency(
            unit_price, currency, Currency.RUB, currency_rates=currency_rates)

    return price_dict
