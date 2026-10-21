import {
  ApiOutlined,
  ApartmentOutlined,
  ExperimentOutlined,
  HomeOutlined,
  NodeIndexOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { Dropdown, Menu, MenuProps } from 'antd';
import type React from 'react';
import { Link } from 'react-router-dom';

const linkLabel = (to: string, icon: React.ReactNode, text: string) => (
  <Link to={to} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
    {icon}<span>{text}</span>
  </Link>
);

export default function RootMenu({ selectedKey }: { selectedKey: string }) {
  const experimentItems: MenuProps['items'] = [
    { key: '/console', label: linkLabel('/console', <ExperimentOutlined />, '实验控制台') },
    { key: '/create-experiment', label: linkLabel('/create-experiment', <PlusOutlined />, '新建仿真实验') },
    { key: '/llms', label: linkLabel('/llms', <ApiOutlined />, '大模型配置') },
    { key: '/agents', label: linkLabel('/agents', <TeamOutlined />, '智能体配置') },
    { key: '/workflows', label: linkLabel('/workflows', <NodeIndexOutlined />, '工作流配置') },
  ];

  const items: MenuProps['items'] = [
    { key: '/', label: linkLabel('/', <HomeOutlined />, '工作台') },
    { key: '/supplier-risk', label: linkLabel('/supplier-risk', <SafetyCertificateOutlined />, '供应商风险') },
    { key: '/quality', label: linkLabel('/quality', <SafetyCertificateOutlined />, '质量异常处置') },
    { key: '/industry', label: linkLabel('/industry', <ApartmentOutlined />, '产业链图谱') },
    {
      key: '/console',
      label: (
        <Dropdown menu={{ items: experimentItems }} placement="bottomLeft" arrow>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ExperimentOutlined /><span>仿真与配置</span>
          </div>
        </Dropdown>
      ),
    },
    { key: '/survey', label: linkLabel('/survey', <QuestionCircleOutlined />, '调研问卷') },
  ];

  return (
    <Menu
      theme="dark"
      mode="horizontal"
      items={items}
      selectedKeys={[selectedKey]}
      style={{ background: 'transparent', border: 'none' }}
    />
  );
}
