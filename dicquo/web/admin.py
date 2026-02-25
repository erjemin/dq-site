# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from web.models import TbDictumAndQuotes, TbAuthor, TbImages, TbOrigin
from taggit.managers import TaggableManager
from django_select2.forms import Select2TagWidget
from taggit.models import Tag
from taggit.utils import parse_tags
from django.db import models
from django.db.utils import OperationalError, ProgrammingError

try:
    from etpgrf.typograph import Typographer
    from etpgrf.layout import LayoutProcessor
    from etpgrf.hyphenation import Hyphenator
except ImportError:
    # Заглушка, если библиотека не установлена
    class Typographer:
        def __init__(self, **kwargs): pass
        def process(self, text): return text
    class LayoutProcessor:
        def __init__(self, **kwargs): pass
    class Hyphenator:
         def __init__(self, **kwargs): pass


class TagSelect2Widget(Select2TagWidget):
    """
    Select2-виджет для django-taggit, работающий по ИМЕНАМ тегов.

    - подхватывает уже сохранённые теги;
    - показывает выпадающий список из существующих тегов;
    - даёт создавать новые теги с пробелами в названии.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # choices: список всех существующих тегов по имени.
        # Важно: на этапах вроде collectstatic таблицы taggit ещё может не быть,
        # поэтому оборачиваем в try/except и молча игнорируем отсутствие БД.
        try:
            self.choices = [(t.name, t.name) for t in Tag.objects.all()]
        except (OperationalError, ProgrammingError):
            self.choices = []

    class Media:
        css = {
            "all": ("css/select2_taggit_admin.css",),
        }

    def build_attrs(self, base_attrs, extra_attrs=None):
        """
        Настраиваем Select2 так, чтобы пробел НЕ разделял тег
        на несколько частей (нужны теги с пробелами: «Сергей Курёхин»).
        Оставляем в разделителях только запятую.
        """
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # По умолчанию django-select2 ставит: [",", " "]
        # Нам нужен только разделитель-запятая.
        # Строка '[","]' — корректный JSON-массив из одного элемента.
        # Важно: сюда нужно класть СТРОКУ с JSON-массивом, а не python-список.
        # Иначе в HTML окажется "['[\", \"]', ...]" и Select2 будет вести себя непредсказуемо.
        attrs["data-token-separators"] = '[","]'
        return attrs

    def format_value(self, value):
        """
        Преобразуем значение из TaggableManager/TagField
        в список ИМЁН тегов, который ожидает Select2TagWidget.
        """
        from django.db.models import QuerySet

        if value is None:
            return []

        # QuerySet или список Tag-объектов
        if isinstance(value, QuerySet):
            return [t.name for t in value]
        if isinstance(value, (list, tuple, set)):
            names = []
            for v in value:
                if isinstance(v, Tag):
                    names.append(v.name)
                else:
                    names.append(str(v))
            return names

        # Строка вида "tag1, tag2" — разбираем в список имён
        if isinstance(value, str):
            return parse_tags(value)

        return super().format_value(value)

    def value_from_datadict(self, data, files, name):
        """
        Django-Select2 возвращает список значений (['Сергей Курёхин', 'Другой тег']).
        Taggit (TagField) ждёт ОДНУ строку, которую потом парсит в список тегов.
        Если отдать список, он превратится в строку `"['Сергей', 'Курёхин']"`,
        и распарсится в кривые теги — этого мы избегаем.
        """
        values = super().value_from_datadict(data, files, name)
        if not values:
            return ""

        # Для нашего виджета value — это уже список имён тегов
        tag_names = [str(v).strip() for v in values if str(v).strip()]
        if not tag_names:
            return ""

        # ОДИН многословный тег: "Сергей Курёхин" -> "Сергей Курёхин,"
        # Тогда parse_tags переключится в режим "деление по запятым"
        if len(tag_names) == 1:
            single = tag_names[0]
            if " " in single and "," not in single and '"' not in single:
                return single + ","
            return single

        # Несколько тегов — явная запятая между ними.
        return ", ".join(tag_names)


class DictumAdminForm(forms.ModelForm):
    # Виртуальные поля для настройки типографа
    etp_language = forms.ChoiceField(
        label="Язык типографики",
        choices=[('ru', 'Русский'), ('en', 'English'), ('ru,en', 'Ru + En')],
        initial='ru',
        required=False
    )
    etp_quotes = forms.BooleanField(
        label="Обработка кавычек",
        initial=True,
        required=False,
        help_text="Заменять прямые кавычки на «ёлочки» или “лапки”"
    )
    etp_hanging_punctuation = forms.ChoiceField(
        label="Висячая пунктуация",
        choices=[('no', 'Нет'), ('left', 'Слева'), ('right', 'Справа'), ('both', 'Обе стороны')],
        initial='left',
        required=False,
        help_text="Выносить кавычки за границу текстового блока"
    )
    etp_hyphenation = forms.BooleanField(
        label="Переносы",
        initial=True,
        required=False,
        help_text="Расставлять мягкие переносы (&amp;shy;)"
    )
    etp_sanitize = forms.BooleanField(
        label="Санитайзер (HTML)",
        initial=False,
        required=False,
        help_text="Очищать HTML теги перед обработкой"
    )
    etp_mode = forms.ChoiceField(
        label="Режим вывода",
        choices=[('mixed', 'Смешанный (Mixed)'), ('unicode', 'Юникод (Unicode)'), ('mnemonic', 'Мнемоники')],
        initial='mixed',
        required=False,
        help_text="Формат спецсимволов"
    )

    class Meta:
        model = TbDictumAndQuotes
        fields = '__all__'
        widgets = {
            'tags': TagSelect2Widget,
        }


# Register your models here.
class AdmDictumAndQuotesAdmin(admin.ModelAdmin):
    form = DictumAdminForm
    search_fields = ['id', 'szIntro', 'szContent', ]
    list_display = ('id', 'szIntro', 'szContent', 'tag_list', 'iViewCounter', 'dtEdited', )
    list_display_links = ('id', 'szIntro', 'szContent', )
    # list_filter = ('iViewCounter', )
    empty_value_display = u"<b style='color:red;'>-empty-</b>"
    actions_on_top = False
    actions_on_bottom = True
    actions_selection_counter = True

    fieldsets = (
        (None, {
            'fields': ('szIntro', 'szContent', 'kAuthor', 'kOrigin', 'kImages', 'tags', 'bIsChecked')
        }),
        ('Настройки типографа (Etpgrf)', {
            'classes': ('collapse',),
            'fields': (
                ('etp_language', 'etp_mode'),
                ('etp_quotes', 'etp_sanitize'),
                ('etp_hyphenation', 'etp_hanging_punctuation'),
            ),
            'description': 'Настройки применяются при сохранении. Результат записывается в скрытые HTML-поля.'
        }),
        ('HTML Результат (ReadOnly)', {
            'classes': ('collapse',),
            'fields': ('szIntroHTML', 'szContentHTML'),
        }),
        ('Служебное', {
             'classes': ('collapse',),
             'fields': ('iViewCounter', 'imFileOG', 'bTypograph') # bTypograph kept for compatibility
        })
    )
    readonly_fields = ('szIntroHTML', 'szContentHTML', 'iViewCounter')

    formfield_overrides = {
        models.ManyToManyField: {'widget': Select2TagWidget},
    }

    def save_model(self, request, obj, form, change):
        # 1. Читаем базовые настройки
        langs = form.cleaned_data.get('etp_language', 'ru').split(',')

        # 2. Собираем LayoutProcessor
        layout_option = False
        # Включаем layout по умолчанию с базовыми настройками (инициалы, юниты)
        layout_option = LayoutProcessor(
            langs=langs,
            process_initials_and_acronyms=True,
            process_units=True
        )

        # 3. Собираем Hyphenator
        hyphenation_enabled = form.cleaned_data.get('etp_hyphenation', True)
        hyphenation_option = False
        if hyphenation_enabled:
            hyphenation_option = Hyphenator(
                langs=langs,
                max_unhyphenated_len=12
            )

        # 4. Читаем Sanitizer
        sanitizer_enabled = form.cleaned_data.get('etp_sanitize', False)
        sanitizer_option = None
        if sanitizer_enabled:
            sanitizer_option = 'etp'

        # 5. Читаем Hanging Punctuation
        hanging_val = form.cleaned_data.get('etp_hanging_punctuation', 'no')
        hanging_option = None
        if hanging_val != 'no':
            hanging_option = hanging_val

        # 6. Собираем общие опции
        options = {
            'langs': langs,
            'process_html': True,
            'quotes': form.cleaned_data.get('etp_quotes', True),
            'layout': layout_option,
            'unbreakables': True,
            'hyphenation': hyphenation_option,
            'symbols': True,
            'hanging_punctuation': hanging_option,
            'mode': form.cleaned_data.get('etp_mode', 'mixed'),
            'sanitizer': sanitizer_option,
        }

        # Инициализируем типограф с настройками из формы
        try:
            # DEBUG: Проверка, какой класс используется
            if Typographer.__module__ == __name__: # Если класс определен в этом же файле (заглушка)
                 self.message_user(request, "ВНИМАНИЕ: Используется заглушка Typographer! Библиотека etpgrf не найдена.", level='WARNING')

            t = Typographer(**options)

            # Обрабатываем контент
            if obj.szContent:
                # В онлайн-типографе используется .process(text)
                old_html = obj.szContentHTML or ""
                processed = t.process(obj.szContent)
                obj.szContentHTML = processed

                # DEBUG: Проверка изменений
                if processed != old_html and processed != obj.szContent:
                     self.message_user(request, f"Типограф: szContentHTML обновлен (len changed: {len(old_html)} -> {len(processed)})", level='INFO')

            # Обрабатываем интро
            if obj.szIntro:
                obj.szIntroHTML = t.process(obj.szIntro)

        except Exception as e:
            # Fallback if processing fails
            self.message_user(request, f"Ошибка типографа: {e}", level='ERROR')
            if not obj.szContentHTML: obj.szContentHTML = obj.szContent
            if not obj.szIntroHTML: obj.szIntroHTML = obj.szIntro

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


class AdmOrigin(admin.ModelAdmin):
    search_fields = ['id', 'szOrigin', ]
    list_display = ('id', 'szOrigin',)
    list_display_links = ('id', 'szOrigin',)
    empty_value_display = u"<b style='color:red;'>-empty-</b>"


class AdmImages(admin.ModelAdmin):
    search_fields = ['id', 'imFile', 'szCaption', ]
    list_display = ('id', 'szCaption', 'tag_list', 'iViewCounter', 'imFile', 'dtEdited',)
    list_display_links = ('id', 'szCaption')
    empty_value_display = u"<b style='color:red;'>-empty-</b>"

    # Добавляем виджет для тегов
    formfield_overrides = {
        TaggableManager: {'widget': TagSelect2Widget},
    }

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


class AdmAuthor(admin.ModelAdmin):
    search_fields = ['id', 'szAuthor', 'szCaption', ]
    list_display = ('id', 'szAuthor', 'tag_list', 'iViewCounter', 'dtEdited',)
    list_display_links = ('id', 'szAuthor')
    empty_value_display = u"<b style='color:red;'>-empty-</b>"

    # Добавляем виджет для тегов
    formfield_overrides = {
        TaggableManager: {'widget': TagSelect2Widget},
    }

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


admin.site.register(TbDictumAndQuotes, AdmDictumAndQuotesAdmin)
admin.site.register(TbOrigin, AdmOrigin)
admin.site.register(TbImages, AdmImages)
admin.site.register(TbAuthor, AdmAuthor)
