from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"
        HOD = "HOD", "HOD"
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    roll_number = models.CharField(max_length=24, unique=True)
    department = models.CharField(max_length=80, default="CSE")
    year = models.PositiveSmallIntegerField(default=4)
    section = models.CharField(max_length=8, default="A")
    def __str__(self):
        return f"{self.roll_number} - {self.user.get_full_name() or self.user.username}"

class Subject(models.Model):
    code = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=80, default="CSE")
    def __str__(self):
        return f"{self.code} - {self.name}"

class Mark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="marks")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_name = models.CharField(max_length=60, default="Internal 1")
    score = models.DecimalField(max_digits=6, decimal_places=2)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=30)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "subject", "exam_name"], name="unique_student_subject_exam")]
    def __str__(self):
        return f"{self.student} / {self.subject} / {self.exam_name}"

class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance_records")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.PRESENT)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    source = models.CharField(max_length=12, default="CLASS", choices=[("CLASS","Class"),("EVENT","Event")])
    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "subject", "date", "source"], name="unique_attendance_per_day")]
        ordering = ["-date"]
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date} - {self.status}"

class Event(models.Model):
    title = models.CharField(max_length=140)
    event_date = models.DateField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, help_text="Subject to which event attendance is credited")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.title

class EventRoster(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="roster")
    roll_number = models.CharField(max_length=24)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "roll_number"], name="unique_event_roll")]
    def __str__(self):
        return f"{self.event}: {self.roll_number}"

class EventReport(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="event_reports")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    description = models.TextField(max_length=1200)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "event"], name="unique_student_event_report")]
        ordering = ["-submitted_at"]
