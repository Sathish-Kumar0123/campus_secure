
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .decorators import roles_required
from .forms import (
    StudentRegistrationForm,
    AddStudentForm,
    AddTeacherForm,
    MarkForm,
    AttendanceForm,
    EventForm,
    EventRosterForm,
    EventReportForm,
)
from .models import (
    User,
    StudentProfile,
    Mark,
    AttendanceRecord,
    Event,
    EventRoster,
    EventReport,
)


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


# Public self-registration is disabled. Staff create student accounts.
def register_student(request):
    messages.info(
        request,
        "Student accounts are created by authorized college staff. Please sign in."
    )
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@login_required
def dashboard(request):
    role = request.user.role
    student = None

    if role == User.Role.STUDENT:
        try:
            student = request.user.student_profile
        except ObjectDoesNotExist:
            messages.error(
                request,
                "Your student profile is missing. Please contact college staff."
            )

    context = {
        "role": role,
        "student": student,
    }

    if student:
        context["marks"] = (
            Mark.objects.filter(student=student)
            .select_related("subject")
        )

        # Calculate class attendance separately from event attendance.
        class_records = AttendanceRecord.objects.filter(
            student=student,
            source="CLASS",
        )
        total = class_records.count()
        present = class_records.filter(
            status=AttendanceRecord.Status.PRESENT
        ).count()

        context["attendance_pct"] = (
            round((present / total) * 100, 1) if total else 0
        )

        context["reports"] = (
            EventReport.objects.filter(student=student)
            .select_related("event")
        )

    elif role in (User.Role.TEACHER, User.Role.HOD):
        context["student_count"] = StudentProfile.objects.count()
        context["teacher_count"] = User.objects.filter(
            role=User.Role.TEACHER
        ).count()
        context["pending_reports"] = (
            EventReport.objects.filter(status=EventReport.Status.PENDING)
            .select_related("student__user", "event")
        )

    else:
        raise PermissionDenied("Your account does not have a valid portal role.")

    return render(request, "dashboard.html", context)


@roles_required(User.Role.TEACHER, User.Role.HOD)
def add_student(request):
    if request.method == "POST":
        form = AddStudentForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, "Student account created successfully.")
                return redirect("dashboard")
            except IntegrityError:
                form.add_error(
                    None,
                    "The username or roll number already exists. Please check the details."
                )
    else:
        form = AddStudentForm()

    return render(
        request,
        "form.html",
        {"form": form, "title": "Add student"},
    )


@roles_required(User.Role.HOD)
def add_teacher(request):
    if request.method == "POST":
        form = AddTeacherForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Teacher account created successfully.")
            return redirect("dashboard")
    else:
        form = AddTeacherForm()

    return render(
        request,
        "form.html",
        {"form": form, "title": "Add teacher"},
    )


@login_required
def marks(request):
    role = request.user.role

    if role == User.Role.STUDENT:
        try:
            student = request.user.student_profile
        except ObjectDoesNotExist:
            raise PermissionDenied("Your student profile is not configured.")

        rows = (
            Mark.objects.filter(student=student)
            .select_related("subject")
        )

    elif role in (User.Role.TEACHER, User.Role.HOD):
        rows = Mark.objects.select_related(
            "student__user", "subject"
        ).all()

    else:
        raise PermissionDenied

    form = None

    if request.method == "POST":
        if role not in (User.Role.TEACHER, User.Role.HOD):
            raise PermissionDenied

        form = MarkForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    obj = form.save(commit=False)
                    obj.updated_by = request.user
                    obj.save()

                messages.success(request, "Mark saved successfully.")
                return redirect("marks")

            except IntegrityError:
                form.add_error(
                    None,
                    "A mark already exists for this student, subject and exam."
                )

    elif role in (User.Role.TEACHER, User.Role.HOD):
        form = MarkForm()

    return render(
        request,
        "marks.html",
        {"rows": rows, "form": form},
    )


