import React, { useState, useEffect } from 'react';
import { Card, Button, Select, Space, Typography, Divider, message, Row, Col, Spin, Form, Input } from 'antd';
import { useNavigate } from 'react-router-dom';
import { ExperimentOutlined, ApiOutlined, TeamOutlined, GlobalOutlined, RocketOutlined, NodeIndexOutlined } from '@ant-design/icons';
import storageService, { STORAGE_KEYS, ConfigItem } from '../../services/storageService';
import configService from '../../services/configService';

const { Text } = Typography;
const { Option } = Select;

// Add these interfaces at the top of the file
interface LLMConfig {
  provider?: string;
  model?: string;
  api_key?: string;
  base_url?: string;
}

interface WorkflowConfig extends ConfigItem {
  config: {
    llm?: LLMConfig;
    [key: string]: any;
  }
}

const CreateExperiment: React.FC = () => {
  // State declarations
  const [llms, setLLMs] = useState<ConfigItem[]>([]);
  const [agents, setAgents] = useState<ConfigItem[]>([]);
  const [workflows, setWorkflows] = useState<ConfigItem[]>([]);
  const [maps, setMaps] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState<string>('');
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('');
  const [selectedMap, setSelectedMap] = useState<string>('');
  const [experimentName, setExperimentName] = useState<string>('');
  const [experimentRunning, setExperimentRunning] = useState(false);
  const [experimentId, setExperimentId] = useState<string | null>(null);
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);
  const [experimentStatus, setExperimentStatus] = useState<string | null>(null);
  const navigate = useNavigate();
  const [form] = Form.useForm();

  // Load all configurations
  useEffect(() => {
    const loadConfigurations = async () => {
      setLoading(true);
      try {
        // Initialize example data
        await storageService.initializeExampleData();

        // Load all configurations
        const llmConfigs = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.LLMS);
        const agts = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.AGENTS);
        const wkfs = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.WORKFLOWS);
        const mps = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.MAPS);

        setLLMs(llmConfigs);
        setAgents(agts);
        setWorkflows(wkfs);
        setMaps(mps);

        // Set defaults if available
        if (llmConfigs.length > 0) setSelectedLLM(llmConfigs[0].id);
        if (agts.length > 0) setSelectedAgent(agts[0].id);
        if (wkfs.length > 0) setSelectedWorkflow(wkfs[0].id);
        if (mps.length > 0) setSelectedMap(mps[0].id);
      } catch (error) {
        message.error('加载配置失败');
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    loadConfigurations();
  }, []);

  // Clean up interval timer
  useEffect(() => {
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, [statusCheckInterval]);

  // Handle navigation to create new configuration pages
  const handleCreateNew = (type: 'llm' | 'agent' | 'workflow' | 'map') => {
    switch (type) {
      case 'llm':
        navigate('/llms');
        break;
      case 'agent':
        navigate('/agents');
        break;
      case 'workflow':
        navigate('/workflows');
        break;
      case 'map':
        navigate('/maps');
        break;
    }
  };

  // Render option content with name and description
  const renderOptionContent = (item: ConfigItem) => (
    <div>
      <div>{item.name}</div>
      {item.description && <Text type="secondary">{item.description}</Text>}
    </div>
  );

  // Handle form submission to start experiment
  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Validate form
      await form.validateFields();

      // Build configuration from selected components
      const config = await configService.buildExperimentConfig(
        selectedLLM,
        selectedAgent,
        selectedWorkflow,
        selectedMap,
        experimentName
      );

      console.log(config);

      if (!config) {
        throw new Error('生成实验配置失败');
      }

      // Send request to start experiment
      const response = await fetch('/api/run-experiments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '启动实验失败');
      }

      const data = await response.json();
      const newExperimentId = data.data.id;

      setExperimentId(newExperimentId);
      setExperimentRunning(true);
      message.success(`实验已启动，实验 ID：${newExperimentId}`);

      // Navigate to experiment details after a short delay
      setTimeout(() => {
        navigate(`/console`);
      }, 2000);
    } catch (error) {
      message.error(`启动实验失败：${error.message}`);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        experimentName: '',
      }}
    >
      <Card title="新建实验" extra={
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          disabled={experimentRunning}
        >
          启动实验
        </Button>
      }>
        <Form.Item
          name="experimentName"
          label="实验名称"
          rules={[{ required: true, message: '请输入实验名称' }]}
        >
          <Input
            placeholder="请输入实验名称"
            onChange={(e) => setExperimentName(e.target.value)}
            disabled={experimentRunning}
          />
        </Form.Item>

        <Divider orientation="left">配置组件</Divider>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card
              title={<Space><ApiOutlined /> LLM</Space>}
              extra={<Button type="link" onClick={() => handleCreateNew('llm')}>新建</Button>}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text>选择大模型配置：</Text>
                <Form.Item
                  name="llm"
                  rules={[{ required: true, message: '请选择大模型配置' }]}
                  initialValue={selectedLLM}
                >
                  <Select
                    placeholder="选择大模型"
                    style={{ width: '100%' }}
                    loading={loading}
                    value={selectedLLM || undefined}
                    onChange={setSelectedLLM}
                    optionLabelProp="label"
                    disabled={experimentRunning}
                  >
                    {llms.map(llm => (
                      <Option key={llm.id} value={llm.id} label={llm.name}>
                        {renderOptionContent(llm)}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Space>
            </Card>
          </Col>

          <Col span={12}>
            <Card
              title={<Space><GlobalOutlined /> 地图</Space>}
              extra={<Button type="link" onClick={() => handleCreateNew('map')}>新建</Button>}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text>选择地图：</Text>
                <Form.Item
                  name="map"
                  rules={[{ required: true, message: '请选择地图' }]}
                  initialValue={selectedMap}
                >
                  <Select
                    placeholder="选择地图"
                    style={{ width: '100%' }}
                    loading={loading}
                    value={selectedMap || undefined}
                    onChange={setSelectedMap}
                    optionLabelProp="label"
                    disabled={experimentRunning}
                  >
                    {maps.map(map => (
                      <Option key={map.id} value={map.id} label={map.name}>
                        {renderOptionContent(map)}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Space>
            </Card>
          </Col>

          <Col span={12}>
            <Card
              title={<Space><TeamOutlined /> 智能体</Space>}
              extra={<Button type="link" onClick={() => handleCreateNew('agent')}>新建</Button>}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text>选择智能体配置：</Text>
                <Form.Item
                  name="agent"
                  rules={[{ required: true, message: '请选择智能体配置' }]}
                  initialValue={selectedAgent}
                >
                  <Select
                    placeholder="选择智能体"
                    style={{ width: '100%' }}
                    loading={loading}
                    value={selectedAgent || undefined}
                    onChange={setSelectedAgent}
                    optionLabelProp="label"
                    disabled={experimentRunning}
                  >
                    {agents.map(agent => (
                      <Option key={agent.id} value={agent.id} label={agent.name}>
                        {renderOptionContent(agent)}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Space>
            </Card>
          </Col>

          <Col span={12}>
            <Card
              title={<Space><NodeIndexOutlined /> 工作流</Space>}
              extra={<Button type="link" onClick={() => handleCreateNew('workflow')}>新建</Button>}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text>选择工作流：</Text>
                <Form.Item
                  name="workflow"
                  rules={[{ required: true, message: '请选择工作流' }]}
                  initialValue={selectedWorkflow}
                >
                  <Select
                    placeholder="选择工作流"
                    style={{ width: '100%' }}
                    loading={loading}
                    value={selectedWorkflow || undefined}
                    onChange={setSelectedWorkflow}
                    optionLabelProp="label"
                    disabled={experimentRunning}
                  >
                    {workflows.map(workflow => (
                      <Option key={workflow.id} value={workflow.id} label={workflow.name}>
                        {renderOptionContent(workflow)}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Space>
            </Card>
          </Col>
        </Row>

        <Divider />

        {experimentRunning && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Spin />
            <div style={{ marginTop: 8 }}>
              <Text>实验正在运行，状态：{experimentStatus || '启动中…'}</Text>
            </div>
          </div>
        )}
      </Card>
    </Form>
  );
};

export default CreateExperiment; 
