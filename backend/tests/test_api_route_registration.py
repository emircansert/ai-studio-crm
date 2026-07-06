import unittest

from app.main import app


class ApiRouteRegistrationTests(unittest.TestCase):
    def test_use_case_routes_are_registered(self) -> None:
        paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/api/v1/use-cases", paths)
        self.assertIn("/api/v1/use-cases/{use_case_id}", paths)
        self.assertIn("/api/v1/use-cases/{use_case_id}/archive", paths)
        self.assertIn("/api/v1/use-cases/{use_case_id}/unarchive", paths)

    def test_program_activity_routes_are_registered(self) -> None:
        paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/api/v1/program-activities", paths)
        self.assertIn("/api/v1/program-activities/{activity_id}", paths)
        self.assertIn("/api/v1/program-activities/{activity_id}/participants", paths)
        self.assertIn("/api/v1/program-activities/{activity_id}/participants/{participant_id}", paths)
        self.assertIn("/api/v1/program-activities/{activity_id}/archive", paths)
        self.assertIn("/api/v1/program-activities/{activity_id}/unarchive", paths)

    def test_route_diagnostics_is_registered(self) -> None:
        paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/api/v1/health/routes", paths)

    def test_ai_tools_routes_are_registered(self) -> None:
        paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/api/v1/ai-tools", paths)
        self.assertIn("/api/v1/ai-tools/{tool_id}", paths)
        self.assertIn("/api/v1/ai-tools/{tool_id}/archive", paths)
        self.assertIn("/api/v1/ai-tools/{tool_id}/unarchive", paths)

    def test_poc_pipeline_board_routes_are_registered(self) -> None:
        paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/api/v1/opportunities", paths)
        self.assertIn("/api/v1/opportunities/{opportunity_id}/stage", paths)
        self.assertIn("/api/v1/opportunities/{opportunity_id}/documents", paths)
        self.assertIn("/api/v1/opportunities/{opportunity_id}/documents/{document_id}/download", paths)

    def test_section_access_routes_are_registered(self) -> None:
        paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/api/v1/users/me/section-access", paths)
        self.assertIn("/api/v1/admin/users/section-access", paths)
        self.assertIn("/api/v1/admin/users/{user_id}/section-access", paths)


if __name__ == "__main__":
    unittest.main()
