export function StatusBadge({ value }: { value: string }) {
  const label = value.replace(/_/g, ' ')
  return <span className={`badge badge-${value}`}>{label}</span>
}
