from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class LoginUser(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


import uuid
from django.db import models
from .models import LoginUser

class Message(models.Model):
    user = models.ForeignKey(LoginUser, on_delete=models.CASCADE, related_name='messages', null=True)
    content = models.TextField()
    sender = models.CharField(max_length=255, default="user")  # or "bot"
    timestamp = models.DateTimeField(auto_now_add=True)
    conversation_id = models.UUIDField(default=uuid.uuid4)
