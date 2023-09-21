# django-df-chat


## New Design

### Model Data

ChatUser

- One-to-one to User (or other model from settings, like settings.DF_CHAT_USER_MODEL)
- description = str
- avatar = ImageField


ChatRoom

- name = str
- description = str
- avatar = ImageField
- type = Enum: 'private_messages', 'group', 'channel'
- is_public = BooleanField(default=False)  # does appear in search results; can be joined by anyone

RoomUser

- room = ForeignKey(ChatRoom)
- user = ForeignKey(ChatUser)
- muted = BooleanField(default=False)
- created_by = ForeignKey(ChatUser)
- last_seen_at = DateTimeField()  # To show how many messages are unread

Somehow we need to manage perms per room:
- can_add_users
- can_remove_users
- can_create_messages
- can_delete_messages
- can_delete_own_messages
- can_edit_messages
- can_edit_own_messages
- can_edit_room
- can_delete_room


It could be JSONField with list of permissions. Or separate RoomUserPermission model (room_user fk + permission Enum).

ChatMessage

- room = ForeignKey(ChatRoom)
- user = ForeignKey(ChatUser)
- text = TextField()

ChatMessageMedia

- message = ForeignKey(ChatMessage)
- chat_media = ForeignKey(ChatMedia)
- sequence = IntegerField()


ChatMedia

- media = FileField


ChatMessageReaction

- message = ForeignKey(ChatMessage)
- user = ForeignKey(ChatUser)
- reaction = CharField(max_length=255) -- Constrained in settings: only `like/dislike` or `emoji` or custom text.


### API:

- chat_room:
  - list
  - create
  - retrieve
- room_user:
  - list
  - create
  - retrieve
  - update
  - delete
- chat_message:
  - list
  - create
  - retrieve
  - update
  - delete
- chat_media:
  - create
  - retrieve
- chat_message_reactions:
  - list (for specific message only or for myself)
  - create
  - retrieve
  - delete

### Use cases:

- Private messages: room with 2 users. Nobody can add other users to the room. Both can delete the room.
- Group: room where everybody can create a message. Everybody can add other users to the room. Only is_owner can delete the room.
- Channel: room where only `admin` can create a message. Everybody can add other users to the room. Only is_owner can delete the room.


### Flows:

- Send picture to a room:
  - Create chat_media, retrieve media_id
  - Create chat_message with media_id
- Create a chat on 3 people:
  - Create new room type=group
  - Create room_user for each user
  - Create chat_message with text="User X created a chat" and room_id
- Create a news channel:
  - Create new room type=channel
  - Add User to the room with can_add_users=True, can_write_messages=True (and other perms). So user can post news to the channel.
  - Add create other room_users without perms. So they can read the channel.
