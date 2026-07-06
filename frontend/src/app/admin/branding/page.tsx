import { BrandingManager } from "@/components/BrandingManager";
import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { PageHeader } from "@/components/ui/PageHeader";

export default function AdminBrandingPage() {
  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Admin"
        title="Branding"
        description="Manage the Borusan AI Studio visual identity for the CRM shell."
      />
      <BrandingManager />
    </ProtectedPage>
  );
}
