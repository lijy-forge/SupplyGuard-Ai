import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Space, Modal, message, Tooltip, Input, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import MapForm from './MapForm';
import storageService, { STORAGE_KEYS, ConfigItem } from '../../services/storageService';
import configService from '../../services/configService';
import { MapConfig } from '../../types/config';

const MapList: React.FC = () => {
  const [maps, setMaps] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [currentMap, setCurrentMap] = useState<ConfigItem | null>(null);
  const [formValues, setFormValues] = useState<Partial<MapConfig>>({});
  const [metaForm] = Form.useForm();

  // Load map configurations
  const loadMaps = async () => {
    setLoading(true);
    try {
      const data = await storageService.getConfigs<ConfigItem>(STORAGE_KEYS.MAPS);
      setMaps(data);
    } catch (error) {
      message.error('加载地图配置失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Initialize data
  useEffect(() => {
    const init = async () => {
      await storageService.initializeExampleData();
      await loadMaps();
    };
    init();
  }, []);

  // Handle search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
  };

  // Filter maps based on search text
  const filteredMaps = maps.filter(map => 
    map.name.toLowerCase().includes(searchText.toLowerCase()) || 
    (map.description && map.description.toLowerCase().includes(searchText.toLowerCase()))
  );

  // Handle create new map
  const handleCreate = () => {
    setCurrentMap(null);
    // Create a basic map config based on config.json structure
    setFormValues({
      file_path: "maps/default_map.pb",
      cache_path: "maps/default_map.cache"
    });
    metaForm.setFieldsValue({
      name: `地图配置 ${maps.length + 1}`,
      description: ''
    });
    setIsModalVisible(true);
  };

  // Handle edit map
  const handleEdit = (map: ConfigItem) => {
    setCurrentMap(map);
    setFormValues(map.config);
    metaForm.setFieldsValue({
      name: map.name,
      description: map.description
    });
    setIsModalVisible(true);
  };

  // Handle delete map
  const handleDelete = async (id: string) => {
    try {
      await storageService.deleteConfig(STORAGE_KEYS.MAPS, id);
      message.success('地图配置已删除');
      loadMaps();
    } catch (error) {
      message.error('删除地图配置失败');
      console.error(error);
    }
  };

  // Handle modal OK
  const handleModalOk = async () => {
    try {
      // Validate meta form
      const metaValues = await metaForm.validateFields();
      
      const configData: ConfigItem = {
        id: currentMap?.id || `map_${Date.now()}`,
        name: metaValues.name,
        description: metaValues.description || '',
        config: formValues,
        createdAt: currentMap?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      await storageService.saveConfig(STORAGE_KEYS.MAPS, configData);
      
      message.success(currentMap ? '地图配置已更新' : '地图配置已创建');
      setIsModalVisible(false);
      loadMaps();
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
          <Tooltip title="查看关系图谱">
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              onClick={() => window.location.href = '/graph'} 
            />
          </Tooltip>
          <Tooltip title="查看产业链">
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              onClick={() => window.location.href = '/industry'} 
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定删除该地图配置吗？"
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
      title="地图配置" 
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建</Button>}
    >
      <Input.Search
        placeholder="搜索地图配置"
        onChange={handleSearch}
        style={{ marginBottom: 16 }}
      />
      
      <Table
        columns={columns}
        dataSource={filteredMaps}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={currentMap ? "编辑地图配置" : "新建地图配置"}
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
        
        <Card title="地图参数">
          <MapForm 
            value={formValues} 
            onChange={setFormValues}
          />
        </Card>
      </Modal>
    </Card>
  );
};

export default MapList;
