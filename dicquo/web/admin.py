# -*- coding: utf-8 -*-
from django.contrib import admin
from web.models import TbDictumAndQuotes, TbAuthor, TbImages, TbOrigin


# Register your models here.
class AdmDictumAndQuotesAdmin(admin.ModelAdmin):
    search_fields = ['id', 'szIntro', 'szContent', ]
    list_display = ('id', 'szIntro', 'szContent', 'tag_list', 'iViewCounter', 'dtEdited', )
    list_display_links = ('id', 'szIntro', 'szContent', )
    # list_filter = ('iViewCounter', )
    empty_value_display = u"<b style='color:red;'>-empty-</b>"
    actions_on_top = False
    actions_on_bottom = True
    actions_selection_counter = True
    # погасить кнопку "Добавить" в интерфейсе админки
    # def has_add_permission(self, request):
    #     return False
    # fieldsets = (
    #     (None, {'fields': ('szIntro', 'iViewCounter', 'tags',)}),
    # )

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

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


class AdmAuthor(admin.ModelAdmin):
    search_fields = ['id', 'szAuthor', 'szCaption', ]
    list_display = ('id', 'szAuthor', 'tag_list', 'iViewCounter', 'dtEdited',)
    list_display_links = ('id', 'szAuthor')
    empty_value_display = u"<b style='color:red;'>-empty-</b>"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


admin.site.register(TbDictumAndQuotes, AdmDictumAndQuotesAdmin)
admin.site.register(TbOrigin, AdmOrigin)
admin.site.register(TbImages, AdmImages)
admin.site.register(TbAuthor, AdmAuthor)
