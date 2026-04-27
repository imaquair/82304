from django.db import models


class Story(models.Model):
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=50)
    english_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Recording(models.Model):
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name="recordings",
    )
    audio_file = models.FileField(upload_to="recordings/", blank=True, null=True)
    order = models.PositiveIntegerField()
    language = models.CharField(max_length=50)
    transcript_original = models.TextField(blank=True)
    transcript_english = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.story.title} - part {self.order}"
    
class Keyword(models.Model):
    recording = models.ForeignKey(
        Recording,
        on_delete=models.CASCADE,
        related_name="keywords",
    )
    original_keyword = models.TextField(blank=True)
    english_translation = models.TextField(blank=True)
