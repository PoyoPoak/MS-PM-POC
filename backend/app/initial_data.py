import logging

from sqlmodel import Session

from app.core.db import engine, init_db
from app.telemetry_seed import seed_pacemaker_telemetry_if_empty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        seed_pacemaker_telemetry_if_empty(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
