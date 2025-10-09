document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const usernameOrEmailInput = document.getElementById('username_or_email');
    const passwordInput = document.getElementById('password');
    const togglePasswordButton = document.getElementById('togglePassword');
    const loginButton = document.getElementById('loginButton');
    const buttonText = document.getElementById('buttonText');
    const buttonSpinner = document.getElementById('buttonSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // 切换密码可见性
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
        fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username_or_email: usernameOrEmail,
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
                setLoading(false);

                if (data.code === 200) {
                    // 登录成功，刷新当前页面
                    window.location.reload();
                } else {
                    showError(data.message || '登录失败，请重试');
                }
            })
            .catch(error => {
                setLoading(false);
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
});