// 获取仪表盘数据
function fetchDashboardData() {
    const totalUsersElement = document.querySelector('#totalUsers');
    const onlineUsersElement = document.querySelector('#onlineUsers');
    const totalVisitsElement = document.querySelector('#totalVisits');
    const conversionRateElement = document.querySelector('#conversionRate');

    if (totalUsersElement || onlineUsersElement || totalVisitsElement || conversionRateElement) {
        // 获取管理员名称
        fetch('/api/admin/get_admin_name', {
            method: 'POST',
            credentials: 'same-origin'
        })
            .then(response => response.text())
            .then(data => {
                if (totalUsersElement && data && data !== 'Unknown') {
                    totalUsersElement.textContent = data;
                }
            })
            .catch(error => {
                console.error('获取总用户数失败:', error);
            });
    }
}


// 获取管理员名称和身份
function fetchAdminInfo() {
    const adminNameElement = document.querySelector('#admin-name');
    const adminIdentityElement = document.querySelector('#admin-identity');

    if (adminNameElement || adminIdentityElement) {
        // 获取管理员名称
        fetch('/api/admin/get_admin_name', {
            method: 'POST',
            credentials: 'same-origin'
        })
            .then(response => response.text())
            .then(data => {
                if (adminNameElement && data && data !== 'Unknown') {
                    adminNameElement.textContent = data;
                }
            })
            .catch(error => {
                console.error('获取管理员名称失败:', error);
            });

        // 获取管理员身份
        fetch('/api/admin/get_admin_identity', {
            method: 'POST',
            credentials: 'same-origin'
        })
            .then(response => response.text())
            .then(data => {
                if (adminIdentityElement && data && data !== 'Unknown') {
                    adminIdentityElement.textContent = data;
                }
            })
            .catch(error => {
                console.error('获取管理员身份失败:', error);
            });
    }
}


// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function () {
    // 下拉菜单功能
    const userProfile = document.querySelector('.user-profile');
    const dropdownMenu = document.querySelector('.dropdown-menu');

    if (userProfile && dropdownMenu) {
        userProfile.addEventListener('click', function (e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        // 点击其他区域关闭下拉菜单
        document.addEventListener('click', function () {
            if (dropdownMenu.classList.contains('show')) {
                dropdownMenu.classList.remove('show');
            }
        });

        // 阻止下拉菜单内的点击事件冒泡
        dropdownMenu.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    }

    // 退出登录功能
    const logoutButton = document.querySelector('.logout-button') || document.querySelector('#logout-btn');

    if (logoutButton) {
        logoutButton.addEventListener('click', function () {
            if (confirm('确定要退出登录吗？')) {
                // 发送退出登录请求到服务器
                fetch('/api/auth/logout', {
                    method: 'GET',
                    credentials: 'same-origin'
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.code === 200) {
                            // 删除localStorage中的用户信息
                            try {
                                localStorage.removeItem('userInfo');
                                localStorage.removeItem('token');
                            } catch (e) {
                                console.error('清除localStorage失败:', e);
                            }

                            console.log('用户退出登录成功');
                            window.location.reload();
                        } else {
                            console.error('退出登录失败:', data.message);
                            alert('退出登录失败，请重试');
                            // 失败时也刷新页面，确保用户状态一致性
                            window.location.reload();
                        }
                    })
                    .catch(error => {
                        console.error('退出登录请求失败:', error);
                        // 即使请求失败，也刷新页面，确保用户状态安全
                        window.location.reload();
                    });
            }
        });
    }

    // 如果页面上有仪表盘元素，则调用此函数
    if (document.querySelector('#totalUsers') || document.querySelector('#onlineUsers') ||
        document.querySelector('#totalVisits') || document.querySelector('#conversionRate')) {
        fetchDashboardData();
    }

    // 登录表单处理
    const loginForm = document.querySelector('.login-form');

    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const username = document.querySelector('#username').value;
            const password = document.querySelector('#password').value;
            const errorMessage = document.querySelector('.error-message');
            const submitButton = document.querySelector('.submit-button');
            const originalButtonText = submitButton.innerHTML;

            // 显示加载状态
            submitButton.disabled = true;
            submitButton.innerHTML = '<div class="spinner"></div> 登录中...';

            // 简单的表单验证
            if (!username || !password) {
                setTimeout(function () {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonText;

                    if (errorMessage) {
                        errorMessage.textContent = '请输入用户名和密码';
                        errorMessage.classList.add('show');
                    }
                }, 500);
                return;
            }

            // 隐藏错误消息
            if (errorMessage && errorMessage.classList.contains('show')) {
                errorMessage.classList.remove('show');
            }
        });
    }

    // 密码显示/隐藏功能
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');

    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function () {
            const passwordInput = this.previousElementSibling;
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';

            passwordInput.setAttribute('type', type);
            this.textContent = type === 'password' ? '显示' : '隐藏';
        });
    });

    // 页面滚动监听
    window.addEventListener('scroll', function () {
        const header = document.querySelector('.header');

        if (header) {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }
    });

    // 平滑滚动功能
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // 响应式导航菜单
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function () {
            mobileMenu.classList.toggle('show');
        });
    }

    // 防抖函数 - 用于优化搜索、窗口调整等频繁触发的事件
    function debounce(func, wait) {
        let timeout;
        return function () {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    // 节流函数 - 用于优化滚动、鼠标移动等连续触发的事件
    function throttle(func, limit) {
        let inThrottle;
        return function () {
            const context = this;
            const args = arguments;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // 导出常用函数，以便在其他脚本中使用
    window.adminUtils = {
        debounce,
        throttle,
        fetchAdminInfo,
        fetchDashboardData
    };

    // 如果页面上有需要显示管理员信息的元素，则调用此函数
    if (document.querySelector('#admin-name') || document.querySelector('#admin-identity')) {
        fetchAdminInfo();
    }
});
