import pandas as pd
from sqlalchemy import create_engine, text

from definitions import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from utils import read_sql_query


def main() -> None:
    """
    Connect to the database, create the 'time' table and insert data into it
    """

    # Connection URL
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    connection = engine.connect()

    create_time_table = read_sql_query("create_time_table.sql")

    connection.execute(text(create_time_table))
    connection.commit()

    insert_to_time = read_sql_query("insert_to_time.sql")

    df = pd.DataFrame(
        data=pd.date_range("1950-01-01", "2024-07-31", freq="D"), columns=["date"]
    )

    values = df.to_dict(orient="records")

    connection.execute(text(insert_to_time), values)
    connection.commit()

    connection.close()


if __name__ == "__main__":
    main()
