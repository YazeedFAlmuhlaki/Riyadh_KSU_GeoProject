# adding needed imports
import psycopg2
from sql_queries import drop_table_queries,create_table_queries
import configparser



def get_connection():
    """
    
    a helper function will read DB parameters from db.cfg and return connection and cursior
    """

    config = configparser.ConfigParser()
    config.read('config/db.cfg')

    db_host = config.get("postgresql" , "host")
    db_name = config.get("postgresql" , "dbname")
    db_user = config.get("postgresql" , "user")
    db_password = config.get("postgresql" , "password")
    db_port = config.get("postgresql" , "port")

    try:
        conn = psycopg2.connect(
        dbname = db_name,
        host = db_host, 
        user = db_user,
        port = db_port,
        password = db_password
        )
        cur = conn.cursor()

    except psycopg2.DatabaseError as e:
        print("Error" , e)
    
    else:
        print(f"connection to {db_name} is done!")
        return conn , cur

    
def drop_tables(cur , conn):
    """

    this method accept two parameter 
    cur and conn to excuate a predefiend (droping queries)
    cur will excuate the query , conn will commit the changes to the database
    """
    try:
        for query in drop_table_queries:
            cur.execute(query)
        conn.commit()
    except psycopg2.OperationalError as e:
        print("Error:" , e)
    
    else:
        print("dropping all tables is done!")


def create_tables(cur , conn):
    """
    this method accept two parameter 
    cur and conn to excuate a predefiend (creating queries)
    cur will excuate the query , conn will commit the changes to the database
    """
    try:
        for query in create_table_queries:
            cur.execute(query)
        conn.commit()
    except psycopg2.OperationalError as e:
        print("Error:" , e)

    else:
        print("creating all tables is done!")


def main():
    conn , cur = get_connection()
    drop_tables(cur , conn)
    create_tables(cur , conn)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

