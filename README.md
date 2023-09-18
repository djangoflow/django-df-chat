=======================================
Djangoflow Chat
=======================================

Opinionated Django Chat





------
Design
------

...

Principles
----------

* **Opinionated:** Create a set of strict guidelines to be followed by the users
  and developers. Well defined and consistent guidelines reduces errors and
  unwanted side-effects. Framework should be easy to understand, implement and maintain.

* **Secure:** Follow the industry best practices secure software development; communications;
  storage as well as long term maintenance. Always evaluate the risk and trade-offs in
  appropriate contexts.

* **Clean code:** Strictly follow DRY principle; write your code for other developers
  to understand; document and keep documentation updated; automate testing your code,
  packaging, deployments and other processes; discuss your ideas before implementing unless
  you are absolutely sure; be a good craftsmen.

* **Open:** Offer source code and related artifacts under open source licenses. Build
  and manage a collaborative community where everyone is welcome.

* **Configurable:** Provide ways to change behavior, appearance and offer extension points
  everywhere possible.

* **Reuse:** Do not reinvent the wheel. Use existing high-quality modules as much as possible.

Endpoints
---------

* `chat/`
# TODO: specify endpoints

Data model
----------

...

Views and templates
-------------------

...


## Development


### Running test application.

Here you can check admin and API endpoints.

```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
./manage.py migrate
./manage.py runserver
```


To run a chat example you need:

- Create two superusers via `./manage.py createsuperuser`
- Open http://127.0.0.1:8000/api/auth/token/ and obtain a `token` for each user with username and password
- Create chat room via admin http://127.0.0.1:8000/admin/df_chat/room/ and obtain `room_id` from URL
- Open http://localhost:8000/chat/<room_id>/?token=<token> in two different browsers
- Start chatting. You should see messages appear in both browsers


### Running tests

```
pytest
```

### Contribution

Make sure you've run the following commands to setup the environment for development:
  ```bash
  # Setup the python virtual environment
  python3 -m venv venv
  . venv/bin/activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt

  # Run pre-commit install to install pre-commit into your git hooks.
  # It will run on every commit and fail to commit if the code is not as per standards defined in .pre-commit-config.yaml
  pre-commit install
  ```


### Deploying new version

Change version in `setup.cfg` and push new tag to main branch.

```
git tag 0.0.x
git push --tags
```

## Other modules and links out there


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

...

Sponsors
========

[Apexive OSS](https://apexive.com)
