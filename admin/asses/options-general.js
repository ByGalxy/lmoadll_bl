// 查询基础信息
function fetchoptions() {
    const site_name = document.querySelector('#site-name');
    const site_description = document.querySelector('#site-description');
    const site_keywords = document.querySelector('#site-keywords');

    if (site_name || site_description || site_keywords) {
        // 获取网站名称
        fetch('/admin/get_name_options', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user: 'site_name' }),
            credentials: 'same-origin'
        })
            .then((response) => response.text())
            .then((data) => {
                site_name.value = data;
            });

        // 获取网站描述
        fetch('/admin/get_name_options', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user: 'site_description' }),
            credentials: 'same-origin'
        })
            .then((response) => response.text())
            .then((data) => {
                site_description.value = data;
            });

        // 获取网站关键词
        fetch('/admin/get_name_options', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user: 'site_keywords' }),
            credentials: 'same-origin'
        })
            .then((response) => response.text())
            .then((data) => {
                site_keywords.value = data;
            });
    }
}

// 保存设置
function saveSettings() {
    const site_name = document.querySelector('#site-name').value;
    const site_description = document.querySelector('#site-description').value;
    const site_keywords = document.querySelector('#site-keywords').value;

    fetch('/admin/set_name_options', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            site_name: site_name,
            site_description: site_description,
            site_keywords: site_keywords
        }),
        credentials: 'same-origin'
    })
        .then((response) => response.text())
        .then((data) => {
            alert(data);
            window.location.reload();
        });
}

// 页面加载时获取数据
window.onload = function () {
    fetchoptions();

    // 绑定保存按钮的点击事件
    const submitBtn = document.querySelector('.submit-btn');
    submitBtn.addEventListener('click', saveSettings);
};
