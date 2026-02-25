# -*- coding: utf-8 -*-
from django.db import models
from taggit.managers import TaggableManager
from taggit.models import Tag, TaggedItem
try:
    from typus import en_typus, ru_typus
except ImportError:
    def en_typus(text): return text
    def ru_typus(text): return text
from pathlib import Path
import pytils


# класс для транслитерации русскоязычных slug
# рецепт взят отсюда: https://timonweb.com/django/russian-slugs-for-django-taggit/
class RuTag(Tag):
    class Meta:
        proxy = True
        # ordering = ['id']

    def slugify(self, tag, i=None):
        return pytils.translit.slugify(self.name.lower())[:128]


class RuTaggedItem(TaggedItem):
    class Meta:
        proxy = True
        # ordering = ['id']

    @classmethod
    def tag_model(cls):
        return RuTag


class TbImages(models.Model):
    # ============================================================
    # ТАБЛИЦА TbImages -- Изображения
    # ------------------------------------------------------------
    # | id              -- id | INT(11) | PRIMARY KEY
    # | imFile          -- Картинка | varchar(128) NOT NULL
    # | szCaption       -- Заголовок, подпись под картинкой | varchar(136) NULL
    # | bIsChecked      -- Проверен | tinyint(1) NOT NULL
    # | iViewCounter    -- Просмотры | int(10) UNSIGNED NOT NULL
    # | dtCreated       -- Дата создания | datetime(6) NOT NULL
    # | dtEdited        -- Дата проверки | datetime(6) NOT NULL
    # ============================================================
    imFile = models.ImageField(
        max_length=136,
        upload_to="img2",
        default=u"",
        unique=True,
        db_index=True,
        verbose_name=u"Картинка",
        help_text=u"Файл с картинкой (gif, jpeg, png, bmp)."
    )
    szCaption = models.CharField(
        max_length=128,
        default=u"",
        unique=True,
        db_index=True,
        blank=False,
        verbose_name=u"Название",
        help_text=u"Название, подпись, описание что изображено…"
    )
    tags = TaggableManager(
        blank=True,
        through=RuTaggedItem,
        verbose_name=u"Теги",
        help_text=u"Теги через запятую… Регистр не чувствителен… <b>Теги нужны для подстановки картинок и навигации<b>"
    )
    bIsChecked = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=u"Проверен",
        help_text=u"Картинку проверили."
    )
    iViewCounter = models.PositiveIntegerField(
        default=0,
        verbose_name=u"◉",
        help_text=u"Число просмотров картинки."
    )
    dtCreated = models.DateTimeField(
        db_index=True,
        auto_now_add=True,  # надо указать False при миграции, после вернуть в True
        auto_now=False,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после убрать (она не нужна)
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата создания"
    )
    dtEdited = models.DateTimeField(
        db_index=True,
        auto_now=True,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после она не нужна
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата редактирования"
    )

    def __str__(self):
        filename = self.imFile.name
        if len(filename) > 15:
            filename = filename[:15] + u"…"
        caption = self.szCaption
        if len(caption) > 25:
            caption = caption[:25] + u"…"
        caption = "%d×%d - %s" % (self.imFile.width, self.imFile.height, caption)
        return u"%05d: %s (%s)" % (self.id, filename, caption)

    def __unicode__(self):
        return self.__str__()

    # заменим имя файла картинки
    def save(self, *args, **kwargs):
        import os
        from django.conf import settings

        old_obj = None
        old_file_path = None

        # Получаем старую запись, если она есть
        if self.pk:
            try:
                old_obj = TbImages.objects.get(pk=self.pk)
                # Пытаемся получить путь к файлу. Если файл не найден физически, Django может выкинуть ошибку здесь или позже
                # Поэтому просто берем имя из БД и формируем путь руками, чтобы не зависеть от Storage
                if old_obj.imFile:
                     old_file_path = os.path.join(settings.MEDIA_ROOT, str(old_obj.imFile.name))
            except TbImages.DoesNotExist:
                pass

        # Fix 1: Если старый путь уже битый (содержит ['...'])
        if old_file_path and "['" in old_file_path:
             # Формируем "исправленный" путь (каким он должен быть)
             corrected_path = old_file_path.replace("['", "").replace("']", "").replace("'", "")

             # Проверяем: если битого файла нет, а исправленный есть -> значит БД врет
             if not os.path.exists(old_file_path) and os.path.exists(corrected_path):
                 # Исправляем текущее имя файла в объекте (убираем мусор из имени)
                 self.imFile.name = str(self.imFile.name).replace("['", "").replace("']", "").replace("'", "")
                 # Обновляем переменную old_file_path, чтобы дальнейшая логика переименования работала корректно
                 old_file_path = corrected_path

        # Получаем текущее имя и расширение (уже возможно исправленное выше)
        current_path = Path(str(self.imFile.name))
        current_suffix = current_path.suffix

        # Fix 2: Чиним расширение еще раз (на всякий случай, если Fix 1 не сработал или это новый объект)
        if "['" in str(current_suffix):
             current_suffix = str(current_suffix).replace("['", "").replace("']", "").replace("'", "")

        # Формируем новое имя файла на основе заголовка (Slug)
        new_filename = pytils.translit.slugify(self.szCaption.lower()) + current_suffix

        # Определяем папку (если есть родитель, используем его, иначе img2)
        # Важно: self.imFile.name может содержать полный путь. Нам нужен только относительный от MEDIA_ROOT
        # Но проще взять родителя из текущего имени
        parent_dir = current_path.parent.name if current_path.parent.name else 'img2'
        new_name_with_path = str(Path(parent_dir) / new_filename)

        # Переименование физического файла
        # Сравниваем старое имя (из БД) с новым (сгенерированным)
        if old_obj and str(old_obj.imFile.name) != new_name_with_path:
             new_file_full_path = os.path.join(settings.MEDIA_ROOT, new_name_with_path)

             # Если старый файл (old_file_path) существует физически, переименовываем его
             if old_file_path and os.path.exists(old_file_path):
                 try:
                    os.makedirs(os.path.dirname(new_file_full_path), exist_ok=True)
                    os.rename(old_file_path, new_file_full_path)
                    self.imFile.name = new_name_with_path
                 except OSError as e:
                     print(f"Error renaming file from {old_file_path} to {new_file_full_path}: {e}")
             else:
                 # Если старого файла нет, просто обновляем имя в БД
                 self.imFile.name = new_name_with_path
        else:
             # Если имя не менялось или объекта не было, просто устанавливаем правильное имя
             # (например, чтобы убрать мусор из расширения в БД)
             self.imFile.name = new_name_with_path

        super(TbImages, self).save(*args, **kwargs)

    class Meta:
        verbose_name = u"КАРТИНКА"
        verbose_name_plural = u"КАРТИНКИ"
        ordering = ['id', ]


