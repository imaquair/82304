import re

from django.contrib import messages
from django.conf import settings
from django.db.models import Count, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .models import Recording, Story, Keyword

CREATE_GATE_SESSION_KEY = "create_story_access_granted"

_PUNCT_STRIP = ".,;:!?«»\"'()[]…"


def segment_transcript_with_keywords(text, keywords):
    """Split transcript into space / word segments; words matching a Keyword get a translation."""
    kw_map = {kw.original_keyword: kw.english_translation for kw in keywords}
    segments = []
    for m in re.finditer(r"(\s+)|(\S+)", text):
        if m.group(1):
            segments.append({"kind": "space", "text": m.group(1)})
            continue
        word = m.group(2)
        trans = kw_map.get(word)
        if trans is None and word:
            stripped = word.strip(_PUNCT_STRIP)
            trans = kw_map.get(stripped)
        segments.append({"kind": "word", "text": word, "translation": trans})
    return segments


def previous_transcript_segments_for_story(story):
    last_rec = story.recordings.last()
    if last_rec is None:
        return None
    return segment_transcript_with_keywords(
        last_rec.transcript_english or "",
        last_rec.keywords.all(),
    )


@require_http_methods(["GET", "POST"])
def create_story(request):
    create_story_password = getattr(settings, "CREATE_STORY_PASSWORD", "")
    if create_story_password and not request.session.get(CREATE_GATE_SESSION_KEY, False):
        if request.method == "POST" and "create_access_password" in request.POST:
            submitted_password = request.POST.get("create_access_password", "")
            if submitted_password == create_story_password:
                request.session[CREATE_GATE_SESSION_KEY] = True
                return redirect("create")
            return render(
                request,
                "create_gate.html",
                {"gate_error": "Incorrect password. Try again."},
            )
        return render(request, "create_gate.html", {})

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
        # ensure keywords exist
        for i in range(1, 4):
            original = request.POST.get(f"keyword_{i}", "").strip()
            english = request.POST.get(f"keyword_en_{i}", "").strip()
            if not (original and english) and not ("Three keywords are required" in errors):
                errors.append("Three keywords are required")


        if errors:
            return render(
                request,
                "create_story.html",
                {
                    "errors": errors,
                    "title": title,
                    "language": language.capitalize(),
                    "english_text": english_text,
                },
            )

        story = Story.objects.create(
            title=title[:255],
            language=language[:50],
            english_text=english_text,
        )
        if not audio:
            audio = None
        recording = Recording.objects.create(
            story=story,
            audio_file=audio,
            order=1,
            language=language[:50].capitalize(),
            transcript_original=english_text,
            transcript_english=english_text
        )
        # save the keywords
        for i in range(1, 4):
            original = request.POST.get(f"keyword_{i}", "").strip()
            english = request.POST.get(f"keyword_en_{i}", "").strip()
            if original or english:
                Keyword.objects.create(
                    recording=recording,
                    original_keyword=original[:100],
                    english_translation=english[:100],
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
    """In progress: fewer than 20 recordings. Completed: 20 or more."""
    tab = request.GET.get("tab", "in_progress")
    if tab not in ("in_progress", "completed"):
        tab = "in_progress"

    annotated = Story.objects.annotate(recording_count=Count("recordings"))
    if tab == "completed":
        stories = annotated.filter(recording_count__gte=20)
    else:
        stories = annotated.filter(recording_count__lt=20)

    return render(
        request,
        "library.html",
        {"stories": stories, "active_tab": tab},
    )

@require_http_methods(["GET", "POST"])
def add_to_story(request, pk):
    story = get_object_or_404(Story, pk=pk)

    if request.method == "POST":
        language = request.POST.get("language", "").strip()
        english_text = request.POST.get("english_text", "").strip()
        audio = request.FILES.get("audio")

        errors = []
        if not language:
            errors.append("Language is required.")
        if not english_text and not audio:
            errors.append("Add text or record audio before submitting.")
        # ensure keywords exist
        for i in range(1, 4):
            original = request.POST.get(f"keyword_{i}", "").strip()
            english = request.POST.get(f"keyword_en_{i}", "").strip()
            if not (original and english) and not ("Three keywords are required" in errors):
                errors.append("Three keywords are required")

        if errors:
            return render(
                request,
                "add_to_story.html",
                {
                    "story": story,
                    "errors": errors,
                    "language": language.capitalize(),
                    "english_text": english_text,
                    "previous_transcript_segments": previous_transcript_segments_for_story(
                        story
                    ),
                    "previous_recording": story.recordings.last(),
                },
            )

        max_order = story.recordings.aggregate(m=Max("order"))["m"]
        next_order = (max_order or 0) + 1
        recording_payload = {
            "story": story,
            "order": next_order,
            "language": language[:50].capitalize(),
            "transcript_original": english_text,
            "transcript_english": english_text,
        }
        if not audio:
            audio = None
        recording_payload["audio_file"] = audio
        recording = Recording.objects.create(**recording_payload)

        # save the keywords
        for i in range(1, 4):
            original = request.POST.get(f"keyword_{i}", "").strip()
            english = request.POST.get(f"keyword_en_{i}", "").strip()
            if original and english:
                Keyword.objects.create(
                    recording=recording,
                    original_keyword=original[:100],
                    english_translation=english[:100],
                )

        messages.success(request, f'Added part {next_order} to "{story.title}".')
        return redirect("home")
    return render(
        request,
        "add_to_story.html",
        {
            "story": story,
            "previous_transcript_segments": previous_transcript_segments_for_story(story),
            "previous_recording": story.recordings.last(),
        },
    )

@require_http_methods(["GET"])
def read_story(request, pk):
    story = get_object_or_404(Story, pk=pk)

    tab = request.GET.get("tab", "read")
    if tab not in ("read", "listen"):
        tab = "read"

    return render(request, "read_story.html", {"story": story, "active_tab": tab})