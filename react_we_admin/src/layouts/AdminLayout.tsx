import React, { useState, useEffect } from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Typography, theme } from 'antd';
import {
    DashboardOutlined,
    UserOutlined,
    MessageOutlined,
    BellOutlined,
    SettingOutlined,
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined
} from '@ant-design/icons';
import Dashboard from '../pages/Dashboard';
import UserManagement from '../pages/UserManagement';
import Messages from '../pages/Messages';
import Settings from '../pages/Settings';
import axios from 'axios';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface AdminLayoutProps {
    onLogout: () => void;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ onLogout }) => {
    const [collapsed, setCollapsed] = useState(false);
    const [selectedKey, setSelectedKey] = useState('dashboard');
    const [adminInfo, setAdminInfo] = useState({ name: '管理员', identity: '管理员' });
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();

    useEffect(() => {
        fetchAdminInfo();
    }, []);

    const fetchAdminInfo = async () => {
    try {
      // 从localStorage获取用户信息
      const userInfo = localStorage.getItem('userInfo');
      if (userInfo) {
        const parsedInfo = JSON.parse(userInfo);
        setAdminInfo({
          name: parsedInfo.name || '管理员',
          identity: parsedInfo.group || '管理员'
        });
      }

      // 从服务器获取最新用户信息
      const response = await axios.get('https://api.banana404.top/api/auth/user', {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data.code === 200) {
        const userData = response.data.data;
        setAdminInfo({
          name: userData.name || '管理员',
          identity: userData.group || '管理员'
        });
        
        // 更新localStorage中的用户信息
        localStorage.setItem('userInfo', JSON.stringify({
          uid: userData.uid,
          name: userData.name,
          email: userData.email,
          group: userData.group
        }));
      }
    } catch (error: any) {
      console.error('获取管理员信息失败:', error);
      if (error.response?.status === 401) {
        // 未登录，清除localStorage
        localStorage.removeItem('userInfo');
      }
    }
  };

    const menuItems = [
        {
        key: 'dashboard',
        icon: <DashboardOutlined />,
        label: '仪表盘',
        },
        {
        key: 'users',
        icon: <UserOutlined />,
        label: '用户管理',
        },
        {
        key: 'messages',
        icon: <MessageOutlined />,
        label: '消息管理',
        },
        {
        key: 'settings',
        icon: <SettingOutlined />,
        label: '系统设置',
        },
    ];

    const userMenuItems = [
        {
        key: 'profile',
        icon: <UserOutlined />,
        label: '个人信息',
        },
        {
        key: 'logout',
        icon: <LogoutOutlined />,        label: '退出登录',
        onClick: onLogout,
        },
    ];

    const renderContent = () => {
        switch (selectedKey) {
        case 'dashboard':
            return <Dashboard />;
        case 'users':
            return <UserManagement />;
        case 'messages':
            return <Messages />;
        case 'settings':
            return <Settings />;
        default:
            return <Dashboard />;
        }
    };

    return (
        <Layout style={{ minHeight: '100vh' }}>
        <Sider 
            trigger={null} 
            collapsible 
            collapsed={collapsed}
            style={{
            background: colorBgContainer,
            boxShadow: '2px 0 8px rgba(0, 0, 0, 0.1)'
            }}
        >
            <div style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0'
            }}>
            <Text strong style={{ fontSize: collapsed ? 14 : 16, color: '#1890ff' }}>
                {collapsed ? 'L' : 'Lmoadll'}
            </Text>
            </div>
            
            <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            items={menuItems}
            onClick={({ key }) => setSelectedKey(key)}
            style={{ borderRight: 0, marginTop: 16 }}
            />
        </Sider>
        
        <Layout>
            <Header style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
            }}>
            <div>
                {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
                className: 'trigger',
                onClick: () => setCollapsed(!collapsed),
                style: { fontSize: 18, cursor: 'pointer' }
                })}
            </div>
            
            <Space size="middle">
                <BellOutlined style={{ fontSize: 18, cursor: 'pointer' }} />
                <Dropdown 
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
                >
                <Space style={{ cursor: 'pointer' }}>
                    <Avatar size="small" icon={<UserOutlined />} />
                    <Text>{adminInfo.name}</Text>
                </Space>
                </Dropdown>
            </Space>
            </Header>
            
            <Content style={{
            margin: '24px',
            padding: 24,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: 280
            }}>
            {renderContent()}
            </Content>
        </Layout>
        </Layout>
    );
};

export default AdminLayout;