from nox_poetry import Session, session


@session(python=["3.10", "3.11", "3.12"])
def tests(session: Session):
    session.install("pytest", "pytest-coverage")
    session.run_always("poetry", "install", external=True)
    session.run("pytest")
