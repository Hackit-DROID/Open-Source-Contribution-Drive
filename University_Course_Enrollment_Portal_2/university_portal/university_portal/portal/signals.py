from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from portal.models import Course, Takes
from portal.notifications import dispatcher


def _notifications_enabled():
    return getattr(settings, 'PORTAL_NOTIFICATIONS_ENABLED', False)


def _course_context(takes):
    context = {
        'course_id': takes.course_id,
        'sec_id': takes.sec_id,
        'semester': takes.semester,
        'year': takes.year,
    }
    course = Course.objects.filter(pk=takes.course_id).only('title', 'credits').first()
    if course is not None:
        context.update(course_title=course.title, credits=course.credits)
    return context


@receiver(pre_save, sender=Takes, dispatch_uid='portal_track_previous_grade')
def track_previous_grade(sender, instance, **kwargs):
    instance._previous_grade = None
    if instance.pk:
        instance._previous_grade = (
            sender.objects.filter(pk=instance.pk).values_list('grade', flat=True).first()
        )


@receiver(post_save, sender=Takes, dispatch_uid='portal_notify_takes_change')
def notify_takes_change(sender, instance, created, **kwargs):
    if not _notifications_enabled():
        return
    student = instance.ID
    if not student.email:
        return

    if created:
        event, context = 'enrollment_confirmed', _course_context(instance)
    else:
        previous = getattr(instance, '_previous_grade', None)
        if not instance.grade or previous == instance.grade:
            return
        event, context = 'grade_posted', _course_context(instance)
        context.update(grade=instance.grade, previous_grade=previous or '')

    transaction.on_commit(lambda: dispatcher.dispatch_to_student(student, event, context))
