type Props = {
  activeIndex: number
  total: number
}
export function PaginationDots({ activeIndex, total }: Props) {
  return (
    <div className="pagination" role="tablist" aria-label="Pagination">
      {Array.from({ length: total }).map((_, i) => (
        <span key={i} className={i === activeIndex ? 'active' : ''} role="tab" aria-selected={i === activeIndex}></span>
      ))}
    </div>
  )
}