from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.seed import backfill_phase2_records


if __name__ == "__main__":
    try:
        with SessionLocal.begin() as session:
            counts = backfill_phase2_records(session)
    except SQLAlchemyError as error:
        print(
            "Phase 2 backfill failed because the PostgreSQL operation was "
            "unsuccessful. No credentials were printed."
        )
        raise SystemExit(1) from error
    except Exception as error:
        print(f"Phase 2 backfill failed: {error}")
        raise SystemExit(1) from error

    print("Verified Phase 2 records imported successfully.")

    for name, count in counts.items():
        print(f"{name}: {count}")
