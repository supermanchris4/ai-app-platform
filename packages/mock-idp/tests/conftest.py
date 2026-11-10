"""The tests run the provider with the example roles and people file, as an application's Compose
file would mount its own."""

import os
from pathlib import Path

# Set before mock_idp is imported, since it reads the file at start-up.
os.environ.setdefault("MOCK_IDP_CONFIG", str(Path(__file__).resolve().parents[1] / "example-roles-and-people.json"))
