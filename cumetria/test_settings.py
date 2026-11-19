"""Settings for the automated tests: debug on, throwaway key, temporary data folder."""
import os
import tempfile

os.environ.setdefault("DJANGO_DEBUG", "true")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key")
os.environ.setdefault("DATA_DIR", os.path.join(tempfile.gettempdir(), "cumetria-test-data"))

from .settings import *  # noqa: E402,F401,F403
