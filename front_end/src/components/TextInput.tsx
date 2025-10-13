import type { InputHTMLAttributes } from 'react'

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
}
export function TextInput({ label, error, ...rest }: Props) {
  return (
    <label style={{ display: 'block', width: '100%' }}>
      <span className="p3" style={{ display: 'block', marginBottom: 8, color: 'var(--color-text-dark)', fontWeight: 600 }}>{label}</span>
      <input
        {...rest}
        className="input"
      />
      {error ? <span className="p3" style={{ color: '#D93025', marginTop: 6, display: 'block' }}>{error}</span> : null}
    </label>
  )
}