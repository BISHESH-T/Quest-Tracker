from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField(default=0)  
    last_quest = models.DateTimeField(null=True, blank=True)  
    quest_status = models.CharField(max_length=10, null=True, blank=True)
    timezone = models.CharField(max_length=50, default="Asia/Kathmandu")  

    def __str__(self):
        return f"{self.user.username} - {self.balance}"

# --- UPDATED DIRECT TRACKING MODEL ---
class QuestSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    work_description = models.TextField()
    
    # 👑 THE FIX: Explicitly increase max_length to 1000 characters
    uploaded_proof = models.FileField(upload_to='quest_submissions/', max_length=1000, null=True, blank=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Entry on {self.submitted_at.date()}"