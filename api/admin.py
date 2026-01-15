from django.contrib import admin
from .models import User, Session, Location, Announcement, UserProfile, SavedAnnouncement, ViewedAnnouncement

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'created_at', 'is_active')
    search_fields = ('username', 'email')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'expires_at', 'is_valid')
    list_filter = ('is_valid', 'created_at')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'owner', 'created_at')
    list_filter = ('type',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'delivery_mode', 'is_active', 'view_count', 'created_at')
    list_filter = ('delivery_mode', 'is_active', 'policy_type')
    search_fields = ('title', 'content')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'value', 'created_at')
    list_filter = ('key',)

@admin.register(SavedAnnouncement)
class SavedAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('user', 'announcement', 'saved_at')

@admin.register(ViewedAnnouncement)
class ViewedAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('user', 'announcement', 'viewed_at')