from django.shortcuts import render
from django.http import JsonResponse
from .models import ChatMessage
from .utils import ConstitutionChat
from django.views.decorators.csrf import csrf_exempt
import json

chat_system = ConstitutionChat()

def chat_home(request):
    messages = ChatMessage.objects.all().order_by('-timestamp')[:5]
    return render(request, 'constitution_chat/chat.html', {'messages': messages})

@csrf_exempt
def ask_question(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('question', '')
        
        # Get answer from the QA system
        answer = chat_system.get_answer(question)
        
        # Save to database
        ChatMessage.objects.create(question=question, answer=answer)
        
        return JsonResponse({'answer': answer})
    return JsonResponse({'error': 'Invalid request method'})