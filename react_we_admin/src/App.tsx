import React, { useState, useEffect } from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import axios from 'axios';
import Login from './pages/Login';
import AdminLayout from './layouts/AdminLayout';
import './App.css';

const App = () => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // 检查用户是否已登录
        const checkLoginStatus = () => {
        try {
            const userInfo = localStorage.getItem('userInfo');
            if (userInfo) {
            setIsLoggedIn(true);
            }
        } catch (error) {
            console.error('检查登录状态失败:', error);
        } finally {
            setLoading(false);
        }
        };

        checkLoginStatus();
    }, []);

    const handleLogin = () => {
        setIsLoggedIn(true);
    };

    const handleLogout = async () => {
    try {
      // 调用登出API
      await axios.post('https://api.banana404.top/api/auth/logout', {}, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('登出API调用失败:', error);
    } finally {
      // 清除localStorage
      localStorage.removeItem('userInfo');
      
      // 清除cookie（通过设置过期时间为过去的时间）
      document.cookie = 'lmoadll_refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      
      setIsLoggedIn(false);
    }
  };

    if (loading) {
        return (
        <ConfigProvider locale={zhCN}>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <div>加载中...</div>
            </div>
        </ConfigProvider>
        );
    }

    return (
        <ConfigProvider locale={zhCN}>
        {isLoggedIn ? (
            <AdminLayout onLogout={handleLogout} />
        ) : (
            <Login onLogin={handleLogin} />
        )}
        </ConfigProvider>
    );
};

export default App;