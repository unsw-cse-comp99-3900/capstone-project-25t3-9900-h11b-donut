type Props = {
  checked: boolean
  onChange: (val: boolean) => void
  label: string
}
export function Checkbox({ checked, onChange, label }: Props) {
  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        style={{ width: 16, height: 16 }}
      />
      <span className="p3" style={{ color: 'var(--color-text-muted)' }}>{label}</span>
    </label>
  )
}