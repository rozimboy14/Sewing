from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, \
    TokenRefreshView

from users.serializers import LoginSerializer, ProfileSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        data = getattr(response, "data", None)
        if data is not None:
            access_token = data.get("access")
            refresh_token = data.get("refresh")

            if access_token:
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=False,  # True in production
                    samesite="Lax",
                    path="/",
                    max_age=3600,  # 1 soat
                )

            if refresh_token:
                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    path="/",
                    max_age=7 * 24 * 3600,  # 7 kun
                )

        return super().finalize_response(request, response, *args, **kwargs)


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get("refresh_token")
        if not refresh:
            return Response({"detail": "No refresh token in cookies."}, status=401)

        request.data["refresh"] = refresh  # cookie dan refresh token qo‘shish

        try:
            response = super().post(request, *args, **kwargs)
        except (TokenError, InvalidToken):
            return Response({"detail": "Invalid or blacklisted refresh token."}, status=401)

        # Tokenlarni yangilab cookie’ga yozish
        new_access = response.data.get("access")
        new_refresh = response.data.get("refresh")

        if new_access:
            response.set_cookie(
                key="access_token",
                value=new_access,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
                max_age=3600,
            )

        if new_refresh:
            response.set_cookie(
                key="refresh_token",
                value=new_refresh,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
                max_age=7 * 24 * 3600,
            )

        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token not found."}, status=401)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid or already blacklisted token."}, status=400)

        response = Response({"detail": "Successfully logged out."}, status=200)
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(
            request.user, context={
                "request": request})
        return Response(serializer.data)

