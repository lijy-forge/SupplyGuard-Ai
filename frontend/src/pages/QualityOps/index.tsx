import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Collapse,
  Descriptions,
  Empty,
  Input,
  Progress,
  Row,
  Space,
  Steps,
  Tag,
  Timeline,
  Typography,
  message,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

type EvidenceType = 'STRUCTURED' | 'GRAPH' | 'DOCUMENT';
type RunMode = 'live' | 'offline';
type Decision = 'approved' | 'rejected' | null;

interface EvidenceItem {
  source_type: EvidenceType;
  source_id: string;
  claim: string;
  payload: Record<string, unknown>;
}

interface AgentRun {
  evidence: EvidenceItem[];
  answer?: string;
  proposed_action?: {
    actionType?: string;
    description?: string;
  };
  correlation_id?: string;
  action_result?: Record<string, unknown>;
}

const sourceLabels: Record<EvidenceType, string> = {
  STRUCTURED: '业务数据',
  GRAPH: '产业链图谱',
  DOCUMENT: '规范文档',
};

const sourceColors: Record<EvidenceType, string> = {
  STRUCTURED: 'blue',
  GRAPH: 'purple',
  DOCUMENT: 'cyan',
};

const offlineEvidence: EvidenceItem[] = [
  {
    source_type: 'STRUCTURED',
    source_id: 'BATCH-001',
    claim: '批次已隔离，并关联一条不合格安全检验记录。',
    payload: { batch_number: 'BATCH-001', part_number: 'PART-001', supplier_code: 'SUP-001', disposition: 'QUARANTINED' },
  },
  {
    source_type: 'STRUCTURED',
    source_id: 'CASE-001',
    claim: '当前 P0 质量案例处于待处置状态。',
    payload: { case_number: 'CASE-001', priority: 'P0', status: 'OPEN', owner: 'quality.lead' },
  },
  {
    source_type: 'GRAPH',
    source_id: 'PART-001',
    claim: '图谱显示该零件影响 VM-A、VM-B 两个车型平台。',
    payload: { vehicle_models: ['VM-A', 'VM-B'], supplier_dependencies: ['SUP-001'], downstream_plants: 2 },
  },
  {
    source_type: 'DOCUMENT',
    source_id: 'SOP-QA-017',
    claim: '遏制规范要求隔离库存、通知供应商，并在 24 小时内提交 8D 报告。',
    payload: { document: 'SOP-QA-017', section: '4.2 供应商遏制', version: '2026.1' },
  },
];

const offlineRun: AgentRun = {
  evidence: offlineEvidence,
  answer: '现有体验数据支持立即执行批次遏制，并同步核查两个受影响车型平台。',
  proposed_action: {
    actionType: 'SUPPLIER_CONTAINMENT',
    description: '隔离库存、通知供应商，并要求其在 24 小时内提交 8D 报告。',
  },
  correlation_id: 'offline-preview',
};

function translateClaim(claim: string) {
  const translations: Record<string, string> = {
    'Batch is quarantined and linked to a failed inspection.': '批次已隔离，并关联一条不合格检验记录。',
    'An open P0 quality case governs containment.': '当前 P0 质量案例处于待遏制状态。',
    'Vehicle-model, batch, and supplier dependency impact is derived from the graph.': '已从图谱检索车型、批次和供应商依赖影响。',
    'Containment SOP requires quarantine, supplier notification and 8D.': '遏制规范要求隔离库存、通知供应商并提交 8D 报告。',
  };
  return translations[claim] || claim;
}

function formatPayload(payload: Record<string, unknown>) {
  return JSON.stringify(payload, null, 2);
}

