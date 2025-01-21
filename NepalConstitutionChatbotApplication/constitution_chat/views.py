from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import ChatHistory, UserProfile
from .chatbot import ask_question
from .forms import RegistrationForm
import json

@login_required
@require_http_methods(["GET", "POST"])
def chat_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question')
            answer = ask_question(question)
            ChatHistory.objects.create(user=request.user, question=question, answer=answer)
            return JsonResponse({'answer': answer})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    chat_history = ChatHistory.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'constitution_chat/chat.html', {'chat_history': chat_history})

@login_required
def delete_history(request, history_id):
    history = get_object_or_404(ChatHistory, id=history_id, user=request.user)
    history.delete()
    return redirect('chat')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                UserProfile.objects.create(user=user)
                login(request, user)
                return redirect('chat')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                return redirect('register')
        else:
            messages.error(request, "Form validation failed. Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, 'constitution_chat/register.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            return redirect('reset_password', email=email)
        except User.DoesNotExist:
            return render(request, 'constitution_chat/forgot_password.html', {
                'error': 'No user found with this email address.',
            })
    return render(request, 'constitution_chat/forgot_password.html')

def reset_password(request, email):
    user = get_object_or_404(User, email=email)
    if request.method == 'POST':
        password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            return render(request, 'constitution_chat/reset_password.html', {
                'error': 'Passwords do not match.',
                'email': email,})
        user.set_password(password)
        user.save()
        return redirect('login')  
    return render(request, 'constitution_chat/reset_password.html', {'email': email})