from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.core.paginator import Paginator

from .models import ChatRoom, Message, DirectMessage, UserStatus
from .forms import MessageForm, ChatRoomForm, DirectMessageForm

User = get_user_model()


@login_required
def chat_home(request):
    """Main chat dashboard"""
    # get al public rooms and rooms user is part of
    public_rooms = (
        ChatRoom.objects.filter(Q(room_type="public") | Q(participants=request.user))
        .distinct()
        .order_by("-created_at")
    )

    # get direct message groups
    dm_groups = (
        ChatRoom.objects.filter(room_type="direct")
        .order_by("-messages__timestamp")
        .distinct()
    )

    # get online users
    online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)

    # get user's status
    user_status, created = UserStatus.objects.get_or_create(user=request.user)

    context = {
        "public_rooms": public_rooms,
        "dm_groups": dm_groups,
        "online_users": online_users,
        "user_status": user_status,
        "dm_form": DirectMessageForm(user=request.user),
        "room_form": ChatRoomForm(user=request.user),
    }
    return render(request, "chat_app/home.html", context)


@login_required
def chat_room(request, room_id):
    """Chat room view"""

    room = get_object_or_404(ChatRoom, id=room_id)

    # check if user can access this room
    if room.room_type == "private" and request.user not in room.participants.all():
        return HttpResponseForbidden("You are not allowed to access this room")

    # get messages for this room
    messages = room.messages.all().order_by("timestamp")[:100]

    # Get participants
    participants = room.participants.all()

    # Update user's current room status
    status, created = UserStatus.objects.get_or_create(user=request.user)
    status.current_room = room
    status.save()

    context = {
        "room": room,
        "messages": messages,
        "participants": participants,
        "message_form": MessageForm(),
    }
    return render(request, "chat_app/room.html", context)


@login_required
def create_room(request):
    """Create a new chat room"""
    if request.method == "POST":
        form = ChatRoomForm(request.POST, user=request.user)
        if form.is_valid():
            room = form.save()
            return redirect("chat-room", room_id=room.id)
    else:
        form = ChatRoomForm(user=request.user)

    return render(request, "chat_app/create_room.html", {"form": form})


@login_required
def start_direct_message(request):
    """Start or get direct message room"""
    if request.method == "POST":
        form = DirectMessageForm(request.POST, user=request.user)
        if form.is_valid():
            other_user = form.cleaned_data["username"]
            dm = DirectMessage.get_or_create_direct_room(request.user, other_user)
            return redirect("chat-room", room_id=dm.room.id)
    else:
        form = DirectMessageForm(user=request.user)

    return render(request, "chat_app/start_dm.html", {"form": form})


@login_required
def join_room(request, room_id):
    """Join a public room"""
    room = get_object_or_404(ChatRoom, id=room_id, room_type="public")
    room.participants.add(request.user)
    return redirect("chat-room", room_id=room.id)


@login_required
def leave_room(request, room_id):
    """Leave a room"""
    room = get_object_or_404(ChatRoom, id=room_id)
    room.participants.remove(request.user)
    return redirect("chat-home")


@login_required
def get_messages(request, room_id):
    """API endpoint to get messages for a room (for pagination)"""
    room = get_object_or_404(ChatRoom, id=room_id)

    if room.room_type == "private" and request.user not in room.participants.all():
        return JsonResponse({"error": "Access denied"}, status=403)

    # Get messages with pagination
    page = request.GET.get("page", 1)
    messages = room.messages.all().order_by("-timestamp")

    paginator = Paginator(messages, 50)
    page_obj = paginator.get_page(page)

    messages_data = [
        {
            "id": msg.id,
            "content": msg.content,
            "sender": msg.sender.username,
            "sender_id": msg.sender.id,
            "timestamp": msg.timestamp.isoformat(),
            "is_read": msg.is_read,
        }
        for msg in page_obj
    ]

    return JsonResponse(
        {
            "messages": messages_data[::-1],  # Reverse to get oldest first
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
        }
    )


@login_required
def mark_message_read(request, message_id):
    """Mark a message as read"""
    message = get_object_or_404(Message, id=message_id)

    # Check if user is in the room
    if request.user not in message.room.participants.all():
        return JsonResponse({"error": "Not in room"}, status=403)

    message.mark_as_read(request.user)
    return JsonResponse({"success": True})


@login_required
def get_online_users(request):
    """Get list of online users"""
    online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)

    users_data = [
        {
            "id": user.id,
            "username": user.username,
            "is_online": user.is_online,
        }
        for user in online_users
    ]

    return JsonResponse({"online_users": users_data})
