import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Spin } from 'antd';
import { UserOutlined, EyeOutlined, RiseOutlined, DashboardOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;

interface DashboardData {
    totalUsers?: number;
    onlineUsers?: number;
    totalVisits?: number;
    conversionRate?: number;
}

const Dashboard: React.FC = () => {
    const [dashboardData, setDashboardData] = useState<DashboardData>({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      const response = await axios.get('https://api.banana404.top/api/auth/user', {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.data.code === 200) {
        const userData = response.data.data;

        const totalUsers = parseInt(userData.uid) || 1000;
        
        // 模拟一些数据，实际应该从API获取
        setDashboardData({
			totalUsers: totalUsers,
			onlineUsers: 245,
			totalVisits: 12345,
			conversionRate: 12.5
        });
      } else {
        // 如果获取用户信息失败，使用默认数据
        setDashboardData({
			totalUsers: 1000,
			onlineUsers: 245,
			totalVisits: 12345,
			conversionRate: 12.5
        });
      }
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
      // 设置默认数据
      setDashboardData({
        totalUsers: 1000,
        onlineUsers: 245,
        totalVisits: 12345,
        conversionRate: 12.5
      });
    } finally {
      setLoading(false);
    }
  };

    if (loading) {
        return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
            <Spin size="large" />
        </div>
        );
    }

    return (
        <div>
        <Title level={2} style={{ marginBottom: 24 }}>
            <DashboardOutlined /> 仪表盘
        </Title>
        
        <Row gutter={[24, 24]}>
            <Col xs={24} sm={12} lg={6}>
            <Card>
                <Statistic
                title="总用户数"
                value={dashboardData.totalUsers || 0}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#3f8600' }}
                />
            </Card>
            </Col>
            
            <Col xs={24} sm={12} lg={6}>
            <Card>
                <Statistic
                title="在线用户"
                value={dashboardData.onlineUsers || 0}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#1890ff' }}
                />
            </Card>
            </Col>
            
            <Col xs={24} sm={12} lg={6}>
            <Card>
                <Statistic
                title="总访问量"
                value={dashboardData.totalVisits || 0}
                prefix={<EyeOutlined />}
                valueStyle={{ color: '#cf1322' }}
                />
            </Card>
            </Col>
            
            <Col xs={24} sm={12} lg={6}>
            <Card>
                <Statistic
                title="转化率"
                value={dashboardData.conversionRate || 0}
                suffix="%"
                prefix={<RiseOutlined />}
                valueStyle={{ color: '#722ed1' }}
                />
            </Card>
            </Col>
        </Row>
        
        <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
            <Col span={24}>
            <Card title="系统概览" style={{ minHeight: 400 }}>
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Title level={4} type="secondary">
                    欢迎使用 Lmoadll 后台管理系统
                </Title>
                <p style={{ color: '#666', fontSize: 16 }}>
                    这里是系统概览页面，后续可以添加更多图表和功能模块
                </p>
                </div>
            </Card>
            </Col>
        </Row>
        </div>
    );
};

export default Dashboard;