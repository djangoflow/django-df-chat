# Djangoflow Chat

Opinionated Django Chat

## Design

...

## Principles

* **Opinionated:** Create a set of strict guidelines to be followed by the users and developers. Well defined and consistent guidelines reduce errors and unwanted side-effects. The framework should be easy to understand, implement, and maintain.

* **Secure:** Follow the industry best practices for secure software development, communications, storage, as well as long-term maintenance. Always evaluate the risks and trade-offs in appropriate contexts.

* **Clean code:** Strictly follow the DRY (Don't Repeat Yourself) principle; write your code for other developers to understand; document and keep the documentation updated; automate testing your code, packaging, deployments, and other processes; discuss your ideas before implementing unless you are absolutely sure; be a good craftsman.

* **Open:** Offer source code and related artifacts under open source licenses. Build and manage a collaborative community where everyone is welcome.

* **Configurable:** Provide ways to change behavior, appearance, and offer extension points everywhere possible.

* **Reuse:** Do not reinvent the wheel. Use existing high-quality modules as much as possible.

## Endpoints

* `chat/`
# TODO: specify endpoints

## Data model

![Model graph](docs/models_graph.png)

The data models in `django-df-chat` represent the main entities in the chat system: Messages, Images, Rooms, Room Users, and User Chat.

### Message

The `Message` model represents a chat message. It stores the sender of the message (`room_user`), the content of the message (`body`), and other relevant information such as whether it's a reaction (`is_reaction`). It also tracks which users have seen or received the message. It can be related to other messages to form a thread (the `parent` attribute). Each message can also have multiple images associated with it, handled by a Many-to-Many relationship with the `Image` model.

### MessageImage

The `MessageImage` model handles images sent in chat messages. It associates an image file with a specific message and stores relevant metadata like the image's dimensions (`width` and `height`).

### Room

The `Room` model represents a chat room. It has fields to store the room's title, a description, an image, and whether the room is public (`is_public`). It also keeps track of the creator of the room (`creator`) and the users who are part of the room. It has a Many-to-Many relationship with the User model to track room admins and users who have muted the room.

### RoomUser

The `RoomUser` model tracks which users are in which rooms. It has a `room` and `user` ForeignKey to denote the room and the user, and an `is_active` field to denote if the user is currently active in the room. A RoomUser could be an actual user or a system.

### UserChat

The `UserChat` model stores attributes that should be visible across all rooms for a user. For example, it stores an `is_online` flag, which indicates whether a user is currently online.

These models, their relationships, and attributes allow for robust representation of a chat system, enabling complex features such as threaded conversations, image attachments, and room administration.


## Views and templates

...

## Development

### Running test application.

Here you can check admin and API endpoints.

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
./manage.py migrate
./manage.py runserver
