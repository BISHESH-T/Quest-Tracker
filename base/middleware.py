# base/middleware.py
import zoneinfo
from django.utils import timezone
from .models import UserProfile

DEFAULT_TZ = "Asia/Kathmandu"


def _valid(name):
    try:
        zoneinfo.ZoneInfo(name)
        return True
    except (zoneinfo.ZoneInfoNotFoundError, ValueError, TypeError):
        return False


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_name = DEFAULT_TZ

        if request.user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            cookie_tz = request.COOKIES.get("user_tz")

            # save the browser's timezone to the profile when it changes
            if cookie_tz and _valid(cookie_tz) and profile.timezone != cookie_tz:
                profile.timezone = cookie_tz
                profile.save(update_fields=["timezone"])

            if profile.timezone and _valid(profile.timezone):
                tz_name = profile.timezone

        timezone.activate(zoneinfo.ZoneInfo(tz_name))
        response = self.get_response(request)
        timezone.deactivate()
        return response