import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { DomainListPage } from "@/components/DomainListPage";

export default function CompaniesPage() {
  return (
    <ProtectedPage>
      <DomainListPage
        kind="companies"
        eyebrow="Library"
        title="Startup Library"
        description="A normalized company and vendor workspace for AI ecosystem discovery."
      />
    </ProtectedPage>
  );
}
