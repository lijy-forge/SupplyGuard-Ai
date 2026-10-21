import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Card, Button } from 'antd';
import { PlusOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { Config, LLMConfig } from '../../types/config';
import { LLMProviderType } from '../../utils/enums';

interface LLMFormProps {
  value: Partial<Config> & { llm_configs?: LLMConfig[] };
  onChange: (value: Partial<Config> & { llm_configs?: LLMConfig[] }) => void;
}

// Define provider model options
const providerModels = {
  deepseek: [
    { value: 'deepseek-reasoner', label: 'DeepSeek-R1' },
    { value: 'deepseek-chat', label: 'DeepSeek-V3' },
  ],
  openai: [
    { value: 'gpt-4.5', label: 'GPT-4.5 Preview' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o mini' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  ],
  qwen: [
    { value: 'qwen-max', label: 'Qwen Max' },
    { value: 'qwen-plus', label: 'Qwen Plus' },
    { value: 'qwen-turbo', label: 'Qwen Turbo' },
    { value: 'qwen2.5-72b-instruct', label: 'qwen2.5-72b-instruct' },
    { value: 'qwen2.5-32b-instruct', label: 'qwen2.5-32b-instruct' },
    { value: 'qwen2.5-14b-instruct-1m', label: 'qwen2.5-14b-instruct-1m' },
    { value: 'qwen2.5-14b-instruct', label: 'qwen2.5-14b-instruct' },
    { value: 'qwen2.5-7b-instruct-1m', label: 'qwen2.5-7b-instruct-1m' },
    { value: 'qwen2.5-7b-instruct', label: 'qwen2.5-7b-instruct' },
    { value: 'qwen2-72b-instruct', label: 'qwen2-72b-instruct' },
    { value: 'qwen2-57b-a14b-instruct', label: 'qwen2-57b-a14b-instruct' },
    { value: 'qwen2-7b-instruct', label: 'qwen2-7b-instruct' },
  ],
  siliconflow: [
    { value: 'Pro/deepseek-ai/DeepSeek-V3', label: 'Pro/deepseek-ai/DeepSeek-V3' },
    { value: 'deepseek-ai/DeepSeek-V3', label: 'deepseek-ai/DeepSeek-V3' },
    { value: 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B', label: 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B' },
    { value: 'deepseek-ai/DeepSeek-R1-Distill-Qwen-14B', label: 'deepseek-ai/DeepSeek-R1-Distill-Qwen-14B' },
    { value: 'Qwen/QwQ-32B', label: 'Qwen/QwQ-32B' },
    { value: 'Qwen/QVQ-72B-Preview', label: 'Qwen/QVQ-72B-Preview' },
  ],
  zhipuai: [
    { value: 'glm-4-air', label: 'GLM-4-Air' },
    { value: 'glm-4-flash', label: 'GLM-4-Flash' },
    { value: 'glm-4-plus', label: 'GLM-4-Plus' },
  ],
};

const LLMForm: React.FC<LLMFormProps> = ({ value, onChange }) => {
  const [form] = Form.useForm();
  const [selectedProviders, setSelectedProviders] = useState<Record<number, LLMProviderType>>({});
  
  // Handle form value changes
  const handleValuesChange = (changedValues: any, allValues: any) => {
    // 获取表单中的 llm_configs 值
    const newConfigs = allValues.llm_configs || [];
    
    onChange({ ...value, llm_configs: newConfigs });

    // Track provider changes to update model options
    if (changedValues.llm_configs) {
      const newSelectedProviders: Record<number, LLMProviderType> = { ...selectedProviders };

      changedValues.llm_configs.forEach((config: Partial<LLMConfig>, index: number) => {
        if (config && config.provider !== undefined) {
          newSelectedProviders[index] = config.provider as LLMProviderType;
        }
      });

      setSelectedProviders(newSelectedProviders);
    }
  };

  // Set initial values
  useEffect(() => {
    form.setFieldsValue(value);

    // Initialize selected providers from value
    if (value.llm_configs && Array.isArray(value.llm_configs)) {
      const initialProviders: Record<number, LLMProviderType> = {};
      value.llm_configs.forEach((config, index) => {
        if (config.provider) {
          initialProviders[index] = config.provider;
        }
      });
      setSelectedProviders(initialProviders);
    }
  }, [form, value]);

  return (
    <Form
      form={form}
      layout="vertical"
      onValuesChange={handleValuesChange}
      initialValues={value}
    >
      <Card bordered={false}>
        <Form.List name="llm_configs" initialValue={[{}]}>
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Card
                  key={key}
                  title={`大模型服务商 ${name + 1}`}
                  style={{ marginBottom: 16 }}
                  extra={
                    fields.length > 1 ?
                      <Button
                        type="text"
                        danger
                        icon={<MinusCircleOutlined />}
                        onClick={() => remove(name)}
                      /> : null
                  }
                >
                  <Form.Item
                    {...restField}
                    name={[name, 'provider']}
                    label="服务商"
                    rules={[{ required: true, message: '请选择服务商' }]}
                  >
                    <Select
                      placeholder="选择大模型服务商"
                      options={[
                        { value: LLMProviderType.OPENAI, label: 'OpenAI' },
                        { value: LLMProviderType.DEEPSEEK, label: 'DeepSeek' },
                        { value: LLMProviderType.QWEN, label: 'Qwen' },
                        { value: LLMProviderType.ZHIPUAI, label: 'ZhipuAI' },
                        { value: LLMProviderType.SILICONFLOW, label: 'SiliconFlow' },
                        { value: LLMProviderType.VLLM, label: 'vLLM' },
                      ]}
                      onChange={(value) => {
                        // Directly update the selectedProviders state when provider changes
                        setSelectedProviders(prev => ({
                          ...prev,
                          [name]: value
                        }));
                        
                        // Force re-render by updating a form field
                        // This ensures the conditional rendering is triggered
                        const currentConfigs = form.getFieldValue('llm_configs');
                        if (currentConfigs && currentConfigs[name]) {
                          // Clear the model field when switching providers
                          const updatedConfig = { ...currentConfigs[name], model: undefined };
                          const newConfigs = [...currentConfigs];
                          newConfigs[name] = updatedConfig;
                          form.setFieldsValue({ llm_configs: newConfigs });
                          onChange({ llm_configs: newConfigs });
                        }
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'base_url']}
                    label="基础地址（可选）"
                  >
                    <Input placeholder="如使用自定义服务地址，请在此输入" />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    name={[name, 'api_key']}
                    label="API 密钥"
                    rules={[{ required: true, message: '请输入 API 密钥' }]}
                  >
                    <Input.Password placeholder="请输入 API 密钥" />
                  </Form.Item>

                  {/* Model selection based on provider */}
                  {typeof selectedProviders[name] !== 'undefined' && 
                   selectedProviders[name].toString() === LLMProviderType.VLLM.toString() ? (
                    <Form.Item
                      {...restField}
                      name={[name, 'model']}
                      label="模型"
                      rules={[{ required: true, message: '请输入模型名称' }]}
                    >
                      <Input placeholder="请输入 vLLM 模型名称" />
                    </Form.Item>
                  ) : (
                    <Form.Item
                      {...restField}
                      name={[name, 'model']}
                      label="模型"
                      rules={[{ required: true, message: '请选择模型' }]}
                    >
                      <Select
                        placeholder="选择模型"
                        options={
                          selectedProviders[name] && providerModels[selectedProviders[name]]
                            ? providerModels[selectedProviders[name]]
                            : []
                        }
                      />
                    </Form.Item>
                  )}
                </Card>
              ))}
              <Form.Item>
                <Button
                  type="dashed"
                  onClick={() => add({})}
                  block
                  icon={<PlusOutlined />}
                >
                  添加大模型服务商
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>
      </Card>
    </Form>
  );
};

export default LLMForm;