export default function QualityOps() {
  const [task, setTask] = useState('评估 BATCH-001 的影响范围，并给出供应商遏制建议');
  const [serviceStatus, setServiceStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [running, setRunning] = useState(false);
  const [approving, setApproving] = useState(false);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [mode, setMode] = useState<RunMode | null>(null);
  const [decision, setDecision] = useState<Decision>(null);
  const [threadId, setThreadId] = useState('');
  const [finishedAt, setFinishedAt] = useState('');
  const [requestError, setRequestError] = useState('');

  useEffect(() => {
    fetch('/agent-api/health')
      .then((response) => {
        if (!response.ok) throw new Error('服务未就绪');
        setServiceStatus('online');
      })
      .catch(() => setServiceStatus('offline'));
  }, []);

  const evidence = useMemo(() => run?.evidence || [], [run]);
  const evidenceKinds = useMemo(() => new Set(evidence.map((item) => item.source_type)), [evidence]);
  const completedCount = run ? 5 : running ? 1 : 0;
  const progress = decision ? 100 : Math.round((completedCount / 6) * 100);

  const stageItems = [
    { title: '提交调查任务', done: running || !!run, description: running ? '智能体服务正在处理请求' : run ? '请求已受理' : '等待提交' },
    { title: '查询业务数据', done: evidenceKinds.has('STRUCTURED'), description: evidenceKinds.has('STRUCTURED') ? '已返回批次与质量案例证据' : '等待服务返回' },
    { title: '检索产业链图谱', done: evidenceKinds.has('GRAPH'), description: evidenceKinds.has('GRAPH') ? '已返回影响关系证据' : '等待服务返回' },
    { title: '检索质量规范', done: evidenceKinds.has('DOCUMENT'), description: evidenceKinds.has('DOCUMENT') ? '已返回规范文档证据' : '等待服务返回' },
    { title: '生成处置建议', done: !!run?.proposed_action, description: run?.proposed_action ? '建议已生成' : '等待证据汇总' },
    { title: '人工审批', done: decision !== null, description: decision === 'approved' ? '已批准' : decision === 'rejected' ? '已驳回' : run ? '等待负责人决策' : '尚未开始' },
  ];

  const submitRun = async () => {
    if (running || !task.trim()) return;
    const newThreadId = `quality-${Date.now()}`;
    setRunning(true);
    setRun(null);
    setMode(null);
    setDecision(null);
    setRequestError('');
    setThreadId(newThreadId);
    setFinishedAt('');

    try {
      const response = await fetch('/agent-api/api/v1/agent/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: task,
          thread_id: newThreadId,
          case_number: 'CASE-001',
          part_number: 'PART-001',
          batch_number: 'BATCH-001',
        }),
      });
      if (!response.ok) throw new Error(`智能体服务返回 ${response.status}`);
      const data = await response.json() as AgentRun;
      setRun(data);
      setMode('live');
      setServiceStatus('online');
      setFinishedAt(new Date().toLocaleString('zh-CN'));
    } catch (error) {
      setServiceStatus('offline');
      setRequestError(error instanceof Error ? error.message : '智能体服务不可用');
    } finally {
      setRunning(false);
    }
  };

  const loadOfflinePreview = () => {
    setRun(offlineRun);
    setMode('offline');
    setDecision(null);
    setThreadId('offline-preview');
    setFinishedAt(new Date().toLocaleString('zh-CN'));
    setRequestError('');
  };

  const submitDecision = async (approved: boolean) => {
    if (!run || decision || approving) return;
    if (mode === 'offline') {
      setDecision(approved ? 'approved' : 'rejected');
      message.info('这是离线体验数据，本次决策不会写入业务系统。');
      return;
    }

    setApproving(true);
    try {
      const response = await fetch('/agent-api/api/v1/agent/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: threadId,
          approved,
          actor: 'quality.lead',
          reason: approved ? '证据已核验，同意执行。' : '证据不足，退回补充分析。',
        }),
      });
      if (!response.ok) throw new Error(`审批服务返回 ${response.status}`);
      const data = await response.json() as AgentRun;
      setRun((current) => ({ ...(current || { evidence: [] }), ...data }));
      setDecision(approved ? 'approved' : 'rejected');
      message.success(approved ? '审批已写入业务系统' : '驳回决定已记录');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '审批提交失败');
    } finally {
      setApproving(false);
    }
  };

  return (
    <div style={{ maxWidth: 1440, margin: '0 auto', padding: 24 }}>
      <Space direction="vertical" size={20} style={{ width: '100%' }}>
        <div>
          <Space wrap>
            <Tag color="red">P0 严重质量事件</Tag>
            <Tag color="blue">CASE-001</Tag>
            <Tag color={serviceStatus === 'online' ? 'green' : serviceStatus === 'checking' ? 'processing' : 'orange'} icon={<CloudServerOutlined />}>
              {serviceStatus === 'online' ? '智能体服务已连接' : serviceStatus === 'checking' ? '正在检查服务' : '智能体服务未连接'}
            </Tag>
            {mode === 'offline' && <Tag color="gold">离线体验数据</Tag>}
          </Space>
          <Title level={2} style={{ margin: '12px 0 4px' }}>质量异常处置智能体</Title>
          <Paragraph type="secondary" style={{ margin: 0 }}>
            证据来自业务 API、产业链图谱和规范文档；只有人工批准后，系统才会创建正式纠正措施。
          </Paragraph>
        </div>

        <Card>
          <Row gutter={[20, 20]} align="middle">
            <Col xs={24} lg={17}>
              <Text strong>调查任务</Text>
              <Input size="large" prefix={<SearchOutlined />} value={task} onChange={(event) => setTask(event.target.value)} onPressEnter={submitRun} style={{ marginTop: 10 }} />
            </Col>
            <Col xs={24} lg={7}>
              <Button type="primary" size="large" block loading={running} onClick={submitRun} icon={<FileSearchOutlined />}>
                {running ? '等待智能体返回' : run && mode === 'live' ? '重新调查' : '运行真实调查'}
              </Button>
            </Col>
          </Row>
          {(running || run) && <Progress percent={progress} status={running ? 'active' : decision ? 'success' : 'normal'} style={{ marginTop: 18 }} />}
          {requestError && (
            <Alert
              style={{ marginTop: 16 }}
              type="warning"
              showIcon
              message="真实智能体服务当前不可用"
              description={<Space wrap><span>{requestError}。可以启动完整服务后重试，或加载明确标记的离线体验数据查看界面流程。</span><Button onClick={loadOfflinePreview}>加载离线体验数据</Button></Space>}
            />
          )}
        </Card>

        <Row gutter={[20, 20]}>
          <Col xs={24} xl={8}>
            <Card title="执行状态" extra={mode && <Tag color={mode === 'live' ? 'green' : 'gold'}>{mode === 'live' ? '实时结果' : '离线体验'}</Tag>} style={{ height: '100%' }}>
              <Steps
                direction="vertical"
                size="small"
                current={stageItems.findIndex((item) => !item.done) === -1 ? stageItems.length : stageItems.findIndex((item) => !item.done)}
                status={requestError ? 'error' : 'process'}
                items={stageItems.map((item) => ({ title: item.title, description: item.description, status: item.done ? 'finish' : undefined }))}
              />
              {threadId && <Text type="secondary" copyable>运行编号：{threadId}</Text>}
            </Card>
          </Col>

          <Col xs={24} xl={16}>
            <Card title="调查结论" style={{ height: '100%' }}>
              {run ? (
                <>
                  <Descriptions bordered size="small" column={{ xs: 1, md: 2 }}>
                    <Descriptions.Item label="质量案例">CASE-001</Descriptions.Item>
                    <Descriptions.Item label="批次">BATCH-001</Descriptions.Item>
                    <Descriptions.Item label="零件">PART-001</Descriptions.Item>
                    <Descriptions.Item label="证据数量">{evidence.length} 条</Descriptions.Item>
                    <Descriptions.Item label="数据模式">{mode === 'live' ? '实时服务返回' : '离线体验数据，不代表真实业务状态'}</Descriptions.Item>
                    <Descriptions.Item label="完成时间">{finishedAt}</Descriptions.Item>
                  </Descriptions>
                  <Alert style={{ marginTop: 16 }} type="warning" showIcon message="智能体结论" description={run.answer || '证据支持立即启动批次遏制，等待负责人审批。'} />
                </>
              ) : <Empty description="运行调查后，这里会显示由服务返回的结论、证据数量和追踪信息。" />}
            </Card>
          </Col>
        </Row>

        <Row gutter={[20, 20]}>
          <Col xs={24} xl={13}>
            <Card title="证据台账" extra={<Space><DatabaseOutlined /><Tag>{evidence.length} 条</Tag></Space>} style={{ height: '100%' }}>
              {evidence.length ? (
                <Timeline
                  items={evidence.map((item, index) => ({
                    color: 'green',
                    children: (
                      <div>
                        <Space wrap><Tag color={sourceColors[item.source_type]}>{sourceLabels[item.source_type]}</Tag><Text strong>{item.source_id}</Text><Text type="secondary">证据 {index + 1}</Text></Space>
                        <Paragraph style={{ margin: '8px 0' }}>{translateClaim(item.claim)}</Paragraph>
                        <Collapse ghost size="small" items={[{ key: 'detail', label: '查看来源数据', children: <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: 260, overflow: 'auto', background: '#f6f8fa', padding: 12, borderRadius: 8 }}>{formatPayload(item.payload)}</pre> }]} />
                      </div>
                    ),
                  }))}
                />
              ) : <Empty description="尚无证据。系统不会在调查完成前预先展示固定结论。" />}
            </Card>
          </Col>

          <Col xs={24} xl={11}>
            <Card title="处置建议与人工审批" style={{ height: '100%' }}>
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Alert
                  type={decision === 'approved' ? 'success' : decision === 'rejected' ? 'error' : run ? 'warning' : 'info'}
                  showIcon
                  message={decision === 'approved' ? (mode === 'live' ? '方案已批准并写入业务系统' : '离线体验：方案已标记为批准') : decision === 'rejected' ? '方案已驳回' : run ? '等待质量负责人审批' : '尚未生成处置建议'}
                />
                <Card size="small" title="建议措施">
                  {run?.proposed_action?.description || <Text type="secondary">智能体完成证据检索后，建议措施才会出现在这里。</Text>}
                </Card>
                {mode === 'offline' && <Alert type="info" showIcon message="离线体验不会调用审批接口，也不会创建纠正措施。" />}
                <Space wrap>
                  <Button type="primary" icon={<CheckCircleOutlined />} loading={approving} disabled={!run || decision !== null} onClick={() => submitDecision(true)}>
                    {mode === 'offline' ? '体验批准流程' : '批准并写入'}
                  </Button>
                  <Button danger icon={<CloseCircleOutlined />} loading={approving} disabled={!run || decision !== null} onClick={() => submitDecision(false)}>驳回方案</Button>
                  <Tag icon={<SafetyCertificateOutlined />} color="blue">人工审批后才允许产生业务写入</Tag>
                </Space>
              </Space>
            </Card>
          </Col>
        </Row>
      </Space>
    </div>
  );
}
