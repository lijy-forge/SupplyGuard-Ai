import { Divider, Flex, Layout, Typography } from "antd";
import { Content, Header } from "antd/es/layout/layout";
import RootMenu from "./Menu";
import { Link } from "react-router-dom";
import React, { useEffect, useRef } from "react";

const { Title } = Typography;

export default function RootLayout({
    children,
    selectedKey,
    homePage,
}: {
    children: React.ReactNode
    selectedKey: string
    homePage?: boolean
}) {
    const headerRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);

    // get the height of the header to set the content height
    useEffect(() => {
        if (contentRef.current === null) {
            return
        }
        if (headerRef.current) {
            const headerHeight = headerRef.current.clientHeight;
            if (contentRef.current) {
                contentRef.current.style.minHeight = `calc(100vh - ${headerHeight}px)`;
                return
            }
        }
        contentRef.current.style.minHeight = `calc(100vh - 64px)`;
    }, [headerRef, contentRef]);

    const contentStyle: React.CSSProperties = homePage ? {
        width: "100%",
        background: '#f3f6fb',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
    } : {};

    return (
        <Layout>
            <Header ref={headerRef}>
                <Flex gap='small' align='center' justify='space-between' style={{ width: '100%' }}>
                    <Flex align='center' style={{ width: '100%' }}>
                    <Link to="/" style={{ color: 'white', whiteSpace: 'nowrap' }}>
                        <Title level={4} style={{ margin: 0, color: 'white' }}>SupplyGuard AI</Title>
                    </Link>
                    <Divider type="vertical" />
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <RootMenu selectedKey={selectedKey} />
                    </div>
                    </Flex>
                </Flex>
            </Header>
            <Content ref={contentRef} style={contentStyle}>
                {children}
            </Content>
        </Layout>
    )
}
