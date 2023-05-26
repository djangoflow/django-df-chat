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

> **_NOTE:_**  Generated content, as with human generated content, may contain errors or oversights. Please review before merging!

The [Django REST Framework (DRF)](https://www.django-rest-framework.org/) is used to build the API for `django-df-chat`. DRF routers are used to automatically create routes for the API views. There are two top-level routes: `rooms` and `images`, and two nested routes under `rooms`: `users` and `messages`.

Below are the endpoints provided by `django-df-chat`:

### Rooms

- `GET /api/v1/chat/rooms/` - List all chat rooms that the authenticated user can access.
- `POST /api/v1/chat/rooms/` - Create a new chat room.
- `GET /api/v1/chat/rooms/<room_id>/` - Retrieve details of a specific chat room.
- `PUT /api/v1/chat/rooms/<room_id>/` - Update details of a specific chat room.
- `DELETE /api/v1/chat/rooms/<room_id>/` - Delete a specific chat room.
- `POST /api/v1/chat/rooms/<room_id>/mute/` - Mute a specific chat room for the authenticated user.
- `POST /api/v1/chat/rooms/<room_id>/unmute/` - Unmute a specific chat room for the authenticated user.

### Users in a Room

- `GET /api/v1/chat/rooms/<room_id>/users/` - List all users in a specific room.
- `POST /api/v1/chat/rooms/<room_id>/users/` - Add a user to a specific room.
- `GET /api/v1/chat/rooms/<room_id>/users/<user_id>/` - Retrieve details of a specific user in a room.
- `PUT /api/v1/chat/rooms/<room_id>/users/<user_id>/` - Update details of a specific user in a room.
- `DELETE /api/v1/chat/rooms/<room_id>/users/<user_id>/` - Remove a specific user from a room.
- `GET /api/v1/chat/rooms/<room_id>/users/names/` - Get the names of all users in a specific room.

### Messages in a Room

- `GET /api/v1/chat/rooms/<room_id>/messages/` - List all messages in a specific room.
- `POST /api/v1/chat/rooms/<room_id>/messages/` - Send a new message in a specific room.
- `GET /api/v1/chat/rooms/<room_id>/messages/<message_id>/` - Retrieve details of a specific message in a room.
- `PUT /api/v1/chat/rooms/<room_id>/messages/<message_id>/` - Update a specific message in a room.
- `DELETE /api/v1/chat/rooms/<room_id>/messages/<message_id>/` - Delete a specific message from a room.
- `POST /api/v1/chat/rooms/<room_id>/messages/seen/` - Mark a message as seen by the authenticated user.

### Images

- `GET /api/v1/chat/images/` - List all images that the authenticated user can access.
- `POST /api/v1/chat/images/` - Upload a new image.
- `GET /api/v1/chat/images/<image_id>/` - Retrieve details of a specific image.
- `PUT /api/v1/chat/images/<image_id>/` - Update details of a specific image.
- `DELETE /api/v1/chat/images/<image_id>/` - Delete a specific image.

Note that all these endpoints require the client to be authenticated, and permissions are checked on each request to ensure the client is allowed to perform the requested action.

## Websocket Endpoint

> **_NOTE:_**  Generated content, as with human generated content, may contain errors or oversights. Please review before merging!

`django-df-chat` also provides a websocket endpoint for real-time chat functionality. This uses [Django Channels](https://channels.readthedocs.io/en/stable/) and the [DjangoChannelsRestFramework](https://djangochannelsrestframework.readthedocs.io/en/latest/) package to provide a consumer that listens for chat events.

### Rooms Consumer

A single websocket consumer is defined for listening to chat events: `RoomsConsumer`.

- Websocket connect to `/api/v1/chat/ws/` - Connects the client to the server via a websocket. If the user is not authenticated, the connection is refused. On connection, the user is automatically subscribed to all the rooms they are a part of.

- Websocket disconnect - The user disconnects from the websocket. On disconnection, the user is automatically unsubscribed from all rooms they are listening to. The `user_chat` model is updated to reflect that the user is offline.

The `RoomsConsumer` listens for changes to `RoomUser` and `Message` models, and sends updates to the client via the websocket when these models change. These updates include both changes made by the client themselves and changes made by other users. Therefore, clients using this websocket endpoint will receive real-time updates about all chat events they are allowed to know about.

- `RoomUser` updates: When a `RoomUser` model is changed (which represents a user joining or leaving a room), the websocket client will receive an update with the new state of the `RoomUser`.

- `Message` updates: When a `Message` model is created or updated, the websocket client will receive an update with the new state of the `Message`.

Note that the server will not send updates for empty messages and reactions, nor for `Message` instances marked as "reactions." This means that the websocket client will only receive updates for substantial chat events.

Please note that for proper functioning of these real-time features, it's crucial that the WebSocket client correctly implements handling of incoming updates and adjust their state accordingly.

## Data model

![Model graph](docs/models_graph.png)

> **_NOTE:_**  Generated content, as with human generated content, may contain errors or oversights. Please review before merging!

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

> **_NOTE:_**  Generated content, as with human generated content, may contain errors or oversights. Please review before merging!

There's a Django view for each URL path, and each view is associated with a corresponding HTML template.

### Index View

The index view (at the `/` URL path) corresponds to the `index.html` template. This view and template allow users to choose a chat room to enter.

The `index.html` template presents a simple interface for entering a room name, and then navigates to the corresponding room URL when the "Enter" button is clicked. It uses JavaScript to enable this functionality and to respond to the Enter key being pressed.

### Room View

The room view (at the `/<str:room_name>/` URL path) corresponds to the `room.html` template. This view and template allow users to chat in the chosen room.

The `room.html` template provides a chat interface for a specific room. It includes a `textarea` for displaying chat messages, an `input` field for writing a new message, and two buttons for sending the message or a reaction.

The template also includes JavaScript code that does the following:

- Extracts the room name from the rendered Django template, and the auth token from the URL.
- Establishes a WebSocket connection for real-time chat functionality.
- Adds messages to the chat log when they're received over the WebSocket.
- Sends new messages and reactions to the server when the "Send" or "Like" button is clicked. These are sent via HTTP POST requests to a REST API endpoint, not via the WebSocket. The messages or reactions are sent as JSON payloads, and the server's responses are added to the chat log.

### How to Use These Views and Templates

To use these views and templates in your Django project, simply map the views to their respective URL paths in your project's URL configuration, and place the templates in your project's templates directory under the appropriate app subdirectory.

Remember to ensure that the WebSocket and REST API endpoints referenced in the `room.html` template are correctly set up in your project, and that you have CSRF protection and authentication set up for the POST requests.

## Development

### Running test application.

Here you can check admin and API endpoints.

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
./manage.py migrate
./manage.py runserver
