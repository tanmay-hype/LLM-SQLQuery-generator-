from abc import ABC, abstractmethod


class BaseSQLCache(ABC):

    @abstractmethod
    def get(
        self,
        key: str,
    ) -> str | None:
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        sql: str,
    ) -> None:
        pass

    @abstractmethod
    def delete(
        self,
        key: str,
    ) -> bool:
        """
        Delete a cache entry.

        Returns True if an entry existed and was deleted.
        Returns False if the key did not exist.
        """
        pass

    @abstractmethod
    def clear(
        self,
    ) -> None:
        pass

    @abstractmethod
    def __len__(
        self,
    ) -> int:
        pass