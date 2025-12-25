from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q


class ChatRoom(models.Model):
    """A model to represent a chat room"""

    ROOMTYPES = (
        ("public", "Public Room"),
        ("private", "Private Room"),
        ("direct", "Direct Message"),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    room_type = models.CharField(max_length=20, choices=ROOMTYPES, default="public")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_rooms"
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="chat_rooms", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["room_type", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name ({self.room_type})}"

    def get_online_participants(self):
        return self.participants.filter(is_online=True)

    def get_recent_messages(self, limit=50):
        return self.messages.all().order_by("-created_at")[:limit]


class Message(models.Model):
    """A model to represent a chat message"""

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="read_messages", blank=True
    )

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["room", "timestamp"]),
            models.Index(fields=["sender", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    def mark_as_read(self, user):
        if user not in self.read_by.all():
            self.read_by.add(user)
            if self.read_by.count() == self.room.participants.count():
                self.is_read = True
                self.save()


class DirectMessage(models.Model):
    """For one-on-one direct messages between users"""

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dm_user1"
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dm_user2"
    )
    room = models.OneToOneField(
        ChatRoom, on_delete=models.CASCADE, related_name="direct_message"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user1", "user2"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"DM: {self.user1.username} & {self.user2.username}"

    @classmethod
    def get_or_create_direct_room(cls, user1, user2):
        """Get or create a direct message room between two users"""
        # Ensure consistent ordering to avoid duplicate rooms
        user1_id, user2_id = sorted([user1.id, user2.id])

        if user1_id == user2_id:
            raise ValueError("Cannot create DM room with same user")

        # Get the actual user objects in correct order
        if user1.id == user1_id:
            u1, u2 = user1, user2
        else:
            u1, u2 = user2, user1

        dm, created = cls.objects.get_or_create(
            user1=u1,
            user2=u2,
            defaults={
                "room": ChatRoom.objects.create(
                    name=f"{u1.username}-{u2.username}",
                    room_type="direct",
                    created_by=u1,
                )
            },
        )

        # Ensure both users are participants
        dm.room.participants.add(u1, u2)
        return dm


class UserStatus(models.Model):
    """Track user's active connections"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="status"
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    current_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_users",
    )

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"
