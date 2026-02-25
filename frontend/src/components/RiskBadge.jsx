export default function RiskBadge({ category }) {
    if (!category) return <span className="text-slate-500 text-xs">—</span>

    const styles = {
        'High': 'badge-high',
        'Medium': 'badge-medium',
        'At Risk': 'badge-risk',
    }

    return (
        <span className={styles[category] || 'badge-medium'}>
            {category}
        </span>
    )
}
