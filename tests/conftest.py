import os

# Must run before app.config is imported: `settings = Settings()` reads the
# environment at import time. Keeps the app's lifespan from starting a real
# scheduler (against the dev database) whenever a test starts the app.
os.environ["SCHEDULER_ENABLED"] = "false"
