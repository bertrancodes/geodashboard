from definitions import SQL_PATH


def read_sql_query(sql_file: str) -> str:
    """
    Read an SQL file and return the query as a string
    """
    return (SQL_PATH / sql_file).read_text()
