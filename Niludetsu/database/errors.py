from __future__ import annotations


class DatabaseError(Exception):
    pass


class DatabaseConnectionError(DatabaseError):
    pass


class QueryError(DatabaseError):
    pass


class RecordNotFoundError(DatabaseError):
    pass


class RetryExhaustedError(DatabaseConnectionError):
    pass
