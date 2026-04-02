export default function SectionTitle({ badge, title, subtitle }) {
  return (
    <div className="section-title">
      {badge && <span className="section-badge">{badge}</span>}
      <h2>{title}</h2>
      {subtitle && <p>{subtitle}</p>}
    </div>
  )
}