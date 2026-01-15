from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid
import json
from datetime import datetime, timedelta

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('O usuário deve ter um username')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.username
class Session(models.Model):
    
    id = models.AutoField(primary_key=True)
    
    # Se quiser manter UUID para tokens de sessão, adicione campo separado:
    token = models.CharField(max_length=100, unique=True)  # OU UUID como string
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Session {self.id} - {self.user.username}"
    

class Location(models.Model):
    LOCATION_TYPES = [
        ('GPS', 'GPS Coordinates'),
        ('WIFI', 'WiFi IDs'),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=LOCATION_TYPES, default='GPS')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    radius_meters = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    wifi_ids_csv = models.TextField(blank=True, null=True)  # IDs separados por vírgula
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'key']
    
    def __str__(self):
        return f"{self.user.username}: {self.key}={self.value}"

class Announcement(models.Model):
    POLICY_TYPES = [
        ('WHITELIST', 'Whitelist'),
        ('BLACKLIST', 'Blacklist'),
    ]
    
    DELIVERY_MODES = [
        ('CENTRALIZED', 'Centralized'),
        ('DECENTRALIZED', 'Decentralized'),
    ]
    
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    policy_type = models.CharField(max_length=10, choices=POLICY_TYPES, default='WHITELIST')
    profile_restrictions_json = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    delivery_mode = models.CharField(max_length=15, choices=DELIVERY_MODES, default='CENTRALIZED')
    is_active = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class SavedAnnouncement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_announcements')
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'announcement']
    
    def __str__(self):
        return f"{self.user.username} saved {self.announcement.title}"

class ViewedAnnouncement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_announcements')
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='viewed_by')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'announcement']
    
    def __str__(self):
        return f"{self.user.username} viewed {self.announcement.title}"