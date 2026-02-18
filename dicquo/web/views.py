# -*- coding: utf-8 -*-
__author__ = "Sergei Erjemin"
__copyright__ = "Copyright 2020-2026, Sergei Erjemin"
__credits__ = ["Sergei Erjemin", ]
__license__ = "GPL"
__version__ = "0.3.0"
__maintainer__ = "Sergei Erjemin"
__email__ = "erjemin@gmail.com"
__status__ = "in progress"

from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView, TemplateView
import time
import hashlib
import random
import pytils
from web.models import TbDictumAndQuotes, TbImages, TbAuthor


# Create your views here.

class CommonContextMixin:
    """
    Общий миксин для представлений:
    - Логика "одной цитаты" (получение контекста цитаты)
    - Общий контекст (куки, тайминги)
    """
    def dispatch(self, request, *args, **kwargs):
        # Засекаем время в самом начале обработки запроса
        self.t_start = time.process_time()
        return super().dispatch(request, *args, **kwargs)

    def get_filtered_queryset(self):
        """
        Возвращает (queryset, tag_slug) на основе GET-параметров запроса.
        Если тега нет или он не найден, возвращает (None, None).
        """
        tag_slug = self.request.GET.get('tag')
        if not tag_slug:
            return None, None

        dq_qs = TbDictumAndQuotes.objects.all()

        # 1. Пробуем найти цитаты, где АВТОР имеет этот тег
        author_tag_qs = dq_qs.filter(kAuthor__tags__slug__in=[tag_slug])
        if author_tag_qs.exists():
            return author_tag_qs, tag_slug

        # 2. Если авторов нет, ищем цитаты с этим тегом
        quote_tag_qs = dq_qs.filter(tags__slug__in=[tag_slug])
        if quote_tag_qs.exists():
            return quote_tag_qs, tag_slug

        return None, None

    def get_dictum_context(self, request, dq, queryset=None):
        """
        Получение контекста для цитаты dq. Если queryset передан, используется для логики "следующей цитаты"
        и фильтрации по тегу.
        """
        context = {}

        # Если queryset не передан, используем все объекты
        if queryset is None:
            queryset = TbDictumAndQuotes.objects.all()

        # --- 1. ЛОГИКА ИСТОРИИ СЕССИИ (Предотвращение петель) ---
        seen_ids = request.session.get('seen_ids', [])

        if dq.id not in seen_ids:
            seen_ids.append(dq.id)
            if len(seen_ids) > 100:
                seen_ids.pop(0)
            request.session['seen_ids'] = seen_ids

        # --- 2. ГЕНЕРАЦИЯ ЦВЕТОВ ---
        num = int(hashlib.blake2s(dq.szContent.encode("utf-8"), digest_size=1).hexdigest(), 16)
        clr = sorted([num / 2, num / 3, num / 5, num / 7, num / 11, num / 1.5], key=lambda A: random.random())
        context.update({'CLR': clr})
        context.update({'DQ': dq})

        # --- 3. АВТОР И ТЕГИ ---
        try:
            au = TbAuthor.objects.get(id=dq.kAuthor_id)
            context.update({'AUTHOR': au})
            tags = au.tags.names()
        except ObjectDoesNotExist:
            tags = dq.tags.names()

        tag_and_slug = []
        for i in tags:
            tag_and_slug.append({"name": i, "slug": pytils.translit.slugify(i.lower())[:120]})
        context.update({'TAGS': sorted(tag_and_slug, key=lambda x: x["name"])})

        # --- 4. ВЫБОР КАРТИНКИ ---
        if dq.kImages_id is None:
            if len(tags) != 0:
                tagged_image = TbImages.objects.filter(tags__name__in=tags).order_by('?').first()
                if tagged_image:
                    context.update({'IMAGE': tagged_image.imFile})
        else:
            context.update({'IMAGE': dq.kImages.imFile})

        # --- 5. СЧЕТЧИК ---
        dq.iViewCounter += 1
        dq.save(update_fields=['iViewCounter'])

        # --- 6. ВЫБОР СЛЕДУЮЩЕЙ ЦИТАТЫ ---
        dq_next = queryset.exclude(id__in=seen_ids).order_by('?').first()

        if dq_next is None:
            request.session['seen_ids'] = []
            dq_next = queryset.exclude(id=dq.id).order_by('?').first()

        if dq_next:
            context.update({"NEXT": dq_next.id})
            context.update({"NEXT_TXT": pytils.translit.slugify(dq_next.szContent.lower()[:120])})

            # Если мы в режиме фильтрации (tag), передаем текущий тег в контекст
            if request.GET.get('tag'):
                 context.update({"CURRENT_TAG": request.GET.get('tag')})

        return context

    def finalize_context(self, context):
        """
        Добавляет общие данные: проверки куки и время выполнения.
        """
        if self.request.COOKIES.get('cookie_accept'):
            context['cookie_accept'] = 1

        # Считаем время от self.t_start, заданного в dispatch
        total_time = 0.0
        if hasattr(self, 't_start'):
            total_time = float(time.process_time() - self.t_start)
        context['ticks'] = total_time
        return context


class DictumDetailView(CommonContextMixin, DetailView):
    model = TbDictumAndQuotes
    template_name = "index.html"
    pk_url_kwarg = 'dq_id'
    context_object_name = 'DQ'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Определяем контекст фильтрации (если есть тег в URL)
        active_qs, _ = self.get_filtered_queryset()

        # Используем миксин логики цитаты с учетом фильтра
        extras = self.get_dictum_context(self.request, self.object, queryset=active_qs)
        context.update(extras)

        # Финализируем контекст (куки, тайминги)
        return self.finalize_context(context)


class IndexView(CommonContextMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_qs, _ = self.get_filtered_queryset()

        dq = None
        if active_qs is not None:
             dq = active_qs.order_by('?').first()

        if dq is None:
            # Если тег не задан, или по тегу ничего не нашлось совсем
            # Сбрасываем active_qs на "все", так как специфический контекст пуст
            active_qs = TbDictumAndQuotes.objects.all()

            # Случайная цитата (с учетом истории, чтобы главная страница тоже не зацикливалась)
            seen_ids = self.request.session.get('seen_ids', [])
            dq = active_qs.exclude(id__in=seen_ids).order_by('?').first()

            if dq is None:
                self.request.session['seen_ids'] = []
                dq = active_qs.order_by('?').first()

        if dq:
             # Используем миксин, ОБЯЗАТЕЛЬНО передаем active_qs
            extras = self.get_dictum_context(self.request, dq, queryset=active_qs)
            context.update(extras)

        # Финализируем контекст (куки, тайминги)
        return self.finalize_context(context)
