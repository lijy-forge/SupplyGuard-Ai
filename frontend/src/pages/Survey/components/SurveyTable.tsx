import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, message, Space, Flex, Col, Row, Alert, Popconfirm } from 'antd';
import dayjs from 'dayjs';
import { Model, Survey as SurveyUI } from 'survey-react-ui';
import 'survey-core/defaultV2.min.css';
import { useForm } from 'antd/lib/form/Form';
import { ExportOutlined } from '@ant-design/icons';
import { Editor } from '../../../components/Editor';
import { Survey } from '../../../components/type';

interface EditingSurvey {
    id: string;
    name: string;
    data: string;
}

const EmptySurvey: EditingSurvey = {
    id: '',
    name: '',
    data: '',
};

const SurveyTable = () => {
    const [surveys, setSurveys] = useState<Survey[]>([]);
    const [open, setOpen] = useState(false);
    const [editingSurvey, setEditingSurvey] = useState<EditingSurvey>(EmptySurvey);
    const [form] = useForm();

    useEffect(() => {
        if (editingSurvey) {
            form.setFieldsValue({
                name: editingSurvey.name,
                data: editingSurvey.data,
            });
        }
    }, [editingSurvey, form]);

    useEffect(() => {
        fetchSurveys();
    }, []);


    const handleJsonButton = () => {
        window.open('https://surveyjs.io/create-free-survey', '_blank');
    };


    const fetchSurveys = async () => {
        try {
            const res = await fetch('/api/surveys');
            if (!res.ok) {
                // Read the error message as text
                const errMessage = await res.text();
                throw new Error(errMessage);
            }
            const data = await res.json();
            setSurveys(data.data);
        } catch (err) {
            message.error(`获取问卷失败：${err}`);
        }
    };

    const handleDelete = async (id) => {
        try {
            const res = await fetch(`/api/surveys/${id}`, { method: 'DELETE' });
            if (!res.ok) {
                // Read the error message as text
                const errMessage = await res.text();
                throw new Error(errMessage);
            }
            message.success('删除成功！');
            await fetchSurveys();
        } catch (err) {
            message.error(`删除失败：${err}`);
        }
    };

    const handleEdit = (survey) => {
        setEditingSurvey({
            id: survey.id,
            name: survey.name,
            data: JSON.stringify(survey.data, null, 2),
        });
        setOpen(true);
    };

    const handleCreate = () => {
        setEditingSurvey(EmptySurvey);
        setOpen(true);
    };

    const handleSubmit = async (values) => {
        console.log(values);
        console.log(editingSurvey);
        if (editingSurvey.id !== '') {
            try {
                const res = await fetch(`/api/surveys/${editingSurvey.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: values.name,
                        data: JSON.parse(values.data),
                    }),
                });
                if (!res.ok) {
                    // Read the error message as text
                    const errMessage = await res.text();
                    throw new Error(errMessage);
                }
                message.success('更新成功！');
                setOpen(false);
                await fetchSurveys();
            } catch (err) {
                message.error(`更新失败：${err}`);
            }
        } else {
            try {
                const res = await fetch('/api/surveys', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: values.name,
                        data: JSON.parse(values.data),
                    }),
                });
                if (!res.ok) {
                    // Read the error message as text
                    const errMessage = await res.text();
                    throw new Error(errMessage);
                }
                message.success('创建成功！');
                setOpen(false);
                await fetchSurveys();
            } catch (err) {
                message.error(`创建失败：${err}`);
            }
        }
    };

    const handleModalCancel = () => {
        setOpen(false);
    };

    const tableColumns = [
        { title: 'ID', dataIndex: 'id', width: '13%' },
        { title: '名称', dataIndex: 'name', width: '7%' },
        {
            title: '数据',
            dataIndex: 'data',
            width: '55%',
            ellipsis: true,
            render: (text) => JSON.stringify(text, null, 2),
        },
        {
            title: '创建时间',
            dataIndex: 'createdAt',
            width: '10%',
            render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
        },
        {
            title: '更新时间',
            dataIndex: 'updatedAt',
            width: '10%',
            render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
        },
        {
            title: '操作',
            key: 'action',
            width: '15%',
            render: (record) => (
                <Space size="middle">
                    <Button type="primary" onClick={() => handleEdit(record)}>编辑与预览</Button>
                    <Popconfirm title="确定删除该问卷吗？" onConfirm={() => handleDelete(record.id)}>
                        <Button type="primary" danger>删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    let model = new Model({});
    try {
        model = new Model(JSON.parse(editingSurvey.data));
    } catch (e) {
        console.error('Failed to parse JSON data:', e);
    }
    model.showCompleteButton = false;

    return (
        <>
            <Flex vertical style={{ margin: "16px" }}>
                <Flex justify='end'>
                    <Button type="primary" onClick={handleCreate} style={{ marginBottom: 16 }}>
                        新建问卷
                    </Button>
                </Flex>
                <Table dataSource={surveys} columns={tableColumns} rowKey="id" />
                <Modal
                    open={open}
                    width='80vw'
                    title={editingSurvey ? '编辑问卷' : '新建问卷'}
                    onCancel={handleModalCancel}
                    footer={null}
                >
                    <Flex>
                        <Form
                            form={form}
                            style={{ width: '50%', marginRight: 16 }}
                            layout="vertical"
                            onValuesChange={(changedValues, allValues) => {
                                setEditingSurvey({
                                    ...editingSurvey,
                                    ...changedValues,
                                });
                            }}
                            onFinish={handleSubmit}
                        >
                            <Form.Item label="名称" name="name" rules={[
                                { required: true, message: '请输入名称' },
                            ]}>
                                <Input />
                            </Form.Item>
                            <Form.Item
                                label={<span>问卷 JSON 数据（在线可视化编辑器&nbsp;<ExportOutlined onClick={handleJsonButton} />&nbsp;）</span>}
                                name="data"
                                rules={[
                                    { required: true, message: '请输入问卷 JSON 数据' },
                                    {
                                        validator: (_, value, callback) => {
                                            try {
                                                JSON.parse(value);
                                                callback();
                                            } catch (e) {
                                                callback('JSON 格式无效');
                                            }
                                        }
                                    },
                                ]}
                            >
                                <Editor
                                    width="100%"
                                    height="50vh"
                                    language="json"
                                    defaultValue=''
                                    value={form.getFieldValue('data') || ''}
                                    onChange={(value) => form.setFieldValue('data', value)}
                                />
                            </Form.Item>
                            <Button type="primary" htmlType='submit' style={{ marginTop: 8 }}>
                                提交
                            </Button>
                        </Form>
                        <div style={{ overflow: 'auto', maxHeight: '60vh', width: '50%' }}>
                            <SurveyUI model={model} />
                        </div>
                    </Flex>
                </Modal>
            </Flex >
        </>
    );
};

export default SurveyTable;
