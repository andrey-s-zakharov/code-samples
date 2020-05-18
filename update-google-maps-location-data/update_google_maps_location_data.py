"""
These functions parse Google Maps data from request
and get or create same location objects in local DB.
They can be used in views or serializers of Django Rest Framework
as helper functions if you use Google Maps on front.
"""

def set_location_data(self, data):
    """ Parse and set location data """
    google_data_keys = ['google_city', 'google_country_code', 'google_country_name']
    if all((google_data_key in data for google_data_key in google_data_keys)):
        google_city = data.pop('google_city')
        google_country_code = data.pop('google_country_code')
        google_country_name = data.pop('google_country_name')

        country = self._get_or_create_country_by_google_country_data(
            google_country_code=google_country_code, google_country_name=google_country_name)
        data['country'] = country.id
        city = self._get_or_create_city_by_google_location_data(
            google_city=google_city, google_country_code=google_country_code, country=country)
        data['location'] = city.id
        if 'google_place_id' in data:
            google_place_id = data.get('google_place_id')
            self._set_place_id_to_city(google_place_id=google_place_id, city=city, country=country)
    return data

def _get_or_create_country_by_google_country_data(self, google_country_name, google_country_code):
    """ Get country by google code and name consistently """
    country = Country.objects.filter(code__iexact=google_country_code).first()
    if not country:
        country = Country.objects.filter(name__iexact=google_country_name).first()
    if not country:
        eur_currency = Currency.objects.filter(name=Currency.EUR).first()
        country = Country.objects.create(code=google_country_code, name=google_country_name)
    return country

def _get_or_create_city_by_google_location_data(self, google_city, google_country_code, country):
    """ Get existed or create new city by name and google country code """
    city = City.objects.filter(name__iexact=google_city, country__code__iexact=google_country_code).first()
    if not city:
        city = City.objects.create(name=google_city, country=country)
    return city

def _set_place_id_to_city(self, google_place_id, city, country):
    if city.place_id != google_place_id:
        city.place_id = google_place_id
        city.save(update_fields=['place_id'])
