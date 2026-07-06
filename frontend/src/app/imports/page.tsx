import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { ImportCenter } from "@/components/import-center/ImportCenter";
import { PageHeader } from "@/components/ui/PageHeader";

export default function ImportCenterPage() {
  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Data intake"
        title="Import Center"
        description="Upload, profile, validate, and preview the Ecosystem Library before any CRM records are created."
      />
      <ImportCenter />
    </ProtectedPage>
  );
}
