import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, ExportOutlined } from '@ant-design/icons';
import LLMForm from './LLMForm';
import storageService, { STORAGE_KEYS, ConfigItem } from '../../services/storageService';
import configService from '../../services/configService';
import { Config } from '../../types/config';

const LLMList: React.FC = () => {
  const [llms, setLLMs] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [currentLLM, setCurrentLLM] = useState<ConfigItem | null>(null);
  const [formValues, setFormValues] = useState<Partial<Config>>({});
  const [metaForm] = Form.useForm();

  // Load LLM configurations
  const loadLLMs = async () => {
    setLoading(true);
    try {
      const data = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.LLMS);
      setLLMs(data);
    } catch (error) {
      message.error('加载大模型配置失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Initialize data
  useEffect(() => {
    const init = async () => {
      await storageService.initializeExampleData();
      await loadLLMs();
    };
    init();
  }, []);

  // Handle search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
  };

  // Filter LLMs based on search text
  const filteredLLMs = llms.filter(llm => 
    llm.name.toLowerCase().includes(searchText.toLowerCase()) || 
    (llm.description && llm.description.toLowerCase().includes(searchText.toLowerCase()))
  );

  // Handle create new LLM
  const handleCreate = () => {
    setCurrentLLM(null);
    metaForm.setFieldsValue({
      name: `大模型配置 ${llms.length + 1}`,
      description: ''
    });
    setIsModalVisible(true);
  };

  // Handle edit LLM
  const handleEdit = (llm: ConfigItem) => {
    setCurrentLLM(llm);
    setFormValues(llm.config);
    metaForm.setFieldsValue({
      name: llm.name,
      description: llm.description
    });
    setIsModalVisible(true);
  };

  // Handle duplicate LLM
  const handleDuplicate = (llm: ConfigItem) => {
    setCurrentLLM(null);
    setFormValues(llm.config);
    metaForm.setFieldsValue({
      name: `${llm.name}（副本）`,
      description: llm.description
    });
    setIsModalVisible(true);
  };

  // Handle delete LLM
  const handleDelete = async (id: string) => {
    try {
      await storageService.deleteConfig(STORAGE_KEYS.LLMS, id);
      message.success('大模型配置已删除');
      loadLLMs();
    } catch (error) {
      message.error('删除大模型配置失败');
      console.error(error);
    }
  };

  // Handle export LLM
  const handleExport = (llm: ConfigItem) => {
    const dataStr = JSON.stringify(llm, null, 2);
    const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
    
    const exportFileDefaultName = `${llm.name.replace(/\s+/g, '_')}_llm.json`;
    
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
        id: currentLLM?.id || `llm_${Date.now()}`,
        name: metaValues.name,
        description: metaValues.description || '',
        config: formValues,
        createdAt: currentLLM?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      await storageService.saveConfig(STORAGE_KEYS.LLMS, configData);
      
      message.success(currentLLM ? '大模型配置已更新' : '大模型配置已创建');
      setIsModalVisible(false);
      loadLLMs();
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
              title="确定删除该大模型配置吗？"
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
      title="大模型配置" 
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建</Button>}
    >
      <Input.Search
        placeholder="搜索大模型配置"
        onChange={handleSearch}
        style={{ marginBottom: 16 }}
      />
      
      <Table
        columns={columns}
        dataSource={filteredLLMs}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={currentLLM ? "编辑大模型配置" : "新建大模型配置"}
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
        
        <Card title="大模型参数">
          <LLMForm 
            value={formValues} 
            onChange={setFormValues}
          />
        </Card>
      </Modal>
    </Card>
  );
};

export default LLMList;
