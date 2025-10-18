# authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)

        # 1. Agar headerda token bo'lmasa, cookie dan o'qish
        if header is None:
            raw_token = request.COOKIES.get("access_token")
            if raw_token is None:
                return None
        else:
            raw_token = self.get_raw_token(header)

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
