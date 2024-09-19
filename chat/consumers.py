import json
from pyexpat.errors import messages
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import User
from django.forms import model_to_dict

from chat.models import Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    group_name = 'chat'

    async def save_msg(self, msg: str) -> Message:
        return await Message.objects.acreate(message=msg, author=self.user)

    async def check_user(self) -> None:
        if self.user.is_anonymous:
            await self.send_json({'msg': 'Login is required!'})
            await self.disconnect(0)
            await self.close()

    async def notification(self, is_connceted: bool = True) -> None:
        message = f'{self.user.username} connected to this chat' if is_connceted else f'{self.user.username} left this chat'

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": message,
                "from_user": model_to_dict(self.user, ['id', 'username']),
                "msg_type": "system"
            }
        )

    async def connect(self):
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.check_user()
        await self.notification()

    async def disconnect(self, close_code):
        await self.notification(False)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        message = content["message"]
        msg_type = content["msg_type"]
        msg = await self.save_msg(message)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": msg.message,
                "from_user": model_to_dict(self.user.username, ['id', 'username']),
                "msg_type": msg_type if msg_type else 'message'
            }
        )

    async def chat_message(self, event):
        response = {
            "message": event["message"],
            "from_user": event["from_user"]['username']
        }
        if self.user.id != event["from_user"]['id']:
            await self.send_json(response)
        else:
            if event["msg_type"] != 'system':
                await self.send_json(event['message'] | {"status": "xabar yuborildi"})