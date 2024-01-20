from waitress import serve
import app
import config
import sys

if __name__ == "__main__":
    config_err: str = config.verify_and_load_config()
    if config_err:
        app.app.logger.critical(config_err)
        sys.exit(1)
    app.app.secret_key = config.FLASK_SECRET_KEY
    serve(app.app, host="0.0.0.0", port=config.PORT)
