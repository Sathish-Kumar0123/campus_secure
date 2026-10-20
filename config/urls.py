
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from portal import views


urlpatterns = [
    path("admin/", admin.site.urls),

    # Website authentication
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Student registration is disabled for public users.
    path("register/", views.register_student, name="register"),

    # Dashboards and academic records
    path("dashboard/", views.dashboard, name="dashboard"),
    path("students/add/", views.add_student, name="add_student"),
    path("teachers/add/", views.add_teacher, name="add_teacher"),
    path("marks/", views.marks, name="marks"),
    path("attendance/", views.attendance, name="attendance"),

    # Events
    path("events/", views.events, name="events"),
    path("events/view/", views.student_events, name="student_events"),
    path(
        "events/report/",
        views.submit_event_report,
        name="submit_event_report",
    ),
    path(
        "events/roster/add/",
        views.add_event_roster,
        name="add_event_roster",
    ),

    # JWT API authentication
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
