import asyncio
import os
import aiosqlite

from operator_mod.logger.global_logger import Logger
from model.utils.file_access.file_access_manager import FileAccessManager

class SQLManager:
    """
    The global instance of the Database Manager. Can be called anywhere. Thread and singleton safe.

    Integration:
    When u want to write data to a sql.db file:
        create_tabel_statement, insert_statement = sql.generate_sql_statements(table_name, data)
        sql.read_or_write(path, insert_statement, "write")

    When u want to read data from a sql.db file:
        result = sql.read_or_write(path, query, "read")
    Returns:
        None
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):

        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.sqllogger = Logger("SQLManager").logger
            self.file_manager = FileAccessManager()
            self._connection = None

    async def _connect(self, path: str):
        async with self._lock:
            try:
                self._connection = await aiosqlite.connect(path)
            except Exception as e:
                self.sqllogger.error(f"Error connecting: {e}")

    async def _write(self, query: str) -> bool:
        async with self._lock:
            try:
                async with self._connection.cursor() as cursor:  # noqa: F841
                    await cursor.execute(query)
                    await self._connection.commit()
                return True
            except Exception as e:
                self.sqllogger.error(f"Writing Error: {e}")
                return False

    async def _read(self, query: str) -> list:
        async with self._lock:
            try:
                async with self._connection.cursor() as cursor:
                    await cursor.execute(query)
                    result = await cursor.fetchall()
                return result
            except Exception as e:
                self.sqllogger.error(f"Reading Error: {e}")
                return []

    async def _disconnect(self):
        async with self._lock:
            try:
                if self._connection:
                    await self._connection.close()
                    self._connection = None
            except Exception as e:
                self.sqllogger.error(f"Error disconnecting: {e}")

    def read_or_write(self, path, query, task):
        """This is the main interactable that does reading/writing with automatic file access generation. Nothing to be done just call this.

        Args:
            path (str): path to the .db file
            query (str): generated by sql.generate_sql_statements()
            task (str): write / read

        Returns:
            result (if read): a list of results
        """
        try:
            if task == "write":
                if os.path.exists(path):
                    self.file_manager.get_access(path)
                    asyncio.run(self._sql_handler(path, query, task))
                    self.file_manager.release_access(path)
                else:
                    asyncio.run(self._sql_handler(path, query, task))
            elif task == "read":
                self.file_manager.get_access(path)
                result = asyncio.run(self._sql_handler(path, query, task))
                self.file_manager.release_access(path)
                return result
        except Exception as e:   
            self.sqllogger.error(f"Error in writing: {e}.")


    async def _sql_handler(self, path, query, action):
        """This is the actual async funtions thats executed."""

        await self._connect(path)

        if action == "write":
            await self._write(query)

        elif action == "read":
            result = await self._read(query)
            await self._disconnect()
            return result

        await self._disconnect()

    def _infer_sql_type(self, value):

        if isinstance(value, int):
            return "INT"
        elif isinstance(value, float):
            return "REAL"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, str):
            return "VARCHAR(255)"
        elif isinstance(value, list):
            return "TEXT"
        elif value is None:
            return "VARCHAR(255)"
        else:
            raise TypeError(f"Unsupported data type: {type(value)}")

    def generate_sql_statements(self, table_name: str, data: dict) -> tuple:
        """Generates sql statements dynamically for table creation and insertion based on given data.

        Args:
            table_name (str): any name
            data (hashmap): hasmap/dictionary

        Returns:
            (create_table, insert): two strings that can be used as querys for sql handler.
        """
        keys = data.keys()
        
        # Generate CREATE TABLE statement
        columns_definitions = []
        for key in keys:
            sql_type = self._infer_sql_type(data[key])
            columns_definitions.append(f"{key} {sql_type}")
        create_table_statement = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + ",\n    ".join(columns_definitions) + "\n);"
        
        # Generate INSERT INTO statement
        columns = ", ".join(keys)
        values = ", ".join([f"'{v}'" if isinstance(v, str) else ("NULL" if v is None else str(v)) for v in data.values()])
        insert_statement = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
        
        return create_table_statement, insert_statement