# MC Server Web

Control Minecraft servers from a web UI and allow others to as well!

This project is mainly intended for friend groups with one person doing DIY server hosting.

## Notes and Limitations

### Scope

This project is not intended for scale. There are _many_ design decisions that were made for the sake of simplicity over scalability or reliability. The intended scope for this software is to be run on a single machine, with the target audience being a group of friends to the host.

### On Accepting PRs

This was built for personal use. PRs likely will not be accepted, and any support is very unlikely to be provided. Bug reports are still very much accepted, though, and you're of course free to do anything with this software so long as you follow the license located in the `LICENSE` file of this repository.

### Thanks

Thanks to <https://blog.miguelgrinberg.com/post/oauth-authentication-with-flask-in-2023> for the understanding and implementation of OAuth2. The code for the tutorial is found [here](https://github.com/miguelgrinberg/flask-oauth-example). 

## Setup

1. `python -m pip install -r requirements.txt` to install requirements. This is tested with Python 3.12, though earlier versions will probably work.
2. Add the environment variables as mentioned in `config.py`.
3. `python app.py` to generate `user_ids.txt`
4. Fill in `user_ids.txt`, with user IDs from Discord and friendly names that you'll use in other places. Any user not here will NOT be able to use MC Server Web. Note that by using a ~ instead of = as a separator, that user is an admin (see below).
5. Optional: For each server, add a `mc_server_web.txt` file, filled with comma-separated friendly names. For example: `Me,MyFriend`. Any users not in this list will not be able to start this server, or even see it in the list view!
6. Optional: For each server folder (the folders configured in `config.py`'s `SERVER_FOLDERS`), add a `mc_server_web.txt` file, filled with comma-separted friendly names, as in step 5. Any users not in this list will not be able to start any server in this folder, even if they are present in an individual server's whitelist in step 5.
7. `python run_server.py` to run MC Server Web.

### Admins

Admins are more powerful than normal users. They have the following extra powers:
- Admins bypass all whitelists, allowing them to see and boot all servers.
- Admins get access to the console through the website. This acts as direct input to the console window. As of writing, these commands do NOT have control codes filtered out!