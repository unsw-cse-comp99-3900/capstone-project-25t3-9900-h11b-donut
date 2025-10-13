import ArrowRight from '../assets/icons/arrow-right-16.svg'

type Props = {
  text: string
  onClick?: () => void
}
export function PrimaryButton({ text, onClick }: Props) {
  return (
    <button className="primary-btn" onClick={onClick}>
      <span>{text}</span>
      <img className="arrow" src={ArrowRight} width={16} height={16} alt="" aria-hidden />
    </button>
  )
}