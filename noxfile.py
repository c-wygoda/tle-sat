from nox import Session, session


@session(python=["3.10", "3.11", "3.12"], venv_backend="uv")
def tests(session: Session):
    session.run_install(
        "uv",
        "sync",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("pytest", *session.posargs)
