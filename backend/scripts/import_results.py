from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.seed import import_canonical_artifacts


if __name__ == "__main__":
    try:
        with SessionLocal.begin() as session:
            counts = import_canonical_artifacts(session)
    except SQLAlchemyError as error:
        print(
            "Canonical artifact import failed because the PostgreSQL "
            "operation was unsuccessful. No credentials were printed."
        )
        raise SystemExit(1) from error
    except Exception as error:
        print(f"Canonical artifact import failed: {error}")
        raise SystemExit(1) from error

    print("Canonical artifacts imported successfully.")

    for name, count in counts.items():
        print(f"{name}: {count}")
