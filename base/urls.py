from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import authView
from .views import home
from .views import signup
from .views import update_balance
from .views import gallery
from .views import delete_quest
urlpatterns = [
    path("", home, name="home"),
    path("signup/", signup, name="signup"),
    path("login/", authView, name="authView"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('update_balance/', update_balance, name='update_balance'),
    path('quests/', gallery, name='quests'),
    path('quests/<int:pk>/delete/', delete_quest, name='delete_quest'),
]
