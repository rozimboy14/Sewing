from django.urls import path
from .views import LoginView, CookieTokenRefreshView, LogoutView, ProfileView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),           # JWT login + cookie
    path('refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),  # Refresh token cookie
    path('logout/', LogoutView.as_view(), name='logout'),        # Logout + blacklist
    path('me/',ProfileView.as_view(), name='profile'),
]
