from pathlib import Path

from alembic import command
from alembic.config import Config

from ocg.core.settings import get_settings


def test_alembic_upgrade_and_downgrade(tmp_path):
    db_file = tmp_path / "test.db"
    url = f"sqlite+pysqlite:///{db_file.as_posix()}"
    import os

    os.environ["OCG_DATABASE_URL"] = url
    get_settings.cache_clear()

    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "alembic"))
    cfg.set_main_option("prepend_sys_path", str(Path(__file__).resolve().parents[2]))
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")