class TbOrigin(models.Model):
    # ============================================================
    # ТАБЛИЦА TbOrigin -- Источник, место откуда взята циатата, высказывание, изречение
    # ------------------------------------------------------------
    # | id              -- id | INT(11) | PRIMARY KEY
    # | szOrigin        -- Источник | varchar(256) NULL
    # | dtCreated       -- Дата создания | datetime(6) NOT NULL
    # | dtEdited        -- Дата проверки | datetime(6) NOT NULL
    # ============================================================
    szOrigin = models.CharField(
        max_length=256,
        default=u"",
        unique=True,
        db_index=True,
        verbose_name=u"Источник",
        help_text=u"Ссылка или указание источника: книга, URL, просто что-то…"
    )
    dtCreated = models.DateTimeField(
        db_index=True,
        auto_now_add=True,  # надо указать False при миграции, после вернуть в True
        auto_now=False,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после убрать (она не нужна)
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата создания"
    )
    dtEdited = models.DateTimeField(
        db_index=True,
        auto_now=True,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после она не нужна
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата редактирования"
    )

    def __str__(self):
        origin = self.szOrigin
        if len(origin) > 35:
            origin = origin[:35] + u"…"
        return u"%03d: %s" % (self.id, origin)

    def __unicode__(self):
        return self.__str__()

    class Meta:
        verbose_name = u"ИСТОЧНИК"
        verbose_name_plural = u"ИСТОЧНИКИ"
        ordering = ['id', ]


class TbAuthor(models.Model):
    # ============================================================
    # ТАБЛИЦА TbAuthor -- Автор изречения или цитаты (dictum and quotes)
    # ------------------------------------------------------------
    # | id              -- id | INT(11) | PRIMARY KEY
    # | szAuthor        -- Автор и, если необходимо, краткая справка | varchar(256) NOT NULL
    # | szAuthorHTML    -- Автор и... в HTML по правилам типографики | varchar(136) NULL
    # | bIsChecked      -- Проверен | tinyint(1) NOT NULL
    # | iViewCounter    -- Просмотры | int(10) UNSIGNED NOT NULL
    # | dtCreated       -- Дата создания | datetime(6) NOT NULL
    # | dtEdited        -- Дата проверки | datetime(6) NOT NULL
    # ============================================================
    szAuthor = models.CharField(
        max_length=128,
        default=u"",
        unique=True,
        db_index=True,
        verbose_name=u"Автор",
        help_text=u"Автор и, если необходимо, краткая справка"
    )
    szAuthorHTML = models.TextField(
        default="",
        blank=True,
        verbose_name=u"Автор HTML",
        help_text=u"Автор и, если необходимо, краткая справка<br />"
                  u"Свертано в HTML по правилам типографики <small>(рекламные URL вставляются тут)</small>"
    )
    bTypograph = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=u"Типографить",
        help_text=u"Применять типографику к этому автору?"
    )
    bIsChecked = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=u"Проверен",
        help_text=u"Автор проверен."
    )
    tags = TaggableManager(
        blank=True,
        through=RuTaggedItem,
        verbose_name=u"Теги",
        help_text=u"Теги через запятую… Регистр не чувствителен… <b>Теги нужны для подстановки картинок и навигации<b>"
    )
    iViewCounter = models.PositiveIntegerField(
        default=0,
        verbose_name=u"◉",
        help_text=u"Число просмотров Автора."
    )
    dtCreated = models.DateTimeField(
        db_index=True,
        auto_now_add=True,  # надо указать False при миграции, после вернуть в True
        auto_now=False,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после убрать (она не нужна)
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата создания"
    )
    dtEdited = models.DateTimeField(
        db_index=True,
        auto_now=True,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после она не нужна
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата редактирования"
    )

    def __str__(self):
        author = self.szAuthor
        if len(author) > 25:
            author = author[:25] + u"…"
        return u"%04d: %s" % (self.id, author)

    def __unicode__(self):
        return self.__str__()

    def save(self, *args, **kwargs):
        # Типографирование перенесено в админку (через библиотеку etpgrf)
        # Здесь оставляем только базовое сохранение
        if not self.szAuthorHTML and self.szAuthor:
            # Если HTML пуст, временно заполняем его оригиналом (или можно вызвать etpgrf с дефолтами)
            self.szAuthorHTML = self.szAuthor
        super(TbAuthor, self).save(*args, **kwargs)

    class Meta:
        verbose_name = u"АВТОР"
        verbose_name_plural = u"АВТОРЫ"
        ordering = ['id', ]


class TbDictumAndQuotes(models.Model):
    # ============================================================
    # ТАБЛИЦА TbDictQuot -- Изречения и Цитаты (dictum and quotes)
    # ------------------------------------------------------------
    # | id              -- id | INT(11) | PRIMARY KEY
    # | szIntro         -- Вступление | varchar(256) NULL
    # | szIntroHTML     -- Вступление | (форматированное в HTML) varchar(136) NULL
    # | szContent       -- Высказывание | varchar(136)  NOT NULL
    # | szContentHtml   -- Высказывание (Сформатированнон в HTML) | varchar(136) NULL
    # | bIsChecked      -- Проверен | tinyint(1) NOT NULL
    # | kImages         -- Ссылка на картинку в таблице TbImages |
    # | iViewCounter    -- Просмотры | int(10) UNSIGNED NOT NULL
    # | dtCreated       -- Дата создания | datetime(6) NOT NULL
    # | dtEdited        -- Дата проверки | datetime(6) NOT NULL
    # ============================================================
    szIntro = models.CharField(
        max_length=256,
        default=None,
        blank=True,
        verbose_name=u"Вступление",
        help_text=u"Не обязательно. Вступление перед цитатой."
    )
    szIntroHTML = models.TextField(
        default="",
        blank=True,
        verbose_name=u"Вступление HTML",
        help_text=u"Автор и, если необходимо, краткая справка<br />"
                  u" Вступление перед цитатой, в HTML по правилам типографики</small>"
    )
    szContent = models.TextField(
        max_length=640,
        default="",
        verbose_name=u"Изречение",
        help_text=u"Не обязательно."
    )
    szContentHTML = models.TextField(
        default="",
        blank=True,
        verbose_name=u"Изречение HTML",
        help_text=u"Содержание цитаты, афоризма, высказывания…<br />"
                  u" Свёрстано в HTML по правилам типографики"
    )
    bTypograph = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=u"Типографировать",
        help_text=u"Применять типографику?"
    )
    bIsChecked = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=u"Проверен",
        help_text=u"Цитата проверена."
    )
    kAuthor = models.ForeignKey(
        TbAuthor,
        default=None,
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=u"Автор",
        help_text=u"Автор изречения или цитаты <b>(не обязательно, но желательно)</b>"
    )
    kOrigin = models.ForeignKey(
        TbOrigin,
        default=None,
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=u"Источник",
        help_text=u"Откуда взята циатата, высказывание, изречение <b>(не обязательно, но желательно)</b>"
    )
    kImages = models.ForeignKey(
        TbImages,
        default=None,
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=u"Картинка",
        help_text=u"Ссылка на картинку, в табличке картинок <b>(не обязательно)</b><br />"
                  u"<small>если нужна именно данная картинка, а не выбранная автоматически</small>"
    )
    imFileOG = models.ImageField(
        max_length=136,
        upload_to="img2og",
        default=u"",
        blank=True,
        verbose_name=u"OG-image",
        help_text=u"Картинка для социальной сети <b>(будет создана автоматически)</b>.<br />"
                  u"<small>Файл с картинкой (png).<small>"
    )
    iViewCounter = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name=u"◉",
        help_text=u"Число просмотров высказывания."
    )
    tags = TaggableManager(
        blank=True,
        through=RuTaggedItem,
        verbose_name=u"Теги",
        help_text=u"Теги через запятую… Регистр не чувствителен… <b>Теги нужны для подстановки картинок и навигации<b>"
    )
    dtCreated = models.DateTimeField(
        db_index=True,
        auto_now_add=True,  # надо указать False при миграции, после вернуть в True
        auto_now=False,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после убрать (она не нужна)
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата создания"
    )
    dtEdited = models.DateTimeField(
        db_index=True,
        auto_now=True,  # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после она не нужна
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name=u"Дата редактирования"
    )

    def __str__(self):
        intro = self.szIntro
        if len(intro) > 35:
            intro = intro[:35] + u"…"
        content = self.szContent
        if len(content) > 55:
            content = content[:55] + u"…"
        return u"%05d: %s :: %s" % (self.id, intro, content)

    def __unicode__(self):
        return self.__str__()

    def save(self, *args, **kwargs):
        # Типографирование (szContent -> szContentHTML, szIntro -> szIntroHTML)
        # перенесено в админку для управления параметрами (язык, переносы и т.д.)
        if not self.szContentHTML and self.szContent:
            self.szContentHTML = self.szContent
        if not self.szIntroHTML and self.szIntro:
            self.szIntroHTML = self.szIntro
        super(TbDictumAndQuotes, self).save(*args, **kwargs)

    class Meta:
        verbose_name = u"ВЫСКАЗЫВАНИЕ"
        verbose_name_plural = u"ВЫСКАЗЫВАНИЯ"
        ordering = ['-id', ]