@login_required
def attendance(request):
    role = request.user.role

    if role == User.Role.STUDENT:
        try:
            student = request.user.student_profile
        except ObjectDoesNotExist:
            raise PermissionDenied("Your student profile is not configured.")

        rows = (
            AttendanceRecord.objects.filter(student=student)
            .select_related("subject")
        )

    elif role in (User.Role.TEACHER, User.Role.HOD):
        rows = AttendanceRecord.objects.select_related(
            "student__user", "subject"
        ).all()

    else:
        raise PermissionDenied

    form = None

    if request.method == "POST":
        if role not in (User.Role.TEACHER, User.Role.HOD):
            raise PermissionDenied

        form = AttendanceForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    obj = form.save(commit=False)
                    obj.marked_by = request.user
                    obj.source = "CLASS"
                    obj.save()

                messages.success(request, "Attendance saved successfully.")
                return redirect("attendance")

            except IntegrityError:
                form.add_error(
                    None,
                    "Attendance already exists for this student, subject, date and source."
                )

    elif role in (User.Role.TEACHER, User.Role.HOD):
        form = AttendanceForm()

    return render(
        request,
        "attendance.html",
        {"rows": rows, "form": form},
    )


# Staff-only event creation and roster management.
@roles_required(User.Role.TEACHER, User.Role.HOD)
def events(request):
    if request.method == "POST":
        form = EventForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()

            messages.success(
                request,
                "Event created. Add the verified roll numbers to its roster."
            )
            return redirect("events")
    else:
        form = EventForm()

    return render(
        request,
        "events.html",
        {
            "events": Event.objects.select_related("subject").all(),
            "form": form,
            "roster_form": EventRosterForm(),
        },
    )


# Students can see events but cannot create events or change rosters.
@roles_required(User.Role.STUDENT)
def student_events(request):
    return render(
        request,
        "student_events.html",
        {"events": Event.objects.select_related("subject").order_by("-event_date")},
    )


@roles_required(User.Role.TEACHER, User.Role.HOD)
@require_POST
def add_event_roster(request):
    form = EventRosterForm(request.POST)

    if form.is_valid():
        try:
            with transaction.atomic():
                roster_entry = form.save(commit=False)
                roster_entry.roll_number = roster_entry.roll_number.strip()
                roster_entry.save()

            messages.success(request, "Roll number added to the event roster.")

        except IntegrityError:
            messages.error(
                request,
                "That roll number is already on this event roster."
            )
    else:
        messages.error(request, "Please correct the event roster form.")

    return redirect("events")


@roles_required(User.Role.STUDENT)
def submit_event_report(request):
    try:
        student = request.user.student_profile
    except ObjectDoesNotExist:
        raise PermissionDenied("Your student profile is not configured.")

    if request.method == "POST":
        form = EventReportForm(request.POST)

        if form.is_valid():
            event = form.cleaned_data["event"]

            # Only staff-maintained roster entries can verify attendance.
            attended = EventRoster.objects.filter(
                event=event,
                roll_number=student.roll_number,
            ).exists()

            if not attended:
                form.add_error(
                    "event",
                    "Your roll number is not on this event's verified roster. "
                    "No attendance was recorded."
                )
            else:
                try:
                    with transaction.atomic():
                        report, created = EventReport.objects.get_or_create(
                            student=student,
                            event=event,
                            defaults={
                                "description": form.cleaned_data["description"],
                                "status": EventReport.Status.VERIFIED,
                            },
                        )

                        if not created:
                            form.add_error(
                                "event",
                                "You have already submitted a report for this event."
                            )
                        else:
                            AttendanceRecord.objects.get_or_create(
                                student=student,
                                subject=event.subject,
                                date=event.event_date,
                                source="EVENT",
                                defaults={
                                    "status": AttendanceRecord.Status.PRESENT,
                                    "marked_by": event.created_by,
                                },
                            )

                    if created:
                        messages.success(
                            request,
                            "Your roster was verified and event attendance was recorded."
                        )
                        return redirect("dashboard")

                except IntegrityError:
                    form.add_error(
                        None,
                        "The report could not be saved because a conflicting record exists."
                    )
    else:
        form = EventReportForm()

    return render(
        request,
        "form.html",
        {
            "form": form,
            "title": "Submit event attendance report",
        },
    )
