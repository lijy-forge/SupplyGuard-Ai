import React, { useState } from 'react';
import { Form, Input, Card, Upload, Button, message } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import type { UploadProps, UploadFile } from 'antd';
import { MapConfig } from '../../types/config';

const { Dragger } = Upload;

interface MapFormProps {
  value: Partial<MapConfig>;
  onChange: (value: Partial<MapConfig>) => void;
}

const MapForm: React.FC<MapFormProps> = ({ value, onChange }) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // Update parent component state when form values change
  const handleValuesChange = (changedValues: any, allValues: any) => {
    onChange(allValues);
  };

  // Set initial values
  React.useEffect(() => {
    form.setFieldsValue(value);
  }, [form, value]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    action: '/api/upload-map',
    fileList,
    onChange(info) {
      let newFileList = [...info.fileList];
      
      // Just keep the latest file
      newFileList = newFileList.slice(-1);
      
      setFileList(newFileList);
      
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 上传成功`);
        // Update the form with the file path
        form.setFieldsValue({
          file_path: `maps/${info.file.name}`
        });
        handleValuesChange({ file_path: `maps/${info.file.name}` }, form.getFieldsValue());
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 上传失败。`);
      }
    },
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onValuesChange={handleValuesChange}
      initialValues={value}
    >
      <Card title="地图配置" bordered={false}>
        <Form.Item
          name="file_path"
          label="地图文件路径"
          rules={[{ required: true, message: '请输入地图文件路径或上传地图文件' }]}
        >
          <Input placeholder="请输入地图文件路径（例如 maps/default_map.pb）" />
        </Form.Item>
        
        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽地图文件至此处上传</p>
          <p className="ant-upload-hint">
            支持上传单个 .pb 文件，文件将保存至 maps 目录。
          </p>
        </Dragger>
        
        <Form.Item
          name="cache_path"
          label="缓存路径（可选）"
        >
          <Input placeholder="请输入缓存路径（可选）" />
        </Form.Item>
      </Card>
    </Form>
  );
};

export default MapForm; 
