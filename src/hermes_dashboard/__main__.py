"""Entry point: hermes-dashboard or python -m hermes_dashboard."""

import uvicorn

from hermes_dashboard.config import settings


def main() -> None:
    uvicorn.run(
        "hermes_dashboard.app:create_app",
        host=settings.host,
        port=settings.port,
        factory=True,
    )


if __name__ == "__main__":
    main()
