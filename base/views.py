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
    # 1. Profile Safeguard: Get profile or create one on the fly if it doesn't exist
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # 2. Timezone Normalization (Defaults to Kathmandu Valley standard time)
    user_tz = pytz.timezone(user_profile.timezone if user_profile.timezone else "Asia/Kathmandu")
    user_now = now().astimezone(user_tz)
    
    # Extract the calendar date of the last successful check-in
    last_quest_date = user_profile.last_quest.astimezone(user_tz).date() if user_profile.last_quest else None


    # 4. Form Action Engine: Process the daily check-in/quest submission
    if request.method == "POST":
        description = request.POST.get("description")
        
        # 🔓 SAFE LOGIC UPDATES: Update the core profile values once
        submission_time = now()
        user_profile.last_quest = submission_time  
        user_profile.quest_status = "Yes" 
        user_profile.balance += 10       
        user_profile.save()
        
        # Sync the local tracking date string instantly for Section 5
        last_quest_date = submission_time.astimezone(user_tz).date()
        
        # 👑 COMMA-SEPARATED MULTI-FILE HANDLING
        uploaded_files = request.FILES.getlist("fileInput")
        saved_paths = []
        
        if uploaded_files:
            from django.core.files.storage import default_storage
            for f in uploaded_files:
                # Manually write each file into the storage engine directory
                file_name = default_storage.save(f'quest_submissions/{f.name}', f)
                saved_paths.append(file_name)
                
            # Combine paths array list down into a single flat string variable container row
            combined_paths = ",".join(saved_paths)
        else:
            combined_paths = None

        # Creates exactly ONE database row entry per submission event (without is_public)
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

    quest_marked = (last_quest_date == user_now.date())
    
    # Calculate exact seconds remaining until next local midnight reset
    next_reset = user_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    time_remaining_seconds = int((next_reset - user_now).total_seconds())

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


@login_required
def gallery(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    personal_qs = request.user.submissions.all().order_by('-submitted_at')
    
    public_qs = QuestSubmission.objects.exclude(user=request.user).order_by('-submitted_at')
    
    personal_submissions = []
    for entry in personal_qs:
        # Check if the field has a file name string present
        proof_list = entry.uploaded_proof.name.split(',') if entry.uploaded_proof else []
        
        personal_submissions.append({
            'submitted_at': entry.submitted_at,
            'work_description': entry.work_description,
            'proof_list': [p.strip() for p in proof_list if p.strip()],
            'has_proof': bool(proof_list)
        })

    public_submissions = []
    for entry in public_qs:
        proof_list = entry.uploaded_proof.name.split(',') if entry.uploaded_proof else []
        
        public_submissions.append({
            'user': entry.user,
            'submitted_at': entry.submitted_at,
            'work_description': entry.work_description,
            'proof_list': [p.strip() for p in proof_list if p.strip()],
            'has_proof': bool(proof_list)
        })
    
    return render(request, "gallery.html", {
        'personal_submissions': personal_submissions,
        'public_submissions': public_submissions,
        'balance': user_profile.balance
    })