document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('user-search');
    const searchClear = document.getElementById('search-clear');
    const searchLoading = document.getElementById('search-loading');
    const searchHint = document.getElementById('search-hint');
    const usersList = document.getElementById('users-list');
    const noUsersMessage = document.getElementById('no-users-message');

    let searchTimeout;

    // 搜索框聚焦事件
    searchInput.addEventListener('focus', function () {
        searchHint.classList.add('show');
    });

    // 搜索框失焦事件
    searchInput.addEventListener('blur', function () {
        setTimeout(() => {
            searchHint.classList.remove('show');
        }, 200);
    });

    // 清除按钮事件
    searchClear.addEventListener('click', function () {
        searchInput.value = '';
        searchClear.classList.remove('show');
        searchInput.focus();
        resetSearchResults();
    });

    // 输入事件
    searchInput.addEventListener('input', function (e) {
        const searchTerm = e.target.value.trim();

        // 显示/隐藏清除按钮
        if (searchTerm.length > 0) {
            searchClear.classList.add('show');
        } else {
            searchClear.classList.remove('show');
        }

        clearTimeout(searchTimeout);

        if (searchTerm.length === 0) {
            resetSearchResults();
            return;
        }

        if (searchTerm.length < 2) {
            showMessage('请输入至少2个字符进行搜索');
            return;
        }

        // 显示加载动画
        searchLoading.classList.add('show');

        searchTimeout = setTimeout(() => {
            searchUsers(searchTerm);
        }, 800);
    });

    function resetSearchResults() {
        usersList.style.display = 'none';
        noUsersMessage.style.display = 'block';
        noUsersMessage.innerHTML = '<p>请输入关键词搜索用户</p>';
        searchLoading.classList.remove('show');
    }

    function showMessage(message) {
        usersList.style.display = 'none';
        noUsersMessage.style.display = 'block';
        noUsersMessage.innerHTML = `<p>${message}</p>`;
        searchLoading.classList.remove('show');
    }

    function searchUsers(searchTerm) {
        fetch(`/api/admin/users/search?q=${encodeURIComponent(searchTerm)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                search_term: searchTerm,
                page: currentPage,
                page_size: pageSize
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('搜索失败');
                }
                return response.json();
            })
            .then(data => {
                displayUsers(data.users || []);
                searchLoading.classList.remove('show');
            })
            .catch(error => {
                console.error('搜索错误:', error);
                showMessage('搜索失败，请重试');
                searchLoading.classList.remove('show');
            });
    }

    function displayUsers(users) {
        if (users.length === 0) {
            showMessage('杂鱼杂鱼杂鱼~没有搜索到对象');
            return;
        }

        usersList.style.display = 'block';
        noUsersMessage.style.display = 'none';

        usersList.innerHTML = users.map(user => `
            <div class="user-card">
                <div class="user-avatar">${user.name ? user.name.charAt(0).toUpperCase() : 'U'}</div>
                <div class="user-details">
                    <div class="user-name">${user.name || '未知用户'}</div>
                    <div class="user-email">${user.email || '无邮箱'}</div>
                    <div class="user-id">ID: ${user.id || '未知'}</div>
                </div>
                <div class="user-actions">
                    <button class="btn btn-secondary" onclick="viewUserDetails('${user.id}')">查看详情</button>
                </div>
            </div>
        `).join('');
    }

    window.viewUserDetails = function (userId) {
        console.log('查看用户详情:', userId);
    };
});