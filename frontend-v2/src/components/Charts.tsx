import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import type { Comparison, FeatureStability, ModelCurve } from '../types'
import { metricLabels } from './Shared'

const colors = ['#247d78', '#d27768', '#809b77', '#806d9b']

export function MetricComparisonChart({ rows }: { rows: Comparison[] }) {
  const data = ['roc_auc', 'pr_auc', 'balanced_accuracy', 'f1'].map(metric => ({
    metric: metricLabels[metric],
    ...Object.fromEntries(rows.map(row => [row.model, row.metrics[metric as keyof typeof row.metrics]])),
  }))
  return <div className="chart" aria-label="Сравнение на моделите">
    <ResponsiveContainer width="100%" height={310}>
      <BarChart data={data} margin={{ left: 4, right: 12 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="metric" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value) => Number(value).toFixed(3)} />
        <Legend />
        {rows.map((row, index) => <Bar key={row.model_key} dataKey={row.model} fill={colors[index]} radius={[4, 4, 0, 0]} />)}
      </BarChart>
    </ResponsiveContainer>
  </div>
}

export function CurveChart({ models, kind }: { models: ModelCurve[]; kind: 'roc' | 'precision_recall' }) {
  const label = kind === 'roc' ? 'ROC крива' : 'Precision–Recall крива'
  return <div className="chart" aria-label={label}>
    <h3>{label}</h3>
    <ResponsiveContainer width="100%" height={300}>
      <LineChart margin={{ left: 0, right: 20, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" dataKey="x" domain={[0, 1]} tick={{ fontSize: 12 }} />
        <YAxis type="number" dataKey="y" domain={[0, 1]} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value) => Number(value).toFixed(3)} />
        <Legend />
        {models.map((model, index) => <Line
          key={model.model_key}
          data={model[kind]}
          dataKey="y"
          name={model.model}
          stroke={colors[index]}
          dot={false}
          strokeWidth={2}
          isAnimationActive={false}
        />)}
      </LineChart>
    </ResponsiveContainer>
  </div>
}

export function StabilityChart({ rows }: { rows: FeatureStability[] }) {
  const data = [...rows].reverse().map(row => ({
    name: row.gene_symbol || row.probe_id,
    frequency: row.selection_frequency,
  }))
  return <div className="chart" aria-label="Честота на избор на характеристики">
    <ResponsiveContainer width="100%" height={Math.max(300, rows.length * 28)}>
      <BarChart data={data} layout="vertical" margin={{ left: 28, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} />
        <YAxis type="category" dataKey="name" width={92} tick={{ fontSize: 11 }} />
        <Tooltip formatter={(value) => Number(value).toFixed(2)} />
        <Bar dataKey="frequency" name="Честота" radius={[0, 4, 4, 0]}>
          {data.map((_, index) => <Cell key={index} fill={index % 2 ? '#75a39a' : '#247d78'} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </div>
}
