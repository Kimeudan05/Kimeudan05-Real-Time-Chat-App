from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_home, name="chat-home"),
    path("room/<int:room_id>/", views.chat_room, name="chat-room"),
    path("create/", views.create_room, name="create-room"),
    path("start-dm/", views.start_direct_message, name="start-dm"),
    path("join/<int:room_id>/", views.join_room, name="join-room"),
    path("leave/<int:room_id>/", views.leave_room, name="leave-room"),
    path("api/messages/<int:room_id>/", views.get_messages, name="get-messages"),
    path(
        "api/messages/<int:message_id>/read/", views.mark_message_read, name="mark-read"
    ),
    path("api/online-users/", views.get_online_users, name="online-users"),
]
