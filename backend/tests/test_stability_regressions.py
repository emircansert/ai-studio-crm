import unittest

from sqlalchemy import select, true
from sqlalchemy.dialects import mssql

from app.models import BrandingAsset, Organization, OrganizationDocument, User, UserContribution
from app.services.notifications import should_write_crm_activity
from app.services.soft_delete import not_archived, not_excluded


class StabilityRegressionTests(unittest.TestCase):
    def test_archive_filter_is_sql_server_safe(self) -> None:
        statement = select(Organization).where(not_archived(Organization.is_archived))
        sql = str(statement.compile(dialect=mssql.dialect()))
        self.assertIn("organizations.is_archived = 0", sql)
        self.assertIn("organizations.is_archived IS NULL", sql)

    def test_contribution_exclusion_filter_is_sql_server_safe(self) -> None:
        statement = select(UserContribution).where(not_excluded(UserContribution.is_excluded))
        sql = str(statement.compile(dialect=mssql.dialect()))
        self.assertIn("user_contributions.is_excluded = 0", sql)
        self.assertIn("user_contributions.is_excluded IS NULL", sql)

    def test_organization_documents_query_has_deterministic_order(self) -> None:
        statement = (
            select(OrganizationDocument)
            .where(OrganizationDocument.organization_id == "00000000-0000-0000-0000-000000000000")
            .order_by(OrganizationDocument.uploaded_at.desc(), OrganizationDocument.id.desc())
            .offset(0)
            .limit(100)
        )
        sql = str(statement.compile(dialect=mssql.dialect()))
        self.assertIn("ORDER BY", sql)
        self.assertTrue("OFFSET" in sql or "ROW_NUMBER()" in sql)

    def test_active_users_query_is_sql_server_safe(self) -> None:
        statement = (
            select(User)
            .where(User.is_active == true())
            .order_by(User.full_name.asc(), User.email.asc(), User.id.asc())
            .limit(500)
        )
        sql = str(statement.compile(dialect=mssql.dialect()))
        self.assertIn("users.is_active = 1", sql)
        self.assertIn("ORDER BY", sql)
        self.assertNotIn("users.is_active IS 1", sql)

    def test_active_branding_query_is_sql_server_safe(self) -> None:
        statement = select(BrandingAsset).where(BrandingAsset.asset_type == "LOGO", BrandingAsset.is_active == true())
        sql = str(statement.compile(dialect=mssql.dialect()))
        self.assertIn("branding_assets.is_active = 1", sql)
        self.assertNotIn("branding_assets.is_active IS 1", sql)

    def test_admin_activity_feed_filters_non_crm_audit_actions(self) -> None:
        self.assertTrue(should_write_crm_activity("ORGANIZATION_CREATED", "ORGANIZATION"))
        self.assertTrue(should_write_crm_activity("FOLLOW_UP_ASSIGNED", "FOLLOW_UP_ACTION"))
        self.assertFalse(should_write_crm_activity("USER_PASSWORD_CHANGED", "USER"))
        self.assertFalse(should_write_crm_activity("ADMIN_USER_PASSWORD_RESET", "USER"))


if __name__ == "__main__":
    unittest.main()


class AuditLogJsonSafetyTests(unittest.TestCase):
    def test_json_safe_coerces_uuid_and_datetime(self) -> None:
        import uuid
        from datetime import datetime, timezone

        from app.services.audit import _json_safe

        payload = {
            "id": uuid.uuid4(),
            "created_at": datetime.now(timezone.utc),
            "nested": {"user_id": uuid.uuid4(), "scores": [1, 2, 3]},
            "name": "ok",
            "none": None,
        }
        result = _json_safe(payload)
        self.assertIsInstance(result["id"], str)
        self.assertIsInstance(result["created_at"], str)
        self.assertIsInstance(result["nested"]["user_id"], str)
        self.assertEqual(result["name"], "ok")
        self.assertIsNone(result["none"])
        self.assertIsNone(_json_safe(None))
