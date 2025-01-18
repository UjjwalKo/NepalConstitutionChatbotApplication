from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('ask-question/', views.ask_question, name='ask_question'),
]