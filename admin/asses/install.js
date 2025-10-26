// 正确定义所有需要的变量
const agreeTerms = document.getElementById('agree-terms');
const nextBtn = document.getElementById('next-btn');
const step1 = document.getElementById('step-1');
const step2 = document.getElementById('step-2');
const step3 = document.getElementById('step-3');
const step4 = document.getElementById('step-4');
const testDbBtn = document.getElementById('verificat_db_conn');
const toStep4Btn = document.getElementById('to-step-4');
const dbTypeSelect = document.getElementById('db-type');
const mysqlConfig = document.getElementById('mysql-config');
const sqliteConfig = document.getElementById('sqlite-config');
const sqlitePathNote = document.getElementById('sqlite-path-note');
const testConnBtn = document.getElementById('verificat_db_conn');

// 存储数据库配置信息
let dbConfig = null;

// 页面加载时重置复选框状态
window.addEventListener('load', () => {
    if (agreeTerms) {
        agreeTerms.checked = false;
    }
    if (nextBtn) {
        nextBtn.classList.add('disabled');
    }
});

// 同意条款复选框事件
if (agreeTerms && nextBtn) {
    agreeTerms.addEventListener('change', () => {
        if (agreeTerms.checked) {
            nextBtn.classList.remove('disabled');
        } else {
            nextBtn.classList.add('disabled');
        }
    });
}

// 下一步按钮事件
if (nextBtn && step1 && step2) {
    nextBtn.addEventListener('click', (e) => {
        if (nextBtn.classList.contains('disabled')) {
            e.preventDefault();
            return;
        }
        step1.style.display = 'none';
        step2.style.display = 'block';
    });
}

// 开始安装
if (toStep4Btn && step3 && step4) {
    toStep4Btn.addEventListener('click', () => {
        const siteName = document.getElementById('site-name')?.value || '';
        const siteUrl = document.getElementById('site-url')?.value || '';
        const adminEmail = document.getElementById('admin-email')?.value || '';
        const adminUsername = document.getElementById('admin-username')?.value || '';
        const adminPassword = document.getElementById('admin-password')?.value || '';

        // 验证必填字段
        if (!siteName || !siteUrl || !adminEmail || !adminUsername || !adminPassword) {
            alert('请填写所有必填字段');
            return;
        }

        // 构建请求数据
        const requestData = {
            site_name: siteName,
            site_url: siteUrl,
            superadministrator_email: adminEmail,
            superadministrator_username: adminUsername,
            superadministrator_password: adminPassword
        };

        // 添加数据库配置信息
        if (dbConfig) {
            Object.assign(requestData, dbConfig);
        }

        // 发送请求到后端
        fetch('/install/create_admin_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 创建成功，跳转到完成页面
                step3.style.display = 'none';
                step4.style.display = 'block';
            } else {
                alert('创建失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('创建管理员账号时出错:', error);
            alert('创建管理员账号时发生错误，请重试');
        });
    });
}

// 控制布局
if (dbTypeSelect) {
    dbTypeSelect.addEventListener('change', function () {
        const dbType = this.value;

        // 隐藏所有配置
        if (mysqlConfig) mysqlConfig.style.display = 'none';
        if (sqliteConfig) sqliteConfig.style.display = 'none';
        if (sqlitePathNote) sqlitePathNote.style.display = 'none';

        if (dbType === 'mysql' && mysqlConfig) {
            mysqlConfig.style.display = 'block';
        } else if (dbType === 'sqlite' && sqliteConfig) {
            sqliteConfig.style.display = 'block';

            // 向后端发送请求获取SQLite默认路径
            fetch('/install/get_sqlite_path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ db_type: 'sqlite' })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.path && document.getElementById('sql_sqlite_path')) {
                        // 设置数据库路径输入框的值
                        document.getElementById('sql_sqlite_path').value = data.path;
                        if (sqlitePathNote) {
                            sqlitePathNote.textContent = '\'' + data.path + '\'' + ' 这个是系统自动生成的地址';
                            sqlitePathNote.style.display = 'block';
                        }
                    } else if (data.error) {
                        console.error('获取SQLite路径时出错:', data.error);
                    }
                })
                .catch(error => {
                    console.error('获取SQLite路径时出错:', error);
                });
        }
    });
}

// 继续按钮事件处理
if (testConnBtn) {
    testConnBtn.addEventListener('click', function (e) {
        e.preventDefault();

        const dbType = document.getElementById('db-type')?.value || '';
        let requestData = { db_type: dbType };

        if (dbType === 'sqlite') {
            requestData.db_prefix = document.getElementById('db-prefix')?.value || '';
            requestData.sql_sqlite_path = document.getElementById('sql_sqlite_path')?.value || '';
        }

        if (dbType === 'mysql') {
            requestData.db_host = document.getElementById('db-host')?.value || '';
            requestData.db_port = document.getElementById('db-port')?.value || '';
            requestData.db_name = document.getElementById('db-name')?.value || '';
            requestData.db_user = document.getElementById('db-user')?.value || '';
            requestData.db_password = document.getElementById('db-password')?.value || '';
        }

        // 保存数据库配置信息
        dbConfig = requestData;

        // 发送验证请求到后端
        fetch('/install/verification_db_conn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (document.getElementById('step-2') && document.getElementById('step-3')) {
                        document.getElementById('step-2').style.display = 'none';
                        document.getElementById('step-3').style.display = 'block';
                    }
                } else {
                    alert('数据库连接失败: ' + data.message);
                }
            })
    });
}