from django.contrib import admin

from .models import Recording, Story, Keyword


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "created_at", "updated_at")
    search_fields = ("title", "language")


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("story", "order", "created_at")
    list_filter = ("story",)
    search_fields = ("story__title",)

@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ("recording", "original_keyword", "english_translation")
    list_filter = ("recording",)
