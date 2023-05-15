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


### Deploying new version

Change version in `setup.cfg` and push new tag to main branch.

```
git tag 0.0.x
git push --tags
```

## Other modules and links out there


...

Sponsors
========

[Apexive OSS](https://apexive.com)
