from django.db import models
from borrow.models import BorrowRecord

class Notification(models.Model):
    borrow_record = models.ForeignKey(BorrowRecord, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.borrow_record.borrower.name}: {self.message[:30]}"
