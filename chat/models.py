from django.db.models import Model, DateTimeField, TextField, ForeignKey, CASCADE, FileField, OneToOneField, SET_NULL
from django.db.models.functions import Now


class TimeBasedModel(Model):
    updated_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        abstract = True


class Attachment(TimeBasedModel):
    file = FileField(upload_to='attachments/%Y/%m/%d/')


class Message(TimeBasedModel):
    message = TextField(null=True, blank=True)
    file = OneToOneField('chat.Attachment', SET_NULL, null=True, blank=True)
    author = ForeignKey('auth.User', CASCADE, related_name='messages')
