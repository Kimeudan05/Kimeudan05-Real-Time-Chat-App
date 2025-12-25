import os
import django
from django.core.asgi import get_asgi_application

# 1. Set settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat.settings")

# 2. Initialize Django & get the HTTP ASGI app
# This MUST happen before importing routing/consumers
django_asgi_app = get_asgi_application()

# 3. Now import Channels components
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# 4. Import your app-specific routing AFTER django.setup() / get_asgi_application()
import chat_app.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(chat_app.routing.websocket_urlpatterns)
        ),
    }
)
