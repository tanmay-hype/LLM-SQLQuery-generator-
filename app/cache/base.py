from abc import ABC, abstractmethod


class BaseSQLCache(ABC):
    """
    Interface for SQL cache implementations.

    QueryService will depend on this abstraction rather
    than a concrete in-memory or Redis implementation.
    """

    @abstractmethod
    def get(
        self,
        key: str,
    ) -> str | None:
        """
        Return cached SQL for the key.

        Returns None when the key does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def set(
        self,
        key: str,
        sql: str,
    ) -> None:
        """
        Store validated SQL.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all cached SQL entries.
        """
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        """
        Return number of cached entries.
        """
        raise NotImplementedError