import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { VendorLibraryPage } from "@/components/VendorLibraryPage";

export default function VendorsPage() {
  return (
    <ProtectedPage>
      <VendorLibraryPage />
    </ProtectedPage>
  );
}
