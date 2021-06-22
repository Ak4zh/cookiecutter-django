from django.core.management.base import BaseCommand
from django.conf import settings
from caprover_api import caprover_api
import git

import caprover_vars


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    g = git.cmd.Git(settings.ROOT_DIR)
    GIT_URL = g.execute(["git", "config", "--get", "remote.origin.url"])
    ONE_CLICK_APPS = ['postgres', 'redis']
    CAPROVER_ENV_VARS = dict(caprover_vars.setup())
    CAPROVER_ENV_VARS['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
    SSH_KEY = CAPROVER_ENV_VARS["CAPROVER_SSH_KEY"].replace(r'\n', '\n')
    CAPROVER_NAMESPACE = CAPROVER_ENV_VARS["CAPROVER_NAMESPACE"]
    APP_HOST = CAPROVER_ENV_VARS["DJANGO_ALLOWED_HOSTS"].split(',')[0].strip('.')
    ENV_VARS = {k: v for k, v in CAPROVER_ENV_VARS.items() if not k.startswith('CAPROVER_')}

    REPO_INFO = {
        'repo': GIT_URL,
        'user': '', 'password': '',
        'branch': 'master',
        'sshKey': SSH_KEY
    }

    def handle(self, *args, **options):
        assert Command.ENV_VARS
        cap = caprover_api.CaproverAPI(
            dashboard_url=Command.CAPROVER_ENV_VARS["CAPROVER_DASHBOARD_URL"],
            password=Command.CAPROVER_ENV_VARS["CAPROVER_DASHBOARD_PASSWORD"]
        )

        app_variables = {
            "$$cap_postgres_version": {{ cookiecutter.postgresql_version }},
            "$$cap_pg_user": Command.ENV_VARS["POSTGRES_USER"],
            "$$cap_pg_pass": Command.ENV_VARS["POSTGRES_PASSWORD"],
            "$$cap_pg_db": Command.ENV_VARS["POSTGRES_DB"],
            "$$cap_redis_password": Command.ENV_VARS["REDIS_PASSWORD"],
        }

        # deploy one click apps
        for app in Command.ONE_CLICK_APPS:
            cap.deploy_one_click_app(
                one_click_app_name=app, namespace=Command.CAPROVER_NAMESPACE,
                automated=True, app_variables=app_variables
            )

        apps_to_deploy = {
             { % if cookiecutter.use_celery == 'y' - %}
            'celery-worker': {
                'captain_definition_path': './celery-worker-captain-definition',
                'environment_variables': Command.ENV_VARS,
                'repo_info': Command.REPO_INFO,
            },
            'celery-beat': {
                'captain_definition_path': './celery-beat-captain-definition',
                'environment_variables': Command.ENV_VARS,
                'repo_info': Command.REPO_INFO,
            },
            'celery-flower': {
                'captain_definition_path': './celery-flower-captain-definition',
                'environment_variables': Command.ENV_VARS,
                'repo_info': Command.REPO_INFO,
                # 'custom_domain': f'flower.{Command.APP_HOST}',
                # 'enable_ssl': True,
                'expose_as_web_app': True,
                # 'force_ssl': True,
                'container_http_port': 5555,
            },
            { % - endif %}

            'web': {
                'captain_definition_path': './captain-definition',
                'environment_variables': Command.ENV_VARS,
                'repo_info': Command.REPO_INFO,
                # 'custom_domain': Command.APP_HOST,
                # 'enable_ssl': True,
                'expose_as_web_app': True,
                # 'force_ssl': True,
                'container_http_port': 5000
            },
            { % if cookiecutter.cloud_provider == 'AWS' %}
            'postgresql-backup-s3': {
                'image_name': 'itbm/postgresql-backup-s3:1.0.8',
                'expose_as_web_app': False,
                'environment_variables': {
                    "POSTGRES_USER": Command.ENV_VARS["POSTGRES_USER"],
                    "POSTGRES_PASSWORD": Command.ENV_VARS["POSTGRES_PASSWORD"],
                    "POSTGRES_DATABASE": Command.ENV_VARS["POSTGRES_DB"],
                    "POSTGRES_HOST": Command.ENV_VARS['POSTGRES_HOST'],
                    "S3_ACCESS_KEY_ID": Command.ENV_VARS['DJANGO_AWS_ACCESS_KEY_ID'],
                    "S3_SECRET_ACCESS_KEY": Command.ENV_VARS['DJANGO_AWS_SECRET_ACCESS_KEY'],
                    "S3_BUCKET": Command.ENV_VARS['DJANGO_AWS_STORAGE_BUCKET_NAME'] + '-pvt',
                    "S3_REGION": Command.ENV_VARS['DJANGO_AWS_S3_REGION_NAME'],
                    "S3_ENDPOINT": Command.ENV_VARS.get("AWS_S3_ENDPOINT_URL"),
                    "SCHEDULE": "@daily",
                    "DELETE_OLDER_THAN": "7 days ago",
                }
            }
            { % endif - %}
        }
        for app, app_data in apps_to_deploy.items():
            cap.create_and_update_app(
                app_name=f'{Command.CAPROVER_NAMESPACE}-{app}',
                **app_data
            )

        self.stdout.write(self.style.SUCCESS('Deployed successfully'))
