# -*- coding: utf-8 -*-
__author__ = "Sergei Erjemin"
__copyright__ = "Copyright 2020-2026, Sergei Erjemin"
__credits__ = ["Sergei Erjemin", ]
__license__ = "GPL"
__version__ = "0.3.9"
__maintainer__ = "Sergei Erjemin"
__email__ = "erjemin@gmail.com"
__status__ = "in progress"

from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
import time
import hashlib
import random
import pytils
from taggit.models import Tag
from web.models import TbOrigin, TbDictumAndQuotes, TbImages, TbAuthor


# Create your views here.
def for_dq(dq):
    to_template = {}
    num = int(hashlib.blake2s(dq.szContent.encode("utf-8"), digest_size=1).hexdigest(), 16)
    clr = sorted([num / 2, num / 3, num / 5, num / 7, num / 11, num / 1.5], key=lambda A: random.random())
    to_template.update({'CLR': clr})
    to_template.update({'DQ': dq})
    try:
        au = TbAuthor.objects.get(id=dq.kAuthor_id)
        to_template.update({'AUTHOR': au})
        tags = au.tags.names()
    except ObjectDoesNotExist:
        tags = dq.tags.names()
    tag_and_slug = []
    for i in tags:
        tag_and_slug.append({"name": i, "slug": pytils.translit.slugify(i.lower())[:120]})
    to_template.update({'TAGS': sorted(tag_and_slug, key=lambda x: x["name"])})  # tag_and_slug
    if dq.kImages_id is None:
        if len(tags) != 0:
            try:
                # tagged_image = TbImages.objects.filter(tags__name__in=tags).order_by('?').first()
                tagged_image = TbImages.objects.filter(tags__name__in=tags)
                random.shuffle(list(tagged_image))
                to_template.update({'IMAGE': tagged_image[0].imFile})
            except IndexError:
                pass
    else:
        to_template.update({'IMAGE': dq.kImages.imFile})
    dq.iViewCounter += 1
    dq.save()
    # dq_next = TbDictumAndQuotes.objects.exclude(id=dq.id).order_by('?').first()
    dq_next = TbDictumAndQuotes.objects.exclude(id=dq.id)
    random.shuffle(list(dq_next))
    to_template.update({"NEXT": dq_next[0].id})
    to_template.update({"NEXT_TXT": pytils.translit.slugify(dq_next[0].szContent.lower()[:120])})
    return to_template


def by_id(request, dq_id):
    t_start = time.process_time()
    template = "index.html"  # шаблон
    dq = TbDictumAndQuotes.objects.get(id=dq_id)
    to_template = for_dq(dq)
    # пероверка, что посетитель согласился со сбором даных через cookies
    if request.COOKIES.get('cookie_accept'):
        to_template.update({'cookie_accept': 1})
    to_template.update({'ticks': float(time.process_time() - t_start)})
    response = render(request, template, to_template)
    return response


def index(request):
    t_start = time.process_time()
    # проверка на аутентификацию
    # if not request.user.is_authenticated():
    #     return HttpResponseRedirect("/access")
    template = "index.html"  # шаблон
    dq_ = TbDictumAndQuotes.objects
    if request.GET.get('tag'):
        dq = dq_.filter(kAuthor__tags__slug__in=[request.GET['tag']]).order_by('?').first()
        if dq is None:
            dq = dq_.filter(tags__slug__in=[request.GET['tag']]).order_by('?').first()
            if dq is None:
                dq = dq_.order_by('?').first()
    else:
        dq = dq_.first()
    to_template = for_dq(dq)
    # пероверка, что посетитель согласился со сбором даных через cookies
    if request.COOKIES.get('cookie_accept'):
        to_template.update({'cookie_accept': 1})
    to_template.update({'ticks': float(time.process_time() - t_start)})
    response = render(request, template, to_template)
    return response

