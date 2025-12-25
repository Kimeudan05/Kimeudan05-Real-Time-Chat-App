### Run the app

1. On linux start the redis

`sudo service redis-server start`

2. satrt the websocoket

`daphne chat.asgi:application -p 8000 -b 0.0.0.0`

3. start the main app

`python manage.py runserver`