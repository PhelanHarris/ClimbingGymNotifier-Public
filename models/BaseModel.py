from abc import ABC, abstractmethod


class BaseModel(ABC):
    @staticmethod
    @abstractmethod
    def get_table_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_column_names() -> list:
        pass
