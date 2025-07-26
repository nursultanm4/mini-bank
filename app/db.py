from sqlmodel import SQLModel, create_engine


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)


def on_startup():
    SQLModel.metadata.create_all(engine)