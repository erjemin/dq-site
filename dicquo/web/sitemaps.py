from django.contrib.sitemaps import Sitemap
from web.models import TbDictumAndQuotes
import pytils

class DictumSitemap(Sitemap):
    changefreq = "weekly"       # Как часто меняются страницы
    priority = 0.9              # Приоритет (от 0.0 до 1.0)

    def items(self):
        # Only show checked items in sitemap
        return TbDictumAndQuotes.objects.filter(bIsChecked=True).order_by('-id')

    def lastmod(self, obj):
        return obj.dtEdited

    def location(self, obj):
        # Generates URL in format: /123_slug
        slug = pytils.translit.slugify(obj.szContent.lower())[:120]
        return f"/{obj.id}_{slug}"

