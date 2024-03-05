# django-df-chat


## Development

Installing dev requirements:

```
pip install -e .[test]
```

Installing pre-commit hook:

```
pre-commit install
```

Running tests:

```
pytest
```


## New Design

### Model Data


ChatRoom

- title = CharField()
- users = ManyToManyField(through="ChatMember")
- chat_type = Enum: 'private', 'group',

ChatMember

- is_owner = BooleanField(default=False)
- is_admin = BooleanField(default=False)
- user = ForeignKey(ChatUser)
- chat_room = ForeignKey(ChatRoom)

MemberChannel (service table)

- last_alive_at = DateTimeField()
- channel_name = CharField()
- user = ForeignKey(ChatUser)


ChatMessage

- created_by = ForeignKey(ChatUser)
- chat_room = ForeignKey(ChatRoom)
- message = TextField(settings.CHAT_USER_MODEL)


### API:

[GET]
/api/v1/chat/rooms/

[POST]
/api/v1/chat/rooms/

[GET]
/api/v1/chat/rooms/{id}/

[PUT]
/api/v1/chat/rooms/{id}/

[PATCH]
/api/v1/chat/rooms/{id}/

[DELETE]
/api/v1/chat/rooms/{id}/

[POST]
/api/v1/chat/rooms/{id}/member/

[GET]
/api/v1/chat/rooms/{room_id}/messages/

[POST]
/api/v1/chat/rooms/{room_id}/messages/

[GET]
/api/v1/chat/rooms/{room_id}/messages/{id}/

[PUT]
/api/v1/chat/rooms/{room_id}/messages/{id}/

[PATCH]
/api/v1/chat/rooms/{room_id}/messages/{id}/

[DELETE]
/api/v1/chat/rooms/{room_id}/messages/{id}/


### Use cases:

- Create chat room with specific type, and add user. Channel layer should be created if user are online and all online users should to receive messages
- Private chat room (chat between 2 members). Nobody can add new members.
- Group chat (chat between multiple users). Users could be added through API endpoint call
- moderation part is missed at the moment


### Flow:
- User connected to WS
- Channel layer stored to DB to use it in a future to dynamically subscribe user with a new chatRooms
- on user disconnected channel layer should be removed from DB
