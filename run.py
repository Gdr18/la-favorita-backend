from src import run_app
from config import config

app = run_app(config)

if __name__ == "__main__":
    app.run()