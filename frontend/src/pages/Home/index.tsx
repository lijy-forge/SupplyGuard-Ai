import React from 'react';
import { Alert, Button, Card, Col, Progress, Row, Space, Statistic, Tag, Typography } from 'antd';
import {
  ApartmentOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';

const { Title, Text, Paragraph } = Typography;

const modules = [
  {
    title: '质量异常处置',
    description: '从异常识别、证据检索到影响分析和人工审批，完成可审计的质量闭环。',
    icon: <SafetyCertificateOutlined />,
    path: '/quality',
    action: '进入处置中心',
    color: '#1677ff',
  },
  {
    title: '产业链影响分析',
    description: '查看企业、零件、交易和通信关系，快速识别异常的上下游影响范围。',
    icon: <ApartmentOutlined />,
    path: '/industry',
    action: '查看产业链图谱',
    color: '#13a8a8',
  },
  {
    title: '智能体仿真实验',
    description: '配置模型、智能体和工作流，用仿真实验验证供应链策略与处置方案。',
    icon: <ExperimentOutlined />,
    path: '/console',
    action: '打开实验控制台',
    color: '#722ed1',
  },
];

const usageSteps = [
  ['发现异常', '从质量事件进入处置中心，输入需要分析的问题。'],
  ['形成证据', '系统关联批次、零件、供应商、产业链和规范文档。'],
  ['人工决策', '质量负责人审核智能体建议，批准或驳回处置方案。'],
  ['仿真验证', '对重要方案创建实验，验证对库存、交付和成本的影响。'],
];

export default function HomePage() {
  return (
    <div style={{ width: '100%', maxWidth: 1440, margin: '0 auto', padding: '28px 24px 48px' }}>
      <Space direction="vertical" size={22} style={{ width: '100%' }}>
        <Card
          bordered={false}
          style={{
            overflow: 'hidden',
            background: 'linear-gradient(120deg, #061b3a 0%, #123f77 60%, #0e7490 100%)',
            boxShadow: '0 18px 50px rgba(16, 51, 92, 0.18)',
          }}
          bodyStyle={{ padding: '42px 44px' }}
        >
          <Row gutter={[32, 28]} align="middle">
            <Col xs={24} lg={16}>
              <Tag color="cyan" bordered={false}>SupplyGuard AI · 工厂运营智能体平台</Tag>
              <Title style={{ color: '#fff', margin: '16px 0 10px', fontSize: 42 }}>
                用可信证据驱动供应链质量决策
              </Title>
              <Paragraph style={{ color: 'rgba(255,255,255,.78)', fontSize: 17, maxWidth: 760 }}>
                为质量工程师、供应链负责人和工厂管理者提供异常处置、产业链追溯与智能体仿真能力。
                关键行动始终由人员审批，并完整保留决策依据。
              </Paragraph>
              <Space wrap size="middle">
                <Link to="/quality"><Button type="primary" size="large" icon={<ThunderboltOutlined />}>开始处理质量异常</Button></Link>
                <Link to="/console"><Button size="large">进入仿真实验</Button></Link>
              </Space>
            </Col>
            <Col xs={24} lg={8}>
              <Card size="small" style={{ background: 'rgba(255,255,255,.1)', borderColor: 'rgba(255,255,255,.18)' }}>
                <Space direction="vertical" size={14} style={{ width: '100%' }}>
                  <Text style={{ color: '#fff' }}>当前演示场景</Text>
                  <Title level={4} style={{ color: '#fff', margin: 0 }}>制动压力传感器批次异常</Title>
                  <Progress percent={100} strokeColor="#42e8ca" trailColor="rgba(255,255,255,.15)" />
                  <Text style={{ color: 'rgba(255,255,255,.72)' }}>结构化数据、产业链图谱和质量规范均已就绪</Text>
                </Space>
              </Card>
            </Col>
          </Row>
        </Card>

        <Alert
          showIcon
          type="info"
          message="建议使用顺序"
          description="首次体验请先进入“质量异常处置”，运行智能体并完成审批；然后查看产业链图谱，最后在实验控制台创建仿真实验。"
        />

        <Row gutter={[18, 18]}>
          {modules.map((item) => (
            <Col xs={24} lg={8} key={item.path}>
              <Card hoverable style={{ height: '100%' }}>
                <div style={{ fontSize: 30, color: item.color }}>{item.icon}</div>
                <Title level={4}>{item.title}</Title>
                <Paragraph type="secondary" style={{ minHeight: 66 }}>{item.description}</Paragraph>
                <Link to={item.path}><Button type="link" style={{ padding: 0 }}>{item.action} <ArrowRightOutlined /></Button></Link>
              </Card>
            </Col>
          ))}
        </Row>

        <Row gutter={[18, 18]}>
          <Col xs={24} xl={16}>
            <Card title="完整使用流程" style={{ height: '100%' }}>
              <Row gutter={[16, 16]}>
                {usageSteps.map(([title, description], index) => (
                  <Col xs={24} md={12} key={title}>
                    <div style={{ display: 'flex', gap: 12, padding: 14, background: '#f7f9fc', borderRadius: 10, height: '100%' }}>
                      <div style={{ width: 30, height: 30, borderRadius: 15, flex: '0 0 auto', background: '#1677ff', color: '#fff', display: 'grid', placeItems: 'center', fontWeight: 700 }}>{index + 1}</div>
                      <div><Text strong>{title}</Text><br /><Text type="secondary">{description}</Text></div>
                    </div>
                  </Col>
                ))}
              </Row>
            </Card>
          </Col>
          <Col xs={24} xl={8}>
            <Card title="平台状态" style={{ height: '100%' }}>
              <Row gutter={[12, 20]}>
                <Col span={12}><Statistic title="质量案例" value={1} suffix="个" /></Col>
                <Col span={12}><Statistic title="证据来源" value={3} suffix="类" /></Col>
                <Col span={12}><Statistic title="关键审批" value={1} suffix="项" /></Col>
                <Col span={12}><Statistic title="核心模块" value={3} suffix="个" /></Col>
              </Row>
              <Space style={{ marginTop: 20 }}><CheckCircleOutlined style={{ color: '#52c41a' }} /><Text>本地演示环境运行正常</Text></Space>
            </Card>
          </Col>
        </Row>
      </Space>
    </div>
  );
}
