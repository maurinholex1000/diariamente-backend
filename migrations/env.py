
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# Importar explícitamente todos los modelos para registrarlos en Base.metadata
from app.models.user import User
from app.models.diary_entry import DiaryEntry
from app.models.therapist_patient import TherapistPatient
from app.models.consent_request import ConsentRequest
from app.models.user_consent import UserConsent


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Utilizar la misma conexión configurada para FastAPI.
# Escapar '%' para evitar problemas con ConfigParser.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("%", "%%"),
)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
