type Props = {
  title: string
  subtitle?: string
}
export function Header({ title, subtitle }: Props) {
  return (
    <>
      <h2 className="h2 title">{title}</h2>
      {subtitle ? <p className="p2 sub">{subtitle}</p> : null}
    </>
  )
}