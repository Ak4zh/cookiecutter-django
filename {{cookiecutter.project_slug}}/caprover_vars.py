import os
from os import getenv as env

from dotenv import dotenv_values, load_dotenv


def setup():
    caprover_vars = {}
    try:
        load_dotenv('.env')
        caprover_vars = dotenv_values(".env")
        cap_namespace = env("CAPROVER_NAMESPACE")
        redis_url = f"redis://:{env('REDIS_PASSWORD')}@srv-captain--{cap_namespace}-redis:6379/0"
        postgres_host = f"srv-captain--{cap_namespace}-postgres-db"
        # database_url = f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}" \
        #                f"@{postgres_host}:{env('POSTGRES_PORT')}/{env('POSTGRES_DB')}"

        caprover_vars["REDIS_URL"] = redis_url
        caprover_vars["POSTGRES_HOST"] = postgres_host
        if caprover_vars.get("DATABASE_URL"):
            del caprover_vars["DATABASE_URL"]

        for k, v in caprover_vars.items():
            if v and isinstance(v, str) and k not in ["DJANGO_ALLOWED_HOSTS"]:
                os.environ.setdefault(k, v)

    except ImportError:
        pass
    return caprover_vars
