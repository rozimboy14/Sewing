import attrs
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken

from users.models import CustomUser


class LoginSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['username'] = serializers.CharField(required=True)
        self.fields['password'] = serializers.CharField(
            required=True, write_only=True  # login uchun faqat yozish mumkin
        )
    def validate(self, attrs):
        data=super().validate(attrs)
        data['full_name']=self.user.full_name
        data['role'] = self.user.role
        data['username'] = self.user.username
        data['warehouse'] = self.user.warehouse.name
        return data

    def get_user(self, *args, **kwargs):
        users = CustomUser.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError(
                {
                    "message": "User not found",
                }
            )
        return users.first()

class LoginRefreshSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data =super().validate(attrs)
        access_token_instance =AccessToken(data["access_token"])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(CustomUser,id=user_id)
        update_last_login(None, user)
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "role",
            "email",
            "phone_number",
            "date_joined",
            "full_name",
        )
        read_only_fields = fields  # barcha fieldlar faqat o‘qish uchun
