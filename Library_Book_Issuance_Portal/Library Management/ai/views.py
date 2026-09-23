from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services import chat_answer


@login_required
def chat_page(request):
    return render(request, 'ai/chat.html')


@login_required
@require_POST
def chat_ask(request):
    question = request.POST.get('question', '').strip()
    if not question:
        return JsonResponse({'error': 'Question is required.'}, status=400)
    answer = chat_answer(question, student=request.user)
    return JsonResponse({'question': question, 'answer': answer})
