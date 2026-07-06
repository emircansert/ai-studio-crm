import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { DomainListPage } from "@/components/DomainListPage";

export default function NetworkPage() {
  return (
    <ProtectedPage>
      <DomainListPage
        kind="network"
        eyebrow="Relationships"
        title="Network Library"
        description="Manage investor, accelerator, institution, and expert relationships."
      />
    </ProtectedPage>
  );
}
