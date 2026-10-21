import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import AgentForm from './AgentForm';
import storageService, { STORAGE_KEYS, ConfigItem } from '../../services/storageService';
import configService from '../../services/configService';
import { AgentsConfig } from '../../types/config';

const AgentList: React.FC = () => {
  const [agents, setAgents] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<ConfigItem | null>(null);
  const [formValues, setFormValues] = useState<Partial<AgentsConfig>>({});
  const [metaForm] = Form.useForm();

  // Load agent configurations
  const loadAgents = async () => {
    setLoading(true);
    try {
      const data = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.AGENTS);
      setAgents(data);
    } catch (error) {
      message.error('加载智能体配置失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Initialize data
  useEffect(() => {
    const init = async () => {
      await storageService.initializeExampleData();
      await loadAgents();
    };
    init();
  }, []);

  // Handle search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
  };

  // Filter agents based on search text
  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchText.toLowerCase()) ||
    (agent.description && agent.description.toLowerCase().includes(searchText.toLowerCase()))
  );

  // Handle create new agent
  const handleCreate = () => {
    setCurrentAgent(null);
    // Create a basic agent config based on config.json structure
    setFormValues({
      citizens: [
        {
          agent_class: 'citizen',
          number: 10,
          memory_config_func: null,
          memory_distributions: null
        }
      ],
      firms: [
        {
          agent_class: 'firm',
          number: 5,
          memory_config_func: null,
          memory_distributions: null
        }
      ],
      governments: [
        {
          agent_class: 'government',
          number: 1,
          memory_config_func: null,
          memory_distributions: null
        }
      ],
      banks: [
        {
          agent_class: 'bank',
          number: 1,
          memory_config_func: null,
          memory_distributions: null
        }
      ],
      nbs: [
        {
          agent_class: 'nbs',
          number: 1,
          memory_config_func: null,
          memory_distributions: null
        }
      ]
    });
    metaForm.setFieldsValue({
      name: `智能体配置 ${agents.length + 1}`,
      description: ''
    });
    setIsModalVisible(true);
  };

  // Handle edit agent
  const handleEdit = (agent: ConfigItem) => {
    setCurrentAgent(agent);
    setFormValues(agent.config);
    metaForm.setFieldsValue({
      name: agent.name,
      description: agent.description
    });
    setIsModalVisible(true);
  };

  // Handle duplicate agent
  const handleDuplicate = (agent: ConfigItem) => {
    setCurrentAgent(null);
    setFormValues(agent.config);
    metaForm.setFieldsValue({
      name: `${agent.name}（副本）`,
      description: agent.description
    });
    setIsModalVisible(true);
  };

  // Handle delete agent
  const handleDelete = async (id: string) => {
    try {
      await storageService.deleteConfig(STORAGE_KEYS.AGENTS, id);
      message.success('智能体配置已删除');
      loadAgents();
    } catch (error) {
      message.error('删除智能体配置失败');
      console.error(error);
    }
  };

  // Handle export agent
  const handleExport = (agent: ConfigItem) => {
    const dataStr = JSON.stringify(agent, null, 2);
    const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;

    const exportFileDefaultName = `${agent.name.replace(/\s+/g, '_')}_agent.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  // Handle modal OK
  const handleModalOk = async () => {
    try {
      // Validate meta form
      const metaValues = await metaForm.validateFields();

      const configData: ConfigItem = {
        id: currentAgent?.id || `agent_${Date.now()}`,
        name: metaValues.name,
        description: metaValues.description || '',
        config: formValues,
        createdAt: currentAgent?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      await storageService.saveConfig(STORAGE_KEYS.AGENTS, configData);

      message.success(currentAgent ? '智能体配置已更新' : '智能体配置已创建');
      setIsModalVisible(false);
      loadAgents();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // Handle modal cancel
  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  // Table columns
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      sorter: (a: ConfigItem, b: ConfigItem) => a.name.localeCompare(b.name)
    },
    {
      title: '说明',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '最后更新',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      render: (text: string) => new Date(text).toLocaleString(),
      sorter: (a: ConfigItem, b: ConfigItem) => new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: ConfigItem) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
          </Tooltip>
          <Tooltip title="复制">
            <Button icon={<CopyOutlined />} size="small" onClick={() => handleDuplicate(record)} />
          </Tooltip>
          <Tooltip title="导出">
            <Button icon={<ExportOutlined />} size="small" onClick={() => handleExport(record)} />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定删除该智能体配置吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button icon={<DeleteOutlined />} size="small" danger />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <Card
      title="智能体配置"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建</Button>}
    >
      <Input.Search
        placeholder="搜索智能体配置"
        onChange={handleSearch}
        style={{ marginBottom: 16 }}
      />

      <Table
        columns={columns}
        dataSource={filteredAgents}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={currentAgent ? "编辑智能体配置" : "新建智能体配置"}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={800}
        destroyOnClose
      >
        <Card title="配置信息" style={{ marginBottom: 16 }}>
          <Form
            form={metaForm}
            layout="vertical"
          >
            <Form.Item
              name="name"
              label="名称"
              rules={[{ required: true, message: '请输入配置名称' }]}
            >
              <Input placeholder="请输入配置名称" />
            </Form.Item>
            <Form.Item
              name="description"
              label="说明"
            >
              <Input.TextArea
                rows={2}
                placeholder="请输入配置说明"
              />
            </Form.Item>
          </Form>
        </Card>

        <Card title="智能体参数">
          <AgentForm
            value={formValues}
            onChange={(newValues) => setFormValues(newValues)}
          />
        </Card>
      </Modal>
    </Card>
  );
};

export default AgentList; 
