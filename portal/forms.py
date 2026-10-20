
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import (
    User,
    StudentProfile,
    Mark,
    AttendanceRecord,
    Event,
    EventRoster,
    EventReport,
)


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    roll_number = forms.CharField(max_length=24)
    department = forms.CharField(max_length=80, initial="CSE")
    year = forms.IntegerField(min_value=1, max_value=6, initial=4)
    section = forms.CharField(max_length=8, initial="A")

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "roll_number",
            "department",
            "year",
            "section",
        )

    def clean_roll_number(self):
        roll_number = self.cleaned_data["roll_number"].strip()

        if StudentProfile.objects.filter(roll_number=roll_number).exists():
            raise forms.ValidationError(
                "A student with this roll number already exists."
            )

        return roll_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT

        if commit:
            with transaction.atomic():
                user.save()
                StudentProfile.objects.create(
                    user=user,
                    roll_number=self.cleaned_data["roll_number"],
                    department=self.cleaned_data["department"],
                    year=self.cleaned_data["year"],
                    section=self.cleaned_data["section"],
                )

        return user


class AddStudentForm(StudentRegistrationForm):
    pass


class AddTeacherForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.TEACHER

        if commit:
            user.save()

        return user


class MarkForm(forms.ModelForm):
    class Meta:
        model = Mark
        fields = [
            "student",
            "subject",
            "exam_name",
            "score",
            "max_score",
        ]

    def clean(self):
        cleaned = super().clean()
        score = cleaned.get("score")
        max_score = cleaned.get("max_score")

        if score is not None and max_score is not None:
            if max_score <= 0:
                self.add_error(
                    "max_score",
                    "Maximum score must be greater than zero.",
                )
            elif score < 0:
                self.add_error(
                    "score",
                    "Score cannot be negative.",
                )
            elif score > max_score:
                self.add_error(
                    "score",
                    "Score cannot exceed maximum score.",
                )

        return cleaned


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ["student", "subject", "date", "status"]


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "event_date", "subject"]


class EventRosterForm(forms.ModelForm):
    class Meta:
        model = EventRoster
        fields = ["event", "roll_number"]

    def clean_roll_number(self):
        return self.cleaned_data["roll_number"].strip()


class EventReportForm(forms.ModelForm):
    class Meta:
        model = EventReport
        fields = ["event", "description"]

    def clean_description(self):
        description = self.cleaned_data["description"].strip()

        if not description:
            raise forms.ValidationError(
                "Please enter your event report."
            )

        return description
