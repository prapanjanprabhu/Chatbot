import uuid
import re
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .models import LoginUser, Message

# Remove emojis and unsupported characters
def remove_unsupported_chars(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)


# -------------------------------
# Authentication View (Login/Register)
# -------------------------------
def auth_view(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if form_type == "register":
            if LoginUser.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
                return redirect('auth_view')

            user = LoginUser(email=email)
            user.set_password(password)
            user.save()
            request.session['user_id'] = user.id
            return redirect('chat_view')

        elif form_type == "login":
            try:
                user = LoginUser.objects.get(email=email)
                if user.check_password(password):
                    request.session['user_id'] = user.id
                    return redirect('chat_view')
                else:
                    messages.error(request, "Incorrect password.")
            except LoginUser.DoesNotExist:
                messages.error(request, "User not found.")

            return redirect('auth_view')

    return render(request, "auth.html")


# -------------------------------
# Logout
# -------------------------------
def logout_view(request):
    request.session.flush()
    return redirect('chat_view')


# -------------------------------
# Chat View (Handles New + Existing Conversations)
# -------------------------------
import uuid
import re
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from .models import LoginUser, Message
from django.utils.timezone import now


import uuid
import re
import requests
from django.shortcuts import render, redirect
from django.conf import settings
from .models import LoginUser, Message


def chat_view(request):
    user = None
    user_id = request.session.get("user_id")

    if user_id:
        try:
            user = LoginUser.objects.get(id=user_id)
        except LoginUser.DoesNotExist:
            user = None  # fallback to anonymous

    if not request.session.get("conversation_id"):
        request.session["conversation_id"] = str(uuid.uuid4())

    conversation_id = request.session.get("conversation_id")

    if request.method == "POST":
        user_input = request.POST.get("message", "").strip()
        if user_input:
            cleaned_input = remove_unsupported_chars(user_input)

            if user:  # Save only if user is logged in
                Message.objects.create(
                    content=cleaned_input,
                    sender="user",
                    user=user,
                    conversation_id=conversation_id,
                    timestamp=now()
                )

            # Get reply from API
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta-llama/llama-4-maverick",
                "messages": [{"role": "user", "content": cleaned_input}]
            }

            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    bot_reply = response.json()['choices'][0]['message']['content']
                else:
                    bot_reply = f"❌ Error: {response.status_code}"
            except Exception as e:
                bot_reply = f"❌ Exception: {str(e)}"

            cleaned_reply = remove_unsupported_chars(bot_reply)

            if user:  # Save only if user is logged in
                Message.objects.create(
                    content=cleaned_reply,
                    sender="bot",
                    user=user,
                    conversation_id=conversation_id,
                    timestamp=now()
                )

        return redirect('chat_view')

    # Show messages only if logged in
    messages = Message.objects.filter(user=user, conversation_id=conversation_id).order_by("timestamp") if user else []

    username = user.email.split('@')[0] if user and user.email else ''
    summaries = get_conversation_summaries(user.id) if user else []

    return render(request, "chat.html", {
        "messages": messages,
        "username": username,
        "user_email": user.email if user else '',
        "summaries": summaries,
        "user": user  # used in template logic
    })





# -------------------------------
# View Specific Conversation
# -------------------------------
def view_conversation(request, conversation_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("auth_view")

    user = LoginUser.objects.get(id=user_id)
    username = user.email.split('@')[0]

    request.session["conversation_id"] = str(conversation_id)

    conversation_messages = Message.objects.filter(
        user_id=user_id,
        conversation_id=conversation_id
    ).order_by("timestamp")

    summaries = get_conversation_summaries(user_id)

    return render(request, "chat.html", {
        "messages": conversation_messages,
        "summaries": summaries,
        "username": username,
        "user_email": user.email,
    })




from django.db.models import Min, Max

def get_conversation_summaries(user_id):
    return Message.objects.filter(user_id=user_id)\
        .values('conversation_id')\
        .annotate(
            first_message=Min('timestamp'),
            last_message=Max('timestamp'),
            content=Min('content')  # still gives a message as summary
        )\
        .order_by('-last_message')  # sort by most recent conversation





def chat_history(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("auth_view")

    user = LoginUser.objects.get(id=user_id)
    username = user.email.split('@')[0]

    all_messages = Message.objects.filter(user_id=user_id).order_by("-conversation_id", "timestamp")

    from collections import defaultdict
    conversations = defaultdict(list)
    for msg in all_messages:
        conversations[msg.conversation_id].append(msg)

    sorted_conversations = sorted(conversations.items(), key=lambda x: x[0], reverse=True)

    summaries = get_conversation_summaries(user_id)

    return render(request, "chat.html", {
        "conversations": sorted_conversations,
        "summaries": summaries,
        "username": username,
        "user_email": user.email,
    })



def new_chat_view(request):
    # Clear current conversation and start new
    request.session["conversation_id"] = str(uuid.uuid4())
    return redirect("chat_view")
