# chat_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from .models import ChatRoom, Message, DirectMessage, UserStatus

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Update user status
        if self.user.is_authenticated:
            await self.update_user_status(True)

            # Notify others that user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_status",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_online": True,
                },
            )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Update user status
        if self.user.is_authenticated:
            await self.update_user_status(False)

            # Notify others that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_status",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_online": False,
                },
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "message")

        if message_type == "message":
            message = text_data_json["message"]
            sender_id = text_data_json["sender_id"]

            # Save message to database
            message_obj = await self.save_message(message, sender_id)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_id": sender_id,
                    "sender_username": self.user.username,
                    "timestamp": message_obj.timestamp.isoformat(),
                    "message_id": message_obj.id,
                },
            )

        elif message_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_typing": text_data_json["is_typing"],
                },
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "sender_username": event["sender_username"],
                    "timestamp": event["timestamp"],
                    "message_id": event["message_id"],
                }
            )
        )

    async def typing_indicator(self, event):
        # Send typing indicator to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "is_typing": event["is_typing"],
                }
            )
        )

    async def user_status(self, event):
        # Send user status update to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_status",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "is_online": event["is_online"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, content, sender_id):
        room = ChatRoom.objects.get(id=self.room_id)
        sender = User.objects.get(id=sender_id)
        message = Message.objects.create(room=room, sender=sender, content=content)
        return message

    @database_sync_to_async
    def update_user_status(self, is_online):
        status, created = UserStatus.objects.get_or_create(user=self.user)
        status.is_online = is_online
        status.save()

        # Update user model status
        self.user.is_online = is_online
        self.user.save()


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    """Consumer for tracking online users globally"""

    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            # Add user to online group
            await self.channel_layer.group_add("online_users", self.channel_name)

            await self.accept()

            # Update user status
            await self.update_user_status(True)

            # Broadcast that user is online
            await self.channel_layer.group_send(
                "online_users",
                {
                    "type": "user_online_status",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_online": True,
                },
            )

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Remove from online group
            await self.channel_layer.group_discard("online_users", self.channel_name)

            # Update user status
            await self.update_user_status(False)

            # Broadcast that user is offline
            await self.channel_layer.group_send(
                "online_users",
                {
                    "type": "user_online_status",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_online": False,
                },
            )

    async def user_online_status(self, event):
        # Send status update to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_online_status",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "is_online": event["is_online"],
                }
            )
        )

    @database_sync_to_async
    def update_user_status(self, is_online):
        status, created = UserStatus.objects.get_or_create(user=self.user)
        status.is_online = is_online
        status.save()

        self.user.is_online = is_online
        self.user.save()
