This code helps to convert currencies using currencies rates from API of http://fixer.io/
There is a periodic task which updates currency rates every day and uses data from cache and db for time and request count decrease.
Function currency_price_dict can be used for API if we want return price in several currencies.
Function convert_currency can be used almost everywhere if we know base currency and converted price.