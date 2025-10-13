type Props = {
  title: string
  body: string
  selected?: boolean
  onClick?: () => void
  iconSrc?: string
  badgeBg?: string
  badgeBorder?: string
}
export function RoleCard({ title, body, selected, onClick, iconSrc, badgeBg = '#FFF1E8', badgeBorder = '#F1E1D7' }: Props) {
  return (
    <div className={`role-card ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div className="icon" style={{ background: badgeBg, borderColor: badgeBorder }}>
        {iconSrc ? <img src={iconSrc} width={32} height={32} alt="" aria-hidden /> : null}
      </div>
      <div className="text">
        <div className="title">{title}</div>
        <p className="p3 body">{body}</p>
      </div>
    </div>
  )
}