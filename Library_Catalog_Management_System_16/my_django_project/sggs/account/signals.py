from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from account.notifications import dispatcher

User = get_user_model()


@receiver(pre_save, sender=User, dispatch_uid='account_track_active_status')
def track_active_status(sender, instance, **kwargs):
    instance._previous_is_active = None
    if instance.pk:
        instance._previous_is_active = (
            sender.objects.filter(pk=instance.pk).values_list('is_active', flat=True).first()
        )


@receiver(post_save, sender=User, dispatch_uid='account_notify_status_change')
def notify_status_change(sender, instance, created, **kwargs):
    if created or not getattr(settings, 'ACCOUNT_STATUS_NOTIFICATIONS', False):
        return
    previous = getattr(instance, '_previous_is_active', None)
    if previous is None or previous == instance.is_active or not instance.email:
        return
    status = 'active' if instance.is_active else 'deactivated'
    dispatcher.dispatch_to_user(instance, 'account_status', {'status': status})
