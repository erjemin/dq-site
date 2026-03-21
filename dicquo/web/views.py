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

        # Если мы переключили контекст (например, выбрали другой тег), имеет смысл сбросить историю?
        # Или можно оставить, так как уникальность ID глобальна.
        # Проблема: если seen_ids забит цитатами, а мы выбрали тег, где всего 2 цитаты,
        # и они обе случайно оказались в seen_ids (потому что мы их видели раньше без тега),
        # то exclude исключит всё.

        # Решение: принудительно добавить текущую цитату, если её нет
        if dq.id not in seen_ids:
            seen_ids.append(dq.id)
            if len(seen_ids) > 100:
                seen_ids.pop(0)
            request.session['seen_ids'] = seen_ids

        context.update({'DQ': dq})
        # slag текущей цитаты
        context.update({"DQ_SLUG": pytils.translit.slugify(dq.szContent.lower()[:120])})

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
        # Сначала пробуем найти следующую цитату, которую мы еще не видели
        dq_next = queryset.exclude(id__in=seen_ids).order_by('?').first()

        # Если таких нет (мы посмотрели все цитаты в этом контексте/теге)
        if dq_next is None:
            # СБРОС ИСТОРИИ!
            # Мы посмотрели всё, что было по этому фильтру. Начинаем круг заново.
            # Но удалять ВСЮ историю сессии опасно (вдруг мы вернемся в общий список).
            # Лучше локально для выбора следующей цитаты игнорировать историю,
            # но возможно стоит очистить сессию, чтобы цикл начался чисто.

            # Вариант: Очистить seen_ids, чтобы в следующий раз (на некст странице) список был пуст?
            # Или просто выбрать любую КРОМЕ текущей?

            dq_next = queryset.exclude(id=dq.id).order_by('?').first()

            # Если мы действительно прошли весь цикл по тегу, логично сбросить seen_ids,
            # чтобы пользователь мог заново проходить этот список случайно, а не "застревать" на последних.
            # Однако, очистка seen_ids здесь повлияет на глобальную сессию.
            # Если тег "red" (2 цитаты), мы их посмотрели. seen_ids=[1,2].
            # queryset=[1,2]. exclude -> []. dq_next=None.
            # Fallback: exclude(current) -> [1] (если cur=2). dq_next=1.
            # User goes to 1. seen_ids=[1,2] (set logic handles dupes/order? No, list appends).
            # seen_ids=[1,2,1].
            # Next request (dq=1). queryset=[1,2]. exclude([1,2,1]) -> []. dq_next=2.
            # It loops 1-2-1-2.

            # Чтобы разорвать этот малый круг и сделать его снова "случайным" (если там >2 элементов, но меньше 100),
            # нужно очистить seen_ids, если мы уткнулись в конец списка.
            # Но удалять нужно только те ID, которые принадлежат этому queryset? Сложно.
            # Проще очистить всё, так как пользователь явно "наелся" текущим контекстом и пошел по второму кругу.
            request.session['seen_ids'] = []

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
        context['ticks'] = total_time * 1000
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
        seen_ids = self.request.session.get('seen_ids', [])

        if active_qs is not None:
             # Если мы в режиме фильтрации, тоже стараемся не показывать то, что уже видели
             dq = active_qs.exclude(id__in=seen_ids).order_by('?').first()

             # Если после фильтрации ничего не осталось (мы просмотрели все цитаты тега)
             if dq is None:
                 # Сбрасываем историю и берем любую
                 self.request.session['seen_ids'] = []
                 dq = active_qs.order_by('?').first()

        if dq is None:
            # Если тег не задан, или по тегу ничего не нашлось совсем
            # Сбрасываем active_qs на "все", так как специфический контекст пуст
            active_qs = TbDictumAndQuotes.objects.all()

            # Случайная цитата (с учетом истории, чтобы главная страница тоже не зацикливалась)
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
