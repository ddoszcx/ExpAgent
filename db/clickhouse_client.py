import clickhouse_connect
import pandas as pd 
import os



class ClickHouseClient:
    def __init__(self):
        self.conn = clickhouse_connect.get_client(
            host= os.getenv('CLICKHOUSE_HOST'),
            port= os.getenv('CLICKHOUSE_PORT'),
            user= os.getenv('CLICKHOUSE_USER'),
            password= os.getenv('CLICKHOUSE_PASSWORD')
        )
        self.database = os.getenv('CLICKHOUSE_DB', 'default')


    
    def test_connection(self) -> bool:
        try:
            self.conn.query('SELECT 1')
            return True
        except:
            return False


    def execute_query(self, sql: str) -> pd.DataFrame:
        return self.conn.query_df(sql)


    def get_schema(self) -> dict:
        df = self.execute_query(
            f"SELECT table, name, type FROM system.columns WHERE database = '{self.database}'"
        )
        schema = {}
        for index, row in df.iterrows():
            table = row['table']
            column = row['name']
            col_type = row['type']

            if table not in schema:
                schema[table] = {}
            schema[table][column] = col_type

        return schema
