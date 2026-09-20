import json
from datetime import timedelta

import pytz
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db import OperationalError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from .models import QuestSubmission, UserProfile

MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2 MB
DEFAULT_TZ = "Asia/Kathmandu"


def get_user_tz(profile):
    return pytz.timezone(profile.timezone or DEFAULT_TZ)


def build_proof_urls(entry):
    raw_proof = str(entry.uploaded_proof) if entry.uploaded_proof else ""
    paths = [p.strip() for p in raw_proof.split(',') if p.strip()]
    return [
        p if p.startswith(('http://', 'https://')) else default_storage.url(p)
        for p in paths
    ]


@login_required
def update_balance(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request"}, status=405)

    profile = UserProfile.objects.get(user=request.user)

    # home() clears stale statuses on load, so non-None means already answered today
    if profile.quest_status is not None:
        return JsonResponse({"error": "Already answered today"}, status=409)

    profile.balance = max(0, profile.balance - 50)  # or use IntegerField and drop max()
    profile.quest_status = "No"
    profile.last_quest = now()
    profile.save()

    return JsonResponse({
        "balance": profile.balance,
        "quest_status": profile.quest_status,
    })


@login_required
def home(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    user_tz = get_user_tz(user_profile)
    user_now = now().astimezone(user_tz)

    if user_profile.last_quest:
        last_quest_local_date = user_profile.last_quest.astimezone(user_tz).date()
        quest_marked = (last_quest_local_date == user_now.date())

        # Only reset if it's a completely new calendar day
        if not quest_marked and user_profile.quest_status is not None:
            user_profile.quest_status = None
            user_profile.last_quest = None
            user_profile.save()
    else:
        quest_marked = False
        if user_profile.quest_status is not None:
            user_profile.quest_status = None
            user_profile.save()

    if request.method == "POST":
        description = request.POST.get("description")
        uploaded_files = request.FILES.getlist("fileInput")

        for f in uploaded_files:
            if f.size > MAX_UPLOAD_SIZE:
                return JsonResponse(
                    {"status": "error", "message": f'"{f.name}" is larger than 2 MB.'},
                    status=413,
                )

        try:
            with transaction.atomic():
                profile = UserProfile.objects.select_for_update().get(pk=user_profile.pk)

                if profile.quest_status is not None:
                    return JsonResponse(
                        {"status": "error", "message": "Already answered today."},
                        status=409,
                    )

                saved_urls = []
                for f in uploaded_files:
                    name = default_storage.save(f'quest_submissions/{f.name}', f)
                    saved_urls.append(default_storage.url(name))

                QuestSubmission.objects.create(
                    user=request.user,
                    work_description=description or "No description provided.",
                    uploaded_proof=",".join(saved_urls) or None,
                )

                profile.quest_status = "Yes"
                profile.last_quest = now()
                profile.balance += 10
                profile.save()
        except OperationalError:
            # e.g. SQLite "database is locked" when two submits collide
            return JsonResponse(
                {"status": "error", "message": "Already answered today."},
                status=409,
            )

        return JsonResponse({
            "status": "success",
            "message": "Daily quest logged!",
            "new_balance": profile.balance,
        })

    # GET falls through to here (function level, not inside the if)
    next_reset = user_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    time_remaining_seconds = max(0, int((next_reset - user_now).total_seconds()))

    hours = time_remaining_seconds // 3600
    minutes = (time_remaining_seconds % 3600) // 60
    seconds = time_remaining_seconds % 60
    time_remaining_hms = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return render(request, "home_page.html", {
        'username': request.user.username,
        'balance': user_profile.balance,
        'quest_marked': quest_marked,
        'quest_submitted': quest_marked,
        'time_remaining': time_remaining_hms,
        'time_remaining_seconds': time_remaining_seconds,
        'quest_status': user_profile.quest_status,
    })


def authView(request):
    if request.method == "POST":
        username_email = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username_email, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            messages.error(request, "Account or password error")
            return redirect("authView")

    return render(request, "registration/login.html")


def signup(request):
    if request.method == "POST":
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('pass1')
        password2 = request.POST.get('pass2')

        if password1 == password2:
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already in use.")
            elif User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
            else:
                User.objects.create_user(username=username, email=email, password=password1)
                messages.success(request, "Account created successfully")
                return redirect("authView")
        else:
            messages.error(request, "Passwords do not match")

    return render(request, 'registration/signup.html')


@login_required
def gallery(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user_tz = get_user_tz(user_profile)
    user_today = now().astimezone(user_tz).date()

    personal_qs = request.user.submissions.all().order_by('-submitted_at')
    public_qs = QuestSubmission.objects.exclude(user=request.user).order_by('-submitted_at')

    personal_submissions = []
    for entry in personal_qs:
        proof_list = build_proof_urls(entry)
        personal_submissions.append({
            'id': entry.id,
            'submitted_at': entry.submitted_at,
            'work_description': entry.work_description,
            'proof_list': proof_list,
            'has_proof': bool(proof_list),
            'is_today': entry.submitted_at.astimezone(user_tz).date() == user_today,
        })

    public_submissions = []
    for entry in public_qs:
        proof_list = build_proof_urls(entry)
        public_submissions.append({
            'user': entry.user,
            'submitted_at': entry.submitted_at,
            'work_description': entry.work_description,
            'proof_list': proof_list,
            'has_proof': bool(proof_list),
        })

    return render(request, "gallery.html", {
        'personal_submissions': personal_submissions,
        'public_submissions': public_submissions,
        'balance': user_profile.balance,
    })


@login_required
def delete_quest(request, pk):
    if request.method == "POST":
        user_profile = UserProfile.objects.get(user=request.user)
        submission = get_object_or_404(QuestSubmission, pk=pk, user=request.user)

        user_tz = get_user_tz(user_profile)
        user_today = now().astimezone(user_tz).date()

        if submission.submitted_at.astimezone(user_tz).date() == user_today:
            submission.delete()
            user_profile.balance = max(0, user_profile.balance - 10)
            user_profile.last_quest = None
            user_profile.quest_status = None
            user_profile.save()
            messages.success(request, "Quest submission deleted successfully.")
        else:
            messages.error(request, "You can only delete quest submissions created today.")

    return redirect('quests')