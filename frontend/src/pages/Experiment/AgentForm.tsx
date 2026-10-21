import React from 'react';
import { Form, Input, InputNumber, Select, Card, Tabs, Button } from 'antd';
import { AgentConfig, AgentsConfig } from '../../types/config';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;
const { Option } = Select;

interface AgentFormProps {
  value: Partial<AgentsConfig>;
  onChange: (value: Partial<AgentsConfig>) => void;
}

const AgentForm: React.FC<AgentFormProps> = ({ value, onChange }) => {
  const [form] = Form.useForm();

  // Define agent type options
  const agentClassOptions = [
    { label: '质量工程师', value: 'citizen' },
    { label: '供应商', value: 'firm' },
    { label: '工厂管理者', value: 'government' },
    { label: '物流节点', value: 'bank' },
    { label: '数据分析员', value: 'nbs' },
  ];

  // Update parent component state when form values change
  const handleValuesChange = (changedValues: any, allValues: any) => {
    // Transform form values to match the expected AgentsConfig structure
    const transformedValues = transformFormToAgentsConfig(allValues);
    onChange(transformedValues);
  };

  // Transform form data to AgentsConfig structure
  const transformFormToAgentsConfig = (formValues: any): Partial<AgentsConfig> => {
    const { citizenGroups = [], firmGroups = [], governmentGroups = [], bankGroups = [], nbsGroups = [] } = formValues;
    
    return {
      citizens: citizenGroups.map((group: any) => ({
        agent_class: 'citizen',
        number: group.number || 1,
        memory_config_func: group.memory_config_func || null,
        memory_distributions: group.memory_distributions || null
      })),
      firms: firmGroups.map((group: any) => ({
        agent_class: 'firm',
        number: group.number || 1,
        memory_config_func: group.memory_config_func || null,
        memory_distributions: group.memory_distributions || null
      })),
      governments: governmentGroups.map((group: any) => ({
        agent_class: 'government',
        number: group.number || 1,
        memory_config_func: group.memory_config_func || null,
        memory_distributions: group.memory_distributions || null
      })),
      banks: bankGroups.map((group: any) => ({
        agent_class: 'bank',
        number: group.number || 1,
        memory_config_func: group.memory_config_func || null,
        memory_distributions: group.memory_distributions || null
      })),
      nbs: nbsGroups.map((group: any) => ({
        agent_class: 'nbs',
        number: group.number || 1,
        memory_config_func: group.memory_config_func || null,
        memory_distributions: group.memory_distributions || null
      }))
    };
  };

  // Transform AgentsConfig to form structure
  const transformAgentsConfigToForm = (agentsConfig: Partial<AgentsConfig>) => {
    return {
      citizenGroups: agentsConfig.citizens?.map(agent => ({
        number: agent.number,
        memory_config_func: agent.memory_config_func,
        memory_distributions: agent.memory_distributions
      })) || [{ number: 10 }],
      firmGroups: agentsConfig.firms?.map(agent => ({
        number: agent.number,
        memory_config_func: agent.memory_config_func,
        memory_distributions: agent.memory_distributions
      })) || [{ number: 5 }],
      governmentGroups: agentsConfig.governments?.map(agent => ({
        number: agent.number,
        memory_config_func: agent.memory_config_func,
        memory_distributions: agent.memory_distributions
      })) || [{ number: 1 }],
      bankGroups: agentsConfig.banks?.map(agent => ({
        number: agent.number,
        memory_config_func: agent.memory_config_func,
        memory_distributions: agent.memory_distributions
      })) || [{ number: 1 }],
      nbsGroups: agentsConfig.nbs?.map(agent => ({
        number: agent.number,
        memory_config_func: agent.memory_config_func,
        memory_distributions: agent.memory_distributions
      })) || [{ number: 1 }]
    };
  };

  // Set initial values
  React.useEffect(() => {
    const formValues = transformAgentsConfigToForm(value);
    form.setFieldsValue(formValues);
  }, [form, value]);

  return (
    <Form
      form={form}
      layout="vertical"
      onValuesChange={handleValuesChange}
    >
      <Tabs defaultActiveKey="1">
        <TabPane tab="质量工程师" key="1">
          <Card bordered={false}>
            <Form.List name="citizenGroups" initialValue={[{ number: 10 }]}>
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card 
                      key={key} 
                      title={`质量工程师组 ${name + 1}`}
                      style={{ marginBottom: 16 }}
                      extra={
                        fields.length > 1 ? (
                          <MinusCircleOutlined onClick={() => remove(name)} />
                        ) : null
                      }
                    >
                      <Form.Item
                        {...restField}
                        name={[name, 'number']}
                        label="质量工程师数量"
                        rules={[{ required: true, message: '请输入质量工程师数量' }]}
                      >
                        <InputNumber min={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Card>
                  ))}
                  <Button 
                    type="dashed" 
                    onClick={() => add({ number: 10 })} 
                    block 
                    icon={<PlusOutlined />}
                  >
                    添加质量工程师组
                  </Button>
                </>
              )}
            </Form.List>
          </Card>
        </TabPane>

        <TabPane tab="供应商" key="2">
          <Card bordered={false}>
            <Form.List name="firmGroups" initialValue={[{ number: 5 }]}>
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card 
                      key={key} 
                      title={`供应商组 ${name + 1}`}
                      style={{ marginBottom: 16 }}
                      extra={
                        fields.length > 1 ? (
                          <MinusCircleOutlined onClick={() => remove(name)} />
                        ) : null
                      }
                    >
                      <Form.Item
                        {...restField}
                        name={[name, 'number']}
                        label="供应商数量"
                        rules={[{ required: true, message: '请输入供应商数量' }]}
                      >
                        <InputNumber min={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Card>
                  ))}
                  <Button 
                    type="dashed" 
                    onClick={() => add({ number: 5 })} 
                    block 
                    icon={<PlusOutlined />}
                  >
                    添加供应商组
                  </Button>
                </>
              )}
            </Form.List>
          </Card>
        </TabPane>

        <TabPane tab="工厂管理者" key="3">
          <Card bordered={false}>
            <Form.List name="governmentGroups" initialValue={[{ number: 1 }]}>
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card 
                      key={key} 
                      title={`工厂管理组 ${name + 1}`}
                      style={{ marginBottom: 16 }}
                      extra={
                        fields.length > 1 ? (
                          <MinusCircleOutlined onClick={() => remove(name)} />
                        ) : null
                      }
                    >
                      <Form.Item
                        {...restField}
                        name={[name, 'number']}
                        label="工厂管理者数量"
                        rules={[{ required: true, message: '请输入工厂管理者数量' }]}
                      >
                        <InputNumber min={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Card>
                  ))}
                  <Button 
                    type="dashed" 
                    onClick={() => add({ number: 1 })} 
                    block 
                    icon={<PlusOutlined />}
                  >
                    添加工厂管理组
                  </Button>
                </>
              )}
            </Form.List>
          </Card>
        </TabPane>

        <TabPane tab="物流节点" key="4">
          <Card bordered={false}>
            <Form.List name="bankGroups" initialValue={[{ number: 1 }]}>
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card 
                      key={key} 
                      title={`物流节点组 ${name + 1}`}
                      style={{ marginBottom: 16 }}
                      extra={
                        fields.length > 1 ? (
                          <MinusCircleOutlined onClick={() => remove(name)} />
                        ) : null
                      }
                    >
                      <Form.Item
                        {...restField}
                        name={[name, 'number']}
                        label="物流节点数量"
                        rules={[{ required: true, message: '请输入物流节点数量' }]}
                      >
                        <InputNumber min={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Card>
                  ))}
                  <Button 
                    type="dashed" 
                    onClick={() => add({ number: 1 })} 
                    block 
                    icon={<PlusOutlined />}
                  >
                    添加物流节点组
                  </Button>
                </>
              )}
            </Form.List>
          </Card>
        </TabPane>

        <TabPane tab="数据分析员" key="5">
          <Card bordered={false}>
            <Form.List name="nbsGroups" initialValue={[{ number: 1 }]}>
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card 
                      key={key} 
                      title={`数据分析员组 ${name + 1}`}
                      style={{ marginBottom: 16 }}
                      extra={
                        fields.length > 1 ? (
                          <MinusCircleOutlined onClick={() => remove(name)} />
                        ) : null
                      }
                    >
                      <Form.Item
                        {...restField}
                        name={[name, 'number']}
                        label="数据分析员数量"
                        rules={[{ required: true, message: '请输入数据分析员数量' }]}
                      >
                        <InputNumber min={1} style={{ width: '100%' }} />
                      </Form.Item>
                    </Card>
                  ))}
                  <Button 
                    type="dashed" 
                    onClick={() => add({ number: 1 })} 
                    block 
                    icon={<PlusOutlined />}
                  >
                    添加数据分析员组
                  </Button>
                </>
              )}
            </Form.List>
          </Card>
        </TabPane>
      </Tabs>
    </Form>
  );
};

export default AgentForm; 
