import duckdb
import pandas as pd 


class DuckDBClient:
    def __init__(self, db_path : str = ':memory:'): # датасет в оперативку 
        self.conn = duckdb.connect(db_path)



    def load_experiment(self, df: pd.DataFrame, experiment_name: str): # загрузка датасет в sql
        self.conn.execute(f'CREATE OR REPLACE TABLE {experiment_name} AS SELECT * FROM df')


    def execute_query(self, sql: str) -> pd.DataFrame:  # выполнение запроса в таблицу 
        return self.conn.execute(sql).df()



    def get_schema(self) -> dict:  # получение схемы 
        df = self.execute_query("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'main'")

        schema = {    }
        
        for index, row in df.iterrows(): 
            table  = row['table_name']
            column = row['column_name']
            type = row['data_type']

            if table not in schema: # если такой таблицы еще нету 
                schema[table] = {} # пустой словарь
            schema[table][column] = type 

        return schema

