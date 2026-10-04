import json
import sys

config = json.load(sys.stdin)
environment = config["services"]["init"]["environment"]
for name, minimum_length in (("SECRET_KEY", 50), ("DB_PASSWORD", 24)):
    value = environment.get(name, "")
    if len(value) < minimum_length or "REPLACE_WITH" in value or "change-me" in value:
        raise SystemExit(f"Set a strong {name} in the Docker environment file.")
if environment.get("DEBUG", "").lower() != "false":
    raise SystemExit("Docker deployment requires DEBUG=False.")
if not environment.get("ALLOWED_HOSTS") or "*" in environment["ALLOWED_HOSTS"]:
    raise SystemExit("Set explicit ALLOWED_HOSTS; wildcard hosts are not permitted.")
