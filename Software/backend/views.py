from django.contrib import messages
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .models import Recording, Story


@require_http_methods(["GET", "POST"])
def create_story(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        language = request.POST.get("language", "").strip()
        english_text = request.POST.get("english_text", "").strip()
        audio = request.FILES.get("audio")

        errors = []
        if not title:
            errors.append("Title is required.")
        if not language:
            errors.append("Language is required.")

        if errors:
            return render(
                request,
                "create_story.html",
                {
                    "errors": errors,
                    "title": title,
                    "language": language,
                    "english_text": english_text,
                },
            )

        story = Story.objects.create(
            title=title[:255],
            language=language[:50],
            english_text=english_text,
        )
        if audio:
            Recording.objects.create(
                story=story,
                audio_file=audio,
                order=1,
            )
        messages.success(request, "Story created.")
        return redirect("home")

    return render(request, "create_story.html", {})


def record_audio(request, story_id=None):
    if story_id is None:
        stories = Story.objects.order_by("-created_at")
        return render(request, "record.html", {"story": None, "stories": stories})
    story = get_object_or_404(Story, pk=story_id)
    return render(request, "record.html", {"story": story, "stories": None})


@require_POST
def save_audio_recording(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    audio = request.FILES.get("audio")
    if not audio:
        return JsonResponse({"error": "No audio file was uploaded."}, status=400)

    max_order = story.recordings.aggregate(m=Max("order"))["m"]
    next_order = (max_order or 0) + 1
    recording = Recording.objects.create(
        story=story,
        audio_file=audio,
        order=next_order,
    )
    return JsonResponse(
        {
            "ok": True,
            "recording_id": recording.id,
            "order": recording.order,
            "file_url": recording.audio_file.url,
        }
    )

def get_story_library(request):
    stories = Story.objects.all() 
    
    return render(request, 'library.html', {'stories': stories})
