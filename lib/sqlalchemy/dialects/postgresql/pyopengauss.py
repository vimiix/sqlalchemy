# postgresql/pyopengauss.py

"""
.. dialect:: postgresql+pyopengauss
    :name: py-opengauss
    :dbapi: pyopengauss
    :connectstring: postgresql+pyopengauss://user:password@host:port/dbname[?key=value&key=value...]
    :url: https://python.projects.pgfoundry.org/
"""  # noqa

from .base import PGDialect
from .base import PGExecutionContext
from ... import processors
from ... import types as sqltypes
from ... import util


class PGNumeric(sqltypes.Numeric):
    def bind_processor(self, dialect):
        return processors.to_str

    def result_processor(self, dialect, coltype):
        if self.asdecimal:
            return None
        else:
            return processors.to_float


class PGExecutionContext_pypostgresql(PGExecutionContext):
    pass


class PGDialect_pyopengauss(PGDialect):
    driver = "pyopengauss"

    supports_statement_cache = True
    supports_unicode_statements = True
    supports_unicode_binds = True
    description_encoding = None
    default_paramstyle = "pyformat"

    # requires trunk version to support sane rowcounts
    # TODO: use dbapi version information to set this flag appropriately
    supports_sane_rowcount = True
    supports_sane_multi_rowcount = False

    execution_ctx_cls = PGExecutionContext_pypostgresql
    colspecs = util.update_copy(
        PGDialect.colspecs,
        {
            sqltypes.Numeric: PGNumeric,
            # prevents PGNumeric from being used
            sqltypes.Float: sqltypes.Float,
        },
    )

    @classmethod
    def dbapi(cls):
        from py_opengauss.driver import dbapi20
        return dbapi20

    _DBAPI_ERROR_NAMES = [
        "Error",
        "InterfaceError",
        "DatabaseError",
        "DataError",
        "OperationalError",
        "IntegrityError",
        "InternalError",
        "ProgrammingError",
        "NotSupportedError",
    ]

    @util.memoized_property
    def dbapi_exception_translation_map(self):
        if self.dbapi is None:
            return {}

        return dict(
            (getattr(self.dbapi, name).__name__, name)
            for name in self._DBAPI_ERROR_NAMES
        )

    def create_connect_args(self, url):
        opts = url.translate_connect_args(username="user")
        if "port" in opts:
            opts["port"] = int(opts["port"])
        else:
            opts["port"] = 5432
        opts.update(url.query)
        return ([], opts)

    def is_disconnect(self, e, connection, cursor):
        return "connection is closed" in str(e)


dialect = PGDialect_pyopengauss
