from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, Subject, Mark, AttendanceRecord, Event, EventRoster, EventReport

@admin.register(User)
class PortalUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Portal role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Portal role", {"fields": ("role",)}),)

admin.site.register([StudentProfile, Subject, Mark, AttendanceRecord, Event, EventRoster, EventReport])
