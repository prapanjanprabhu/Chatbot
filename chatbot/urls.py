from django.urls import path
from chatbot import views

urlpatterns = [
    path('login/', views.auth_view, name='auth_view'),
    path('chat/', views.chat_view, name='chat_view'),
    path('logout/', views.logout_view, name='logout_view'),
        path('history/', views.chat_history, name='chat_history'),  # 👈 Add this
    path('chat/<uuid:conversation_id>/', views.view_conversation, name='view_conversation'),
    path("new/", views.new_chat_view, name="new_chat")

]
