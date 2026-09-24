from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from student.models import Student
from library.models import Library

class Account(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    library = models.ForeignKey(Library, on_delete=models.SET_NULL, null=True, blank=True)
    fees_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    due = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    branch = models.CharField(max_length=50, default='Unknown')  # optional if you want branch here

    def __str__(self):
        return f"{self.student.name} Account"


class ImmutableAuditLogError(Exception):
    pass


class AuditLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ImmutableAuditLogError("Audit log entries cannot be updated.")

    def delete(self):
        raise ImmutableAuditLogError("Audit log entries cannot be deleted.")


class AuditLog(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    detail = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = AuditLogQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at', '-id']

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableAuditLogError("Audit log entries cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableAuditLogError("Audit log entries cannot be deleted.")

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.action} [{self.status}]"
