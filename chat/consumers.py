import ujson
from pyexpat.errors import messages
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import User
from django.forms import model_to_dict

from chat.models import Message


class CustomAsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
    @classmethod
    async def decode_json(cls, text_data):
        return ujson.loads(text_data)

    @classmethod
    async def encode_json(cls, content):
        return ujson.dumps(content)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    group_name = 'chat'

    async def save_msg(self, content) -> Message:
        return await Message.objects.acreate(
            message=content.get("message"),
            file_id=content.get('file'),
            author=self.user
        )

    async def check_user(self) -> bool:
        if self.user.is_anonymous:
            await self.send_json({'msg': 'Login is required!'})
            await self.disconnect(0)
            await self.close()
            return False
        return True

    async def notification(self, is_connceted: bool = True) -> None:
        message = f'{self.user.username} connected to this chat' if is_connceted else f'{self.user.username} left this chat'

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "notification.message",
                "message": message,
                "from_user": model_to_dict(self.user, ['id', 'username']),
            }
        )

    async def connect(self):
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        if not await self.check_user():
            return
        await self.notification()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.notification(False)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        keys = {'message', 'file'}
        if len(set(content) & keys) < 1:
            await self.send_json({'message': f'Shu kalitlardan birini yuborish shart {keys}'})
            return
        msg = await self.save_msg(content)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message":  model_to_dict(msg, ['id', 'message', 'file']),
                "from_user": model_to_dict(self.user, ['id', 'username']),
            }
        )

    async def notification_message(self, event):
        response = {
            "message": event.get('message'),
            "file": event.get('file'),
            "from_user": event["from_user"]['username']
        }
        if self.user.id != event["from_user"]['id']:
            await self.send_json(response)
        else:
            if isinstance(event['message'], dict):
                await self.send_json(event['message'] | {"status": "xabar yuborildi"})

    async def chat_message(self, event):
        response = {
            "message": event["message"]["message"],
            "file": event["message"]["file"],
            "from_user": event["from_user"]['username']
        }
        if self.user.id != event["from_user"]['id']:
            await self.send_json(response)
        else:
            if isinstance(event['message'], dict):
                await self.send_json(event['message'] | {"status": "xabar yuborildi"})