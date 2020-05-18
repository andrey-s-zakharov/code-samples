"""
Sitemaps: rel="alternate" hreflang="x" implementation.
XML sitemap developed via django-qartez according to Google specs
about localized versions of site pages
"""

from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from six.moves.urllib import parse as urlparse

from qartez.sitemaps import RelAlternateHreflangSitemap
from qartez.constants import REL_ALTERNATE_HREFLANG_SITEMAP_TEMPLATE

from core.models import Country
from schools.models import School


# Locate of helper functions in separate module
def languages():
    """ Get language codes and names of all languages as a dictionary """
    return {lang_code: lang_name for lang_code, lang_name in settings.LANGUAGES}


def language_codes():
    """ Get language with codes of all languages """
    return languages().keys()


class LanguageRelAlternateHreflangSitemap(RelAlternateHreflangSitemap):

    def __get(self, name, obj, default=None):
        try:
            attr = getattr(self, name)
        except AttributeError:
            return default
        if callable(attr):
            return attr(obj)
        return attr

    def _full_url(self, protocol, domain, path):
        return "{}://{}{}".format(protocol, domain, path)

    def _render_alternate_hreflangs(self, protocol, domain, item):
        """
        Render the tiny bit of XML responsible for rendering the alternate
        hreflang code.
        """
        alternate_hreflangs = self.__get('alternate_hreflangs', item, [])
        output = ""
        if alternate_hreflangs:
            for lang, path in alternate_hreflangs:
                if urlparse.urlparse(path).netloc:
                    url = path
                else:
                    url = self._full_url(protocol, domain, path)
                output += REL_ALTERNATE_HREFLANG_SITEMAP_TEMPLATE.format(**{'lang': lang, 'href': url})
        return output

    def _get_domain(self):
        if Site._meta.installed:
            try:
                site = Site.objects.get_current()
            except Site.DoesNotExist:
                pass
        if site is None:
            raise ImproperlyConfigured(
                "To use sitemaps, either enable the sites framework "
                "or palocationss a Site/RequestSite object in your view."
            )
        return site.domain

    def get_urls(self, page=1, site=None, protocol=None):
        domain = self._get_domain()
        urls = []
        for lang_code in language_codes():
            lang_domain = '{}/{}'.format(domain, lang_code)
            for item in self.paginator.page(page).object_list:
                loc = self._full_url(self.protocol, lang_domain, self.location(item))
                url_info = {
                    'location': loc,
                    'lastmod': None,
                    'changefreq': self.changefreq,
                    'priority': None,
                    'alternate_hreflangs': self._render_alternate_hreflangs(self.protocol, domain, item),
                }
                urls.append(url_info)
        return urls


class CommonPageSitemap(LanguageRelAlternateHreflangSitemap):

    changefreq = "never"
    protocol = get_current_protocol()

    def location(self, item):
        return item


class MainPageSitemap(CommonPageSitemap):

    def items(self):
        return ['/']

    def alternate_hreflangs(self, obj):
        return [(lang_code, '/{}/'.format(lang_code)) for lang_code in language_codes()]


class StaticPagesSitemap(CommonPageSitemap):

    def items(self):
        return ['/about/', '/terms/', '/privacy/']

    def alternate_hreflangs(self, obj):
        return [(lang_code, '/{}{}'.format(lang_code, obj)) for lang_code in language_codes()]


class SchoolSitemap(LanguageRelAlternateHreflangSitemap):

    model = School
    changefreq = "daily"
    protocol = get_current_protocol()

    def alternate_hreflangs(self, obj):
        return [(lang_code, obj.get_language_alternative_url(lang_code)) for lang_code in language_codes()]

    def items(self):
        return self.model.objects.published().all().distinct().order_by('id')

    def lastmod(self, obj):
        return obj.updated_at


class CountrySitemap(LanguageRelAlternateHreflangSitemap):

    model = Country
    protocol = get_current_protocol()
    changefreq = "monthly"

    def alternate_hreflangs(self, obj):
        return [(lang_code, obj.get_language_alternative_url(lang_code)) for lang_code in language_codes()]

    def items(self):
        return self.model.objects.with_cities().distinct().order_by('id')

"""
Then we need implement these classes as sitemap sections in main urls.py
"""
