type StatCardProps = {
  label: string;
  value: string;
  detail?: string;
  icon?: React.ReactNode;
};

export function StatCard({ label, value, detail, icon }: StatCardProps) {
  return (
    <section className="stat-card">
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        {detail ? <span>{detail}</span> : null}
      </div>
      {icon ? <div className="stat-icon">{icon}</div> : null}
    </section>
  );
}
