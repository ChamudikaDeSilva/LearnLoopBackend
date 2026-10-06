from logging.config import (
    fileConfig,
)

from sqlalchemy import (
    engine_from_config,
    pool,
)

from alembic import (
    context,
)

from app.core.config import (
    settings,
)

from app.core.database import (
    Base,
)

# ============================================================
# IMPORT ALL SQLALCHEMY MODELS
#
# These imports register the models with Base.metadata so
# Alembic can detect tables and schema changes.
# ============================================================

from app.models import (  # noqa: F401
    Flashcard,
    FlashcardSet,
    Material,
    MaterialSummary,
    Subject,
    User,
)


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================

config = (
    context.config
)


# ============================================================
# LOGGING
# ============================================================

if (
    config.config_file_name
    is not None
):

    fileConfig(
        config.config_file_name
    )


# ============================================================
# DATABASE URL
# ============================================================

if not settings.database_url:

    raise RuntimeError(
        "DATABASE_URL is not configured."
    )


config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)


# ============================================================
# SQLALCHEMY METADATA
# ============================================================

target_metadata = (
    Base.metadata
)


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline(
) -> None:

    url = (
        config.get_main_option(
            "sqlalchemy.url"
        )
    )


    context.configure(
        url=
            url,

        target_metadata=
            target_metadata,

        literal_binds=
            True,

        dialect_opts={
            "paramstyle":
                "named",
        },
    )


    with context.begin_transaction():

        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def run_migrations_online(
) -> None:

    connectable = (
        engine_from_config(
            config.get_section(
                config.config_ini_section,
                {},
            ),

            prefix=
                "sqlalchemy.",

            poolclass=
                pool.NullPool,
        )
    )


    with connectable.connect() as connection:

        context.configure(
            connection=
                connection,

            target_metadata=
                target_metadata,
        )


        with context.begin_transaction():

            context.run_migrations()


# ============================================================
# RUN
# ============================================================

if context.is_offline_mode():

    run_migrations_offline()

else:

    run_migrations_online()