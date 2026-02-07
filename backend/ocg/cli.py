import json
from pathlib import Path

import typer
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, select

from ocg.connectors.registry import CONNECTOR_REGISTRY
from ocg.core.settings import get_settings
from ocg.db import models
from ocg.db.session import SessionLocal
from ocg.services import aggregation, identity, ingest, kg, personal
from ocg.workers import jobs

app = typer.Typer(help="Open Context Graph CLI")
migrate_app = typer.Typer(help="Migration commands")
seed_app = typer.Typer(help="Seed commands")
diag_app = typer.Typer(help="Diagnostic commands")

app.add_typer(migrate_app, name="migrate")
app.add_typer(seed_app, name="seed")
app.add_typer(diag_app, name="diagnostics")


def _alembic_cfg() -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("prepend_sys_path", str(backend_root))
    return cfg


@migrate_app.command("up")
def migrate_up(revision: str = "head") -> None:
    command.upgrade(_alembic_cfg(), revision)
    typer.echo(f"migrated to {revision}")


@migrate_app.command("down")
def migrate_down(revision: str = "-1") -> None:
    command.downgrade(_alembic_cfg(), revision)
    typer.echo(f"downgraded to {revision}")


@seed_app.command("demo")
def seed_demo() -> None:
    db = SessionLocal()
    try:
        # Enable connectors with secret refs only.
        for tool in ("slack", "jira", "github"):
            ingest.set_connector_enabled(
                db,
                tool,
                True,
                {
                    "auth": {"token_ref": f"env:{tool.upper()}_TOKEN"},
                    "scopes": ["read:default"],
                },
            )

        for tool, connector in CONNECTOR_REGISTRY.items():
            cfg = db.scalar(select(models.ConnectorConfig).where(models.ConnectorConfig.tool == tool))
            ingest.ingest_connector_batch(db, connector, cfg.config_json if cfg else {})
            ingest.sync_permissions(db, connector, cfg.config_json if cfg else {})

        identity.resolve_identities(db)
        kg.infer_kg_entities(db)

        for person in ("demo-user",):
            identity.ensure_person_and_principal(db, person, email=f"{person}@ocg.local")
            personal.set_opt_in(db, person, True)
            personal.build_personal_timeline(db, person, [person, "group:analyst", "group:admin"])
            personal.cluster_personal_tasks(db, person)
        aggregation.abstract_opted_in_traces(db)
        from ocg.core.settings import get_settings

        settings = get_settings()
        settings.k_anonymity_k = 1
        settings.k_anonymity_n = 1
        aggregation.cluster_and_publish(db, settings)
        typer.echo("demo seed complete")
    finally:
        db.close()


@diag_app.command("connectors")
def diagnostics_connectors() -> None:
    db = SessionLocal()
    try:
        rows = db.scalars(select(models.ConnectorConfig).order_by(models.ConnectorConfig.tool.asc())).all()
        if not rows:
            typer.echo("no connector config")
            return
        for row in rows:
            typer.echo(f"{row.tool}: enabled={row.enabled}")
    finally:
        db.close()


@app.command("worker-run")
def worker_run(job_name: str, arg: str = "") -> None:
    if job_name == "ingest":
        typer.echo(jobs.run_connector_ingest(arg))
        return
    if job_name == "permissions":
        typer.echo(jobs.run_permissions_sync(arg))
        return
    if job_name == "aggregation":
        typer.echo(jobs.run_aggregation())
        return
    if job_name == "kg":
        typer.echo(jobs.run_kg_and_identity())
        return
    typer.echo(f"unknown job {job_name}")
    raise typer.Exit(code=2)


@app.command("export-user")
def export_user(person_id: str, output: str = "artifacts/export.json") -> None:
    db = SessionLocal()
    try:
        timeline = personal.personal_timeline(db, person_id, None, None)
        tasks = personal.personal_tasks(db, person_id)
        payload = {"person_id": person_id, "timeline": timeline, "tasks": tasks}
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        typer.echo(f"exported {person_id} to {out}")
    finally:
        db.close()


@app.command("delete-user")
def delete_user(person_id: str) -> None:
    db = SessionLocal()
    try:
        db.execute(delete(models.PersonalTask).where(models.PersonalTask.person_id == person_id))
        db.execute(delete(models.PersonalTimelineItem).where(models.PersonalTimelineItem.person_id == person_id))
        db.execute(delete(models.PersonalOptIn).where(models.PersonalOptIn.person_id == person_id))
        db.execute(delete(models.Identity).where(models.Identity.person_id == person_id))
        db.execute(delete(models.Person).where(models.Person.person_id == person_id))
        db.commit()
        typer.echo(f"deleted user scope for {person_id}")
    finally:
        db.close()


@app.command("purge")
def purge() -> None:
    db = SessionLocal()
    try:
        settings = get_settings()
        if not settings.retention_enabled:
            typer.echo("retention disabled; refusing purge")
            raise typer.Exit(code=2)
        # Minimal deterministic purge baseline.
        typer.echo("purge completed (placeholder baseline)")
    finally:
        db.close()


if __name__ == "__main__":
    app()
