document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const usernameOrEmailInput = document.getElementById('username_email');
    const passwordInput = document.getElementById('password');
    const togglePasswordButton = document.getElementById('togglePassword');
    const loginButton = document.getElementById('loginButton');
    const buttonText = document.getElementById('buttonText');
    const buttonSpinner = document.getElementById('buttonSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // 密码可见性
    let passwordVisible = false;
    togglePasswordButton.addEventListener('click', function () {
        passwordVisible = !passwordVisible;
        const type = passwordVisible ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        togglePasswordButton.textContent = passwordVisible ? '隐藏' : '显示';
    });

    // 表单提交处理
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // 隐藏之前的错误信息
        errorMessage.classList.remove('show');

        // 获取表单数据
        const usernameOrEmail = usernameOrEmailInput.value.trim();
        const password = passwordInput.value.trim();

        // 简单的客户端验证
        if (!usernameOrEmail) {
            showError('请输入用户名或邮箱');
            return;
        }

        if (!password) {
            showError('请输入密码');
            return;
        }

        // 设置加载状态
        setLoading(true);

        // 使用fetch API发送登录请求
        // 注意：这里需要credentials: 'same-origin'以确保Cookie正常设置
        fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                username_email: usernameOrEmail,
                password: password
            })
        })
            .then(response => {
                return response.json().then(data => {
                    if (!response.ok) {
                        // 处理HTTP错误，优先使用后端返回的message
                        throw new Error(data.message || `登录请求失败: ${response.status}`);
                    }
                    return data;
                }).catch(error => {
                    // 如果JSON解析失败，再抛出通用错误
                    if (error.name === 'SyntaxError') {
                        throw new Error(`登录请求失败: ${response.status}`);
                    }
                    throw error;
                });
            })
            .then(data => {
                //setLoading(false);

                if (data.code === 200) {
                    showSuccess(data.message || '登录成功！正在跳转...');
                    const redirectUrl = new URLSearchParams(window.location.search).get('redirect') || '/admin';
                    setTimeout(() => {
                        window.location.href = redirectUrl;
                    }, 2000);
                } else {
                    showError(data.message || '登录失败，请重试');
                }
            })
            .catch(error => {
                showError(error.message || '登录失败，请检查网络连接后重试');
            });
    });

    // 显示错误信息
    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.add('show');

        // 3秒后自动隐藏错误信息
        setTimeout(() => {
            errorMessage.classList.remove('show');
        }, 3000);
    }

    // 显示成功信息
    function showSuccess(message) {
        // 创建或获取成功消息元素
        let successMessage = document.getElementById('successMessage');
        if (!successMessage) {
            successMessage = document.createElement('div');
            successMessage.id = 'successMessage';
            successMessage.className = 'success-message';
            const successText = document.createElement('span');
            successText.id = 'successText';
            successMessage.appendChild(successText);
            errorMessage.parentNode.insertBefore(successMessage, errorMessage.nextSibling);
        }
        
        const successText = document.getElementById('successText');
        successText.textContent = message;
        successMessage.classList.add('show');
        
        // 隐藏错误消息（如果有）
        errorMessage.classList.remove('show');
        
        // 3秒后自动隐藏成功信息
        setTimeout(() => {
            successMessage.classList.remove('show');
        }, 3000);
    }

    // 设置按钮加载状态
    function setLoading(isLoading) {
        loginButton.disabled = isLoading;

        if (isLoading) {
            buttonText.textContent = '登录中...';
            buttonSpinner.style.display = 'inline-block';
        } else {
            buttonText.textContent = '登录';
            buttonSpinner.style.display = 'none';
        }
    }
    
    // 初始化令牌刷新机制
    initTokenRefresh();
});

// 初始化令牌刷新机制
function initTokenRefresh() {
    // 监听所有fetch请求
    const originalFetch = window.fetch;
    window.fetch = async function(resource, options = {}) {
        // 确保有credentials选项
        if (!options.credentials) {
            options.credentials = 'same-origin';
        }
        
        try {
            // 发送原始请求
            const response = await originalFetch(resource, options);
            
            // 如果是401错误，尝试刷新令牌
              if (response.status === 401 && resource !== '/api/auth/refresh') {
                  // 尝试刷新令牌 - 修复：不发送空的body，发送一个有效的JSON对象
                  const refreshResponse = await originalFetch('/api/auth/refresh', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    // 发送一个有效的空对象作为body
                    body: JSON.stringify({})
                });
                
                // 如果刷新成功，重试原始请求
                if (refreshResponse.ok) {
                    return await originalFetch(resource, options);
                } else {
                    // 刷新失败，跳转到登录页
                    // 修复：避免重定向URL嵌套问题
                    const currentPath = window.location.pathname + window.location.search;
                    // 如果当前已经是登录页，则不添加redirect参数，避免嵌套
                    const redirectUrl = currentPath.startsWith('/login') ? 
                        '/login' : 
                        '/login?redirect=' + encodeURIComponent(currentPath);
                    window.location.href = redirectUrl;
                    return response;
                }
            }
            
            return response;
        } catch (error) {
            console.error('请求错误:', error);
            throw error;
        }
    };
}