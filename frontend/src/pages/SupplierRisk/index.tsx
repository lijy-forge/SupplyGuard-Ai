import { useState } from 'react'
import { Alert, Button, Card, Collapse, Input, InputNumber, Select, Space, Table, Tag, Typography } from 'antd'

type Request = { part_number: string; current_supplier: string; case_number: string; required_units: number; max_lead_days: number }
type Row = { supplierCode: string; name: string; base_score: number; graph_penalty: number; risk_score: number; risk_level: string; exclusions: string[]; risk_factors?: string[] }
type Evidence = { id: string; source_type: string; status: string; retrieved_at: string; payload: Record<string, unknown> }
type Narrative = { source: 'llm' | 'template'; summary: string; key_risks: string[]; evidence_ids: string[]; fallback_reason: string | null }
type Result = { request: Request; assessments: Row[]; recommendations: Row[]; warnings: string[]; method: string; evidence: Evidence[]; analysis_status: string; explanation: string; scenario: { relaxed_max_lead_days: number; eligible_if_deadline_relaxed: string[] }; narrative?: Narrative }
type Review = { id: string; status: string; version: number; snapshot: Result; action_id: string | null; decision: unknown }
type Audit = { action: string; actor: string; result: string; created_at: string }
const prefix = '/agent-api/api/v1/supplier-risk'
async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(prefix + path, { method: body === undefined ? 'GET' : 'POST', headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(60000) })
  if (!response.ok) {
    let detail = ''
    try { const data = await response.json(); if (typeof data.detail === 'string') detail = data.detail } catch { /* proxy may return plain text */ }
    throw new Error(`请求失败 (${response.status}) ${detail || '请检查输入、证据与服务状态'}`)
  }
  return response.json()
}
export default function SupplierRisk() {
  const [part, setPart] = useState('PART-001')
  const [supplier, setSupplier] = useState('SUP-001')
  const [caseNumber, setCaseNumber] = useState('CASE-001')
  const [units, setUnits] = useState(4000)
  const [days, setDays] = useState(21)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<Result | null>(null)
  const [review, setReview] = useState<Review | null>(null)
  const [reviewId, setReviewId] = useState('')
  const [audit, setAudit] = useState<Audit[]>([])
  const [key, setKey] = useState('')
  const [selected, setSelected] = useState('')
  const [actor, setActor] = useState('')
  const [reason, setReason] = useState('')
  async function perform(action: () => Promise<void>) {
    setLoading(true); setError('')
    try { await action() } catch (e) { setError(e instanceof Error ? e.message : '服务不可用') }
    finally { setLoading(false) }
  }
  function show(value: Result) { setResult(value); setSelected(value.recommendations[0]?.supplierCode ?? '') }
  async function run() {
    setResult(null); setReview(null); setAudit([]); setKey(crypto.randomUUID())
    await perform(async () => show(await api<Result>('/assess', { part_number: part, current_supplier: supplier, case_number: caseNumber, required_units: units, max_lead_days: days })))
  }
  async function load(id: string) {
    const value = await api<Review>(`/reviews/${encodeURIComponent(id)}`)
    setReview(value); setReviewId(value.id); show(value.snapshot)
    setAudit(await api<Audit[]>(`/reviews/${encodeURIComponent(id)}/audit`))
  }
  async function save() {
    if (!result) return
    await perform(async () => {
      const value = await api<Review>('/reviews', { request_key: key, request: result.request })
      await load(value.id)
    })
  }
  async function decide(approved: boolean) {
    if (!review) return
    await perform(async () => {
      await api<Review>(`/reviews/${encodeURIComponent(review.id)}/decision`, { version: review.version, approved, supplier_code: selected, actor, reason })
      await load(review.id)
    })
  }
  return <Space direction="vertical" style={{ width: '100%', padding: 24 }}>
    <Typography.Title level={2}>供应链风险分析与供方切换评审</Typography.Title>
    <Alert type="info" message="当前种子数据均为虚构。图谱与规范资料共同支撑评估；证据缺失或演示资料不允许批准。批准仅生成评审任务，供货关系仍需正式资格和采购审核。" />
    <Card title="质量事件与评估条件"><Space wrap>
      <label>质量案例 <Input value={caseNumber} onChange={e => setCaseNumber(e.target.value)} /></label>
      <label>零件 <Input value={part} onChange={e => setPart(e.target.value)} /></label>
      <label>当前供方 <Input value={supplier} onChange={e => setSupplier(e.target.value)} /></label>
      <label>需求数量 <InputNumber min={1} max={10000000} value={units} onChange={v => setUnits(v ?? 4000)} /></label>
      <label>最大交期（天） <InputNumber min={1} max={365} value={days} onChange={v => setDays(v ?? 21)} /></label>
      <Button type="primary" loading={loading} onClick={run}>关联证据并评估</Button>
    </Space></Card>
    <Card title="恢复已保存的评审"><Space.Compact style={{ width: '100%' }}><Input aria-label="评审编号" placeholder="输入评审编号，可在刷新或服务重启后重新读取" value={reviewId} onChange={e => setReviewId(e.target.value)} /><Button disabled={!reviewId.trim() || loading} onClick={() => perform(() => load(reviewId.trim()))}>读取评审</Button></Space.Compact></Card>
    {error && <Alert type="error" message={error} />}
    {result && <>
      <Tag color={result.analysis_status === 'READY_FOR_REVIEW' ? 'green' : 'orange'}>{result.analysis_status === 'READY_FOR_REVIEW' ? '证据完整，可提交审核' : '证据不足或无可用供方，批准受阻'}</Tag>
      <Alert message={result.method} description={result.explanation} />
      {result.narrative && <Card title={<Space>风险说明<Tag color={result.narrative.source === 'llm' ? 'purple' : 'default'}>{result.narrative.source === 'llm' ? '大模型生成' : '规则模板'}</Tag></Space>}>
        <Typography.Paragraph>{result.narrative.summary}</Typography.Paragraph>
        {result.narrative.key_risks.length > 0 && <ul>{result.narrative.key_risks.map((r, i) => <li key={i}>{r}</li>)}</ul>}
        {result.narrative.evidence_ids.length > 0 && <Typography.Text type="secondary">引用证据：{result.narrative.evidence_ids.join('、')}</Typography.Text>}
        <Alert style={{ marginTop: 8 }} type="info" message="说明文字仅供阅读；评分、排除原因和推荐顺序均由规则计算，大模型不会改变推荐结果。" />
      </Card>}
      {result.warnings.map((w, i) => <Alert key={i} type="warning" message={w} />)}
      <Card title="风险看板"><Table rowKey="supplierCode" dataSource={result.assessments} pagination={false} scroll={{ x: 850 }} columns={[{ title: '供方', dataIndex: 'name' }, { title: '指标基础分', dataIndex: 'base_score' }, { title: '共同上游附加分', dataIndex: 'graph_penalty' }, { title: '综合风险（越低越好）', dataIndex: 'risk_score' }, { title: '等级', dataIndex: 'risk_level' }, { title: '限制与风险因素', render: (_, row) => [...row.exclusions, ...(row.risk_factors ?? [])].join('；') || '满足条件' }]} /></Card>
      <Card title="多源证据与影响范围"><Collapse items={result.evidence.map(e => ({ key: e.id, label: <Space><Tag>{e.source_type}</Tag><Tag color={e.status === 'AVAILABLE' ? 'green' : 'orange'}>{e.status}</Tag><span>{e.id}</span></Space>, children: <><Typography.Text>检索时间：{e.retrieved_at}</Typography.Text><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(e.payload, null, 2)}</pre></> }))} /></Card>
      <Card title="约束与情景对比"><p>当前符合条件：{result.recommendations.map(r => `${r.name} (${r.supplierCode})`).join('；') || '无，需要人工寻源'}</p><p>若交期放宽至 {result.scenario.relaxed_max_lead_days} 天，可用供方：{result.scenario.eligible_if_deadline_relaxed.join('、') || '无'}。此情景未应用到本次推荐。</p></Card>
      <Card title="持久化评审与人工决策"><Space direction="vertical" style={{ width: '100%' }}>
        <Button loading={loading} disabled={!!review || !key} onClick={save}>重新采集证据并保存评审快照</Button>
        {review && <>
          <Typography.Text copyable>{review.id}</Typography.Text><Tag>{review.status} · 版本 {review.version}</Tag>
          <Select aria-label="待审核供方" style={{ minWidth: 240 }} value={selected || undefined} options={result.recommendations.map(r => ({ value: r.supplierCode, label: r.name }))} onChange={setSelected} />
          <Input aria-label="审核人" placeholder="审核人（本地演示记录，尚无身份认证）" maxLength={100} value={actor} onChange={e => setActor(e.target.value)} />
          <Input.TextArea aria-label="审核意见" placeholder="审核理由，必填" maxLength={2000} value={reason} onChange={e => setReason(e.target.value)} />
          <Space><Button type="primary" disabled={loading || review.status !== 'PENDING_REVIEW' || !selected || !actor.trim() || !reason.trim()} onClick={() => decide(true)}>批准并创建切换评审任务</Button><Button danger disabled={loading || !['PENDING_REVIEW', 'NEEDS_EVIDENCE'].includes(review.status) || !actor.trim() || !reason.trim()} onClick={() => decide(false)}>驳回</Button></Space>
          {review.action_id && <Alert type="success" message={`已创建评审任务 ${review.action_id}，未改变供货关系`} />}
          <Collapse items={[{ key: 'audit', label: '评审审计记录', children: <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(audit, null, 2)}</pre> }]} />
        </>}
      </Space></Card>
    </>}
  </Space>
}
