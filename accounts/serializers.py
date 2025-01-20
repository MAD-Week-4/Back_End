# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)  # 사용자 이름 포함
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'email', 'assets']