from django.contrib import admin

from .models import Recording, Story


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "created_at", "updated_at")
    search_fields = ("title", "language")


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("story", "order", "created_at")
    list_filter = ("story",)
    search_fields = ("story__title",)
