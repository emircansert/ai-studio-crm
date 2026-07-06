import { Badge } from "@/components/ui/Badge";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";

type PlaceholderPageProps = {
  eyebrow: string;
  title: string;
  description: string;
  planned: string[];
};

export function PlaceholderPage({ eyebrow, title, description, planned }: PlaceholderPageProps) {
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} description={description} />
      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>No records yet</h2>
            <p>Data will appear here once records are added or imported.</p>
          </div>
          <Badge tone="info">Ready</Badge>
        </div>
        <div className="placeholder-grid">
          {planned.map((item) => (
            <div key={item}>{item}</div>
          ))}
        </div>
        <EmptyState
          title="No records available"
          description="Create the first record or use the import flow to populate this workspace."
        />
      </SectionCard>
    </>
  );
}
