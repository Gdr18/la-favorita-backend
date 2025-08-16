from config import config, Config
from src.app import run_app

app = run_app(config)

if __name__ == "__main__":
    app.run(port=Config.PORT)
