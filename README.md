# MC Server Web

Control Minecraft servers from a web UI and allow others to as well!

This project is mainly intended for friend groups with one person doing DIY server hosting.

## Note

This was built for personal use. PRs likely will not be accepted, and any support is very unlikely to be provided. Bug reports are still very much accepted, though, and you're of course free to do anything as permitted by the license located in the `LICENSE` file.

Thanks to <https://blog.miguelgrinberg.com/post/oauth-authentication-with-flask-in-2023> for the understanding and implementation of OAuth2. The code for the tutorial is found [here](https://github.com/miguelgrinberg/flask-oauth-example). 

## Setup

1. `python -m pip install -r requirements.txt` to install requirements. This is tested with Python 3.12, though earlier versions will probably work.
2. Add the environment variables as mentioned in `config.py`.
3. `python app.py` to run the server.