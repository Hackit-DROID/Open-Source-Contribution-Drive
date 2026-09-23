from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import StudentRegistrationForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('books:list')
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to the SGGS Library! Your account has been created.")
            return redirect('books:list')
    else:
        form = StudentRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_view(request):
    from transactions.models import IssueRecord
    from ai.services import recommend_for_student

    issued = IssueRecord.objects.filter(student=request.user).select_related('book').order_by('-issue_date')
    active = issued.filter(status=IssueRecord.STATUS_ISSUED)
    history = issued.filter(status=IssueRecord.STATUS_RETURNED)

    recommendations = []
    if request.user.is_student():
        recommendations = recommend_for_student(request.user)

    return render(request, 'users/profile.html', {
        'active_issues': active,
        'history': history,
        'recommendations': recommendations,
    })
