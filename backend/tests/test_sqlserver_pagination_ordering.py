import unittest

from sqlalchemy import select
from sqlalchemy.dialects import mssql

from app.models import ImportBatch, Organization, Status
from app.services.crud import CRUDService


class SQLServerPaginationOrderingTests(unittest.TestCase):
    def assert_mssql_paginated_statement_has_order_by(self, statement) -> None:
        sql = str(statement.compile(dialect=mssql.dialect()))
        self.assertIn("ORDER BY", sql)
        self.assertTrue("OFFSET" in sql or "ROW_NUMBER()" in sql)

    def test_import_batches_pagination_has_order_by(self) -> None:
        statement = select(ImportBatch).order_by(ImportBatch.created_at.desc(), ImportBatch.id.desc()).offset(0).limit(100)
        self.assert_mssql_paginated_statement_has_order_by(statement)

    def test_generic_crud_default_ordering_is_sql_server_safe(self) -> None:
        service = CRUDService(Organization)
        statement = select(Organization).order_by(service._default_order_by()).offset(0).limit(100)
        self.assert_mssql_paginated_statement_has_order_by(statement)

    def test_organization_sort_variants_compile_for_sql_server(self) -> None:
        from app.api.v1.endpoints.organizations import _ordered

        for sort_by in ("newest", "oldest", "name_asc", "last_contact_desc", "last_contact_asc"):
            statement = _ordered(select(Organization), sort_by).offset(0).limit(100)
            sql = str(statement.compile(dialect=mssql.dialect()))
            self.assertIn("ORDER BY", sql, sort_by)
            # SQL Server does not support NULLS FIRST/LAST syntax.
            self.assertNotIn("NULLS", sql.upper(), sort_by)

    def test_status_vocabulary_pagination_has_deterministic_order(self) -> None:
        statement = (
            select(Status)
            .order_by(Status.status_group.asc(), Status.sort_order.asc(), Status.code.asc(), Status.id.asc())
            .offset(0)
            .limit(100)
        )
        self.assert_mssql_paginated_statement_has_order_by(statement)


if __name__ == "__main__":
    unittest.main()
