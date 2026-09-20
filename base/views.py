import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from django.contrib.auth.models import User
from .models import UserProfile, QuestSubmission
from django.utils.timezone import now
from datetime import timedelta
import pytz
from django.shortcuts import get_object_or_404


# Create your views here.

@csrf_exempt
@login_required
def update_balance(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_balance = data.get('balance')

        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.balance = new_balance
        user_profile.save()

        return JsonResponse({"message": "Balance updated successfully", "balance": user_profile.balance})

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def home(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    tz_name = user_profile.timezone if user_profile.timezone else "Asia/Kathmandu"
    user_tz = pytz.timezone(tz_name)
    user_now = now().astimezone(user_tz)

    if user_profile.last_quest:
        last_quest_local_date = user_profile.last_quest.astimezone(user_tz).date()
        quest_marked = (last_quest_local_date == user_now.date())
    else:
        quest_marked = False

    if request.method == "POST":
        description = request.POST.get("description")
        
        user_profile.last_quest = now()  
        user_profile.quest_status = "Yes" 
        user_profile.balance += 10       
        user_profile.save()
        
        uploaded_files = request.FILES.getlist("fileInput")
        saved_urls = []
        
        if uploaded_files:
            from django.core.files.storage import default_storage
            for f in uploaded_files:
                # default_storage will now upload to Cloudinary and return the relative path/filename
                file_name = default_storage.save(f'quest_submissions/{f.name}', f)
                # Obtain the full secure HTTPS URL from Cloudinary
                file_url = default_storage.url(file_name)
                saved_urls.append(file_url)
                
            combined_paths = ",".join(saved_urls)
        else:
            combined_paths = None

        QuestSubmission.objects.create(
            user=request.user,
            work_description=description if description else "No description provided.",
            uploaded_proof=combined_paths
        )
        
        return JsonResponse({
            "status": "success",
            "message": "Daily quest logged!",
            "new_balance": user_profile.balance
        })

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


def authView (request):
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
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                messages.success(request, "Account created successfully")
                return redirect("authView")
        else:
            messages.error(request, "Passwords do not match")

    return render(request, 'registration/signup.html')


from django.core.files.storage import default_storage

@login_required
def gallery(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    tz_name = user_profile.timezone if user_profile.timezone else "Asia/Kathmandu"
    user_tz = pytz.timezone(tz_name)
    user_today = now().astimezone(user_tz).date()
    
    personal_qs = request.user.submissions.all().order_by('-submitted_at')
    public_qs = QuestSubmission.objects.exclude(user=request.user).order_by('-submitted_at')
    
    personal_submissions = []
    for entry in personal_qs:
        # Get raw string safely whether it's a FieldFile, CharField, or None
        raw_proof = str(entry.uploaded_proof) if entry.uploaded_proof else ""
        raw_paths = [path.strip() for path in raw_proof.split(',') if path.strip()]
        
        # Resolve path to full Cloudinary URL if it isn't already a full URL
        formatted_urls = []
        for path in raw_paths:
            if path.startswith('http://') or path.startswith('https://'):
                formatted_urls.append(path)
            else:
                formatted_urls.append(default_storage.url(path))
        
        entry_local_date = entry.submitted_at.astimezone(user_tz).date()
        is_today = (entry_local_date == user_today)
        
        personal_submissions.append({
            'id': entry.id,
            'submitted_at': entry.submitted_at,
            'work_description': entry.work_description,
            'proof_list': formatted_urls,
            'has_proof': bool(formatted_urls),
            'is_today': is_today
        })

    public_submissions = []
    for entry in public_qs:
        # Fixed: str(entry.uploaded_proof) instead of entry.uploaded_proof.name
        raw_proof = str(entry.uploaded_proof) if entry.uploaded_proof else ""
        raw_paths = [path.strip() for path in raw_proof.split(',') if path.strip()]
        
        formatted_urls = []
        for path in raw_paths:
            if path.startswith('http://') or path.startswith('https://'):
                formatted_urls.append(path)
            else:
                formatted_urls.append(default_storage.url(path))
        
        public_submissions.append({
            'user': entry.user,
            'submitted_at': entry.submitted_at,
            'work_description': entry.work_description,
            'proof_list': formatted_urls,
            'has_proof': bool(formatted_urls)
        })
    
    return render(request, "gallery.html", {
        'personal_submissions': personal_submissions,
        'public_submissions': public_submissions,
        'balance': user_profile.balance
    })


@login_required
def delete_quest(request, pk):
    if request.method == "POST":
        user_profile = UserProfile.objects.get(user=request.user)
        submission = get_object_or_404(QuestSubmission, pk=pk, user=request.user)
        
        tz_name = user_profile.timezone if user_profile.timezone else "Asia/Kathmandu"
        user_tz = pytz.timezone(tz_name)
        user_today = now().astimezone(user_tz).date()
        
        submission_local_date = submission.submitted_at.astimezone(user_tz).date()
        
        # Strictly enforce same-day deletion
        if submission_local_date == user_today:
            submission.delete()
            user_profile.balance -= 10
            user_profile.last_quest = None
            user_profile.quest_status = None
            user_profile.save()
            messages.success(request, "Quest submission deleted successfully.")
        else:
            messages.error(request, "You can only delete quest submissions created today.")
            
    return redirect('quests')