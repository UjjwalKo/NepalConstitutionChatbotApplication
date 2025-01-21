from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import ChatHistory, UserProfile, PasswordResetToken
from .chatbot import ask_question
from .forms import RegistrationForm, PasswordResetRequestForm, PasswordResetForm
import json
import uuid

@login_required
@require_http_methods(["GET", "POST"])
def chat_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question')
            answer = ask_question(question)
            
            # Save to chat history
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
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('chat')
    else:
        form = RegistrationForm()
    return render(request, 'constitution_chat/register.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = PasswordResetToken.objects.create(user=user)
                send_password_reset_email(user, token)
                return render(request, 'constitution_chat/password_reset_sent.html')
            except User.DoesNotExist:
                form.add_error('email', 'No user found with this email address.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'constitution_chat/forgot_password.html', {'form': form})

def reset_password(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token)
    if not reset_token.is_valid():
        return render(request, 'constitution_chat/password_reset_invalid.html')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            reset_token.used = True
            reset_token.save()
            return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, 'constitution_chat/reset_password.html', {'form': form})

def send_password_reset_email(user, token):
    subject = 'Password Reset for Nepal Constitution Chatbot'
    message = f'Click the link to reset your password: {settings.SITE_URL}/reset-password/{token.token}/'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])