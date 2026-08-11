<?php
require_once __DIR__ . '/config.php';

// Fetch categories and initial stats server-side
$cats_json = api_get('/categories/');
$cats = $cats_json ? json_decode($cats_json, true)['items'] ?? [] : [];
$landscape_count = 0;
$wp_json = api_get('/wallpapers/?device_type=landscape&size=1');
if ($wp_json) {
    $d = json_decode($wp_json, true);
    $landscape_count = $d['total'] ?? 0;
}
?><!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title><?= SITE_NAME ?> - 壁纸浏览</title>
<link rel="icon" type="image/png" href="<?= LOGO_PATH ?>">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--p:#ff6b6b;--pd:#ee5a24;--bg:#ffffff;--bg2:#f8f9fa;--text:#212529;--t2:#6c757d;--border:#dee2e6;--r:12px;--s:0 2px 12px rgba(0,0,0,.06)}
html{scroll-behavior:smooth}
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei','Helvetica Neue',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}

/* Header */
.header{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(255,255,255,.95);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);height:56px;display:flex;align-items:center;padding:0 16px}
.header-inner{max-width:1200px;width:100%;margin:0 auto;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:8px;font-weight:700;font-size:16px;text-decoration:none;color:var(--text)}
.logo img{width:28px;height:28px;border-radius:6px}
.header-actions{display:flex;align-items:center;gap:8px}
.btn{display:inline-flex;align-items:center;gap:5px;padding:7px 16px;border-radius:20px;font-size:13px;font-weight:600;text-decoration:none;border:none;cursor:pointer;transition:.2s}
.btn-sm{padding:5px 12px;font-size:12px}
.btn-p{background:var(--p);color:#fff}
.btn-p:hover{opacity:.9}
.btn-o{background:transparent;border:1px solid var(--border);color:var(--t2)}
.btn-o:hover{border-color:var(--p);color:var(--p)}
.btn-ghost{background:transparent;color:var(--t2)}
.btn-ghost:hover{color:var(--text)}
.user-info{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--t2)}

/* Filters */
.filters{position:fixed;top:56px;left:0;right:0;z-index:99;background:var(--bg);border-bottom:1px solid var(--border);padding:10px 16px}
.filters-inner{max-width:1200px;margin:0 auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.filter-device{display:inline-flex;gap:4px;margin-right:8px}
.filter-sep{display:inline-block;width:1px;height:16px;background:var(--border);margin:0 8px;vertical-align:middle}
.filter-btn{padding:5px 14px;border-radius:16px;font-size:12px;border:1px solid var(--border);background:var(--bg);color:var(--t2);cursor:pointer;transition:.2s}
.filter-btn:hover{border-color:var(--p);color:var(--p)}
.filter-btn.active{background:var(--p);border-color:var(--p);color:#fff}
.filter-sort{font-size:12px;color:var(--t2);margin-left:auto;display:flex;align-items:center;gap:6px}
.filter-sort select{padding:4px 8px;border-radius:6px;border:1px solid var(--border);font-size:12px;color:var(--text);background:var(--bg);outline:none}

/* Main */
.main{padding-top:110px;max-width:1200px;margin:0 auto;padding-left:16px;padding-right:16px}

/* Wallpaper Grid */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;padding-bottom:40px}
.wp-card{position:relative;border-radius:var(--r);overflow:hidden;background:var(--bg2);border:1px solid var(--border);cursor:pointer;transition:.25s;height:200px}
.wp-card:hover{box-shadow:0 8px 30px rgba(0,0,0,.12);transform:translateY(-2px)}
.wp-card img{width:100%;height:100%;object-fit:cover;display:block}
.wp-overlay{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.7));padding:12px;color:#fff;font-size:12px;opacity:0;transition:.25s}
.wp-card:hover .wp-overlay{opacity:1}
.wp-overlay .wp-meta{display:flex;justify-content:space-between;align-items:center}
.wp-overlay .wp-stats{display:flex;gap:10px;font-size:11px}
.wp-card .lock-icon{position:absolute;top:8px;right:8px;background:rgba(0,0,0,.5);color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px}
.wp-card .res-badge{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.5);color:#fff;padding:2px 8px;border-radius:6px;font-size:10px}

/* Login Modal */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:var(--bg);border-radius:var(--r);padding:32px;width:360px;max-width:90vw;box-shadow:0 20px 60px rgba(0,0,0,.15)}
.modal h2{font-size:20px;font-weight:700;margin-bottom:4px;text-align:center}
.modal .sub{color:var(--t2);font-size:13px;text-align:center;margin-bottom:20px}
.modal input{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:8px;font-size:14px;outline:none;margin-bottom:10px}
.modal input:focus{border-color:var(--p)}
.modal .btn{width:100%;justify-content:center;padding:10px}
.modal .switch{text-align:center;margin-top:12px;font-size:13px;color:var(--t2)}
.modal .switch a{color:var(--p);cursor:pointer;text-decoration:none}
.modal .msg{text-align:center;font-size:13px;min-height:20px;margin-bottom:8px}
.modal .msg.error{color:#e74c3c}
.modal .msg.success{color:#27ae60}

/* Detail Modal */
.detail-modal .modal{width:900px;max-width:95vw;padding:0;overflow:hidden;display:flex;flex-direction:column;max-height:90vh}
.detail-top{display:flex;flex-direction:row;flex:1;min-height:0}
.detail-img{flex:1;background:var(--bg2);display:flex;align-items:center;justify-content:center;min-height:400px;max-height:70vh}
.detail-img img{width:100%;height:100%;object-fit:cover;cursor:zoom-in;transition:.3s}
.detail-side{width:280px;padding:20px;border-left:1px solid var(--border);overflow-y:auto;flex-shrink:0}
.detail-side h3{font-size:16px;font-weight:600;margin-bottom:4px}
.detail-side .meta{color:var(--t2);font-size:13px;margin-bottom:12px;line-height:1.8}
.detail-side .actions{display:flex;flex-direction:column;gap:8px}
.detail-side .actions .btn{width:100%;justify-content:center}
.detail-close{position:absolute;top:12px;right:12px;width:32px;height:32px;border-radius:50%;border:none;background:rgba(0,0,0,.5);color:#fff;font-size:16px;cursor:pointer;z-index:10}
.detail-close:hover{background:rgba(0,0,0,.7)}

/* Pager */
.pager{display:flex;align-items:center;justify-content:center;gap:12px;padding:20px 0 40px}
.pager button{padding:8px 18px;border-radius:20px;border:1px solid var(--border);background:var(--bg);color:var(--text);cursor:pointer;font-size:13px;transition:.2s}
.pager button:hover{border-color:var(--p);color:var(--p)}
.pager button:disabled{opacity:.4;cursor:not-allowed}
.pager span{font-size:13px;color:var(--t2)}

/* Loading */
.loading{text-align:center;padding:60px;color:var(--t2);font-size:14px}
.loading .spinner{display:inline-block;width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--p);border-radius:50%;animation:spin .8s linear infinite;margin-bottom:12px}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:80px 20px;color:var(--t2)}
.empty .icon{font-size:48px;margin-bottom:12px}

/* Footer */
.footer{background:var(--bg2);border-top:1px solid var(--border);padding:32px 16px 24px;text-align:center;font-size:12px;color:var(--t2);line-height:1.8}
.footer a{color:var(--t2);text-decoration:none}
.footer a:hover{color:var(--p)}

/* Toast */
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:300;background:#333;color:#fff;padding:10px 24px;border-radius:20px;font-size:13px;opacity:0;transition:.3s}
.toast.show{opacity:1}

/* Responsive */
@media(max-width:768px){
  .grid{grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}
  .detail-top{flex-direction:column}
  .detail-side{width:100%;border-left:none;border-top:1px solid var(--border);padding:16px}
  .detail-img{min-height:200px}
  .filters-inner{gap:6px}
}
@media(max-width:480px){
  .grid{grid-template-columns:repeat(2,1fr);gap:8px}
  .wp-card{height:140px}
}
</style>
</head>
<body>

<!-- Header -->
<header class="header">
  <div class="header-inner">
    <a href="/" class="logo"><img src="<?= LOGO_PATH ?>" alt=""><?= SITE_NAME ?></a>
    <div class="header-actions" id="headerActions">
      <a href="<?= APP_URL ?>" class="btn btn-ghost btn-sm">官网</a>
      <span id="loginStatus"></span>
    </div>
  </div>
</header>

<!-- Filters -->
<div class="filters">
  <div class="filters-inner">
    <div class="filter-device">
      <button class="filter-btn active" data-device="all">全部</button>
      <button class="filter-btn" data-device="landscape">横屏</button>
      <button class="filter-btn" data-device="portrait">竖屏</button>
    </div>
    <span class="filter-sep"></span>
    <button class="filter-btn active" data-cat="all">全部</button>
    <?php foreach ($cats as $c): ?>
    <button class="filter-btn" data-cat="<?= $c['id'] ?>"><?= htmlspecialchars($c['name']) ?></button>
    <?php endforeach; ?>
    <div class="filter-sort">
      <select id="sortSelect">
        <option value="newest">最新</option>
        <option value="downloads">最热</option>
        <option value="likes">最多点赞</option>
      </select>
    </div>
  </div>
</div>

<!-- Main -->
<div class="main">
  <div class="grid" id="grid"><div class="loading"><div class="spinner"></div>加载中...</div></div>
  <div class="pager" id="pager">
    <button id="prevBtn" onclick="goPage(-1)" disabled>上一页</button>
    <span id="pageInfo"></span>
    <button id="nextBtn" onclick="goPage(1)">下一页</button>
  </div>
</div>

<!-- Footer -->
<div class="footer">
  <p><a href="<?= APP_URL ?>"><?= SITE_NAME ?></a> · 横屏壁纸专区 · 登录后下载收藏</p>
  <p style="margin-top:4px">© 2026 多点壁纸</p>
</div>

<!-- Login Modal -->
<div class="modal-overlay" id="loginModal">
  <div class="modal">
    <h2>🔐 登录</h2>
    <p class="sub">登录后即可下载和收藏壁纸</p>
    <div class="msg" id="loginMsg"></div>
    <input type="text" id="loginUser" placeholder="用户名" autocomplete="off">
    <input type="password" id="loginPass" placeholder="密码">
    <button class="btn btn-p" onclick="doLogin()">登录</button>
    <div class="switch">还没有账号？<a onclick="showRegister()">立即注册</a></div>
  </div>
</div>

<!-- Register Modal -->
<div class="modal-overlay" id="registerModal">
  <div class="modal">
    <h2>📝 注册</h2>
    <p class="sub">创建账号，收藏你喜爱的壁纸</p>
    <div class="msg" id="regMsg"></div>
    <input type="text" id="regUser" placeholder="用户名（3-50位）" autocomplete="off">
    <input type="password" id="regPass" placeholder="密码（至少6位）">
    <button class="btn btn-p" onclick="doRegister()">注册</button>
    <div class="switch">已有账号？<a onclick="showLogin()">去登录</a></div>
  </div>
</div>

<!-- Detail Modal -->
<div class="modal-overlay detail-modal" id="detailModal">
  <div class="modal">
    <button class="detail-close" onclick="closeDetail()">✕</button>
    <div class="detail-top">
      <div class="detail-img"><img id="detailImg" src="" alt=""></div>
      <div class="detail-side" id="detailSide">
        <h3 id="detailTitle"></h3>
        <div class="meta" id="detailMeta"></div>
        <div class="actions" id="detailActions"></div>
      </div>
    </div>
  </div>
</div>

<!-- Image full-size toggle -->
<script>
document.addEventListener('click', function(e) {
  // Click on detail image to toggle full size
  var img = e.target.closest('#detailImg');
  if (img) {
    img.style.objectFit = img.style.objectFit === 'contain' ? 'cover' : 'contain';
    img.style.cursor = 'zoom-out';
    return;
  }
  // Click on overlay background to close
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('show');
  }
  // Click on close button
  if (e.target.classList.contains('detail-close') || e.target.closest('.detail-close')) {
    closeDetail();
  }
});
</script>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
// ===== State =====
let token = localStorage.getItem('wp_token') || '';
let currentPage = 1;
let currentCat = 'all';
let currentSort = 'newest';
let currentDevice = 'all';

// ===== Init =====
updateLoginUI();
loadWallpapers();

// ===== Wallpaper Loading =====
async function loadWallpapers() {
  const grid = document.getElementById('grid');
  grid.innerHTML = '<div class="loading"><div class="spinner"></div>加载中...</div>';
  
  let url = `<?= API_BASE ?>/wallpapers/?page=${currentPage}&size=24&sort=${currentSort}`;
  if (currentDevice !== 'all') url += `&device_type=${currentDevice}`;
  if (currentCat !== 'all') url += `&category=${currentCat}`;
  
  try {
    const r = await fetch(url);
    const d = await r.json();
    if (!d.items || d.items.length === 0) {
      grid.innerHTML = '<div class="empty"><div class="icon">🖼️</div>暂无壁纸</div>';
      document.getElementById('pager').style.display = 'none';
      return;
    }
    document.getElementById('pager').style.display = '';
    grid.innerHTML = d.items.map(w => renderCard(w)).join('');
    document.getElementById('pageInfo').textContent = `第${d.page}页 / 共${d.pages}页 · ${d.total}张`;
    document.getElementById('prevBtn').disabled = d.page <= 1;
    document.getElementById('nextBtn').disabled = d.page >= d.pages;
    currentPage = d.page;
  } catch(e) {
    grid.innerHTML = '<div class="empty"><div class="icon">⚠️</div>加载失败</div>';
  }
}

function renderCard(w) {
  const thumb = w.thumbnail_small_url || w.thumbnail_720_url;
  const locked = !token;
  return `<div class="wp-card" onclick="openDetail(${JSON.stringify(w).replace(/"/g,'&quot;')})">
    <img src="${thumb}" alt="${escHtml(w.title)}" loading="lazy">
    <span class="res-badge">${w.resolution || ''}</span>
    ${locked ? '<span class="lock-icon">🔒</span>' : ''}
    <div class="wp-overlay">
      <div class="wp-meta">
        <span>${escHtml(w.title).substring(0,20)}</span>
        <div class="wp-stats">
          <span>♥ ${w.likes}</span>
          <span>⬇ ${w.downloads}</span>
        </div>
      </div>
    </div>
  </div>`;
}

function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ===== Detail =====
let currentWallpaper = null;

function openDetail(w) {
  currentWallpaper = w;
  const imgSrc = w.thumbnail_720_url || w.thumbnail_small_url;
  document.getElementById('detailImg').src = imgSrc;
  document.getElementById('detailTitle').textContent = w.title || '壁纸';
  const meta = document.getElementById('detailMeta');
  meta.innerHTML = `分辨率: ${w.resolution || '-'}<br>大小: ${w.file_size ? Math.round(w.file_size/1024) + 'KB' : '-'}<br>下载: ${w.downloads || 0} · 点赞: ${w.likes || 0}`;
  
  const actions = document.getElementById('detailActions');
  if (token) {
    actions.innerHTML = `<button class="btn btn-p" onclick="doDownload(${w.id})">⬇ 下载原图</button>
      <button class="btn btn-o" onclick="doLike(${w.id})">♥ ${w.liked ? '已赞' : '点赞'}</button>`;
  } else {
    actions.innerHTML = `<button class="btn btn-p" onclick="showLogin()">🔐 登录后下载</button>
      <button class="btn btn-o" onclick="showLogin()">♥ 登录后点赞</button>`;
  }
  
  document.getElementById('detailModal').classList.add('show');
}

function closeDetail() {
  document.getElementById('detailModal').classList.remove('show');
}

// ===== Login / Register =====
function showLogin() {
  closeDetail();
  document.getElementById('registerModal').classList.remove('show');
  document.getElementById('loginMsg').textContent = '';
  document.getElementById('loginModal').classList.add('show');
}

function showRegister() {
  document.getElementById('loginModal').classList.remove('show');
  document.getElementById('regMsg').textContent = '';
  document.getElementById('registerModal').classList.add('show');
}

function closeModals() {
  document.getElementById('loginModal').classList.remove('show');
  document.getElementById('registerModal').classList.remove('show');
}

async function doLogin() {
  const u = document.getElementById('loginUser').value;
  const p = document.getElementById('loginPass').value;
  if (!u || !p) { document.getElementById('loginMsg').textContent = '请填写用户名和密码'; return; }
  document.getElementById('loginMsg').textContent = '登录中...';
  try {
    const r = await fetch('<?= API_BASE ?>/users/login', {
      method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body: 'username='+encodeURIComponent(u)+'&password='+encodeURIComponent(p)
    });
    const d = await r.json();
    if (d.access_token) {
      token = d.access_token;
            closeModals();
      updateLoginUI();
      loadWallpapers();
      showToast('✅ 登录成功');
      if (currentWallpaper) openDetail(currentWallpaper);
    } else {
      document.getElementById('loginMsg').className = 'msg error';
      document.getElementById('loginMsg').textContent = d.detail || '登录失败';
    }
  } catch(e) {
    document.getElementById('loginMsg').className = 'msg error';
    document.getElementById('loginMsg').textContent = '网络错误';
  }
}

async function doRegister() {
  const u = document.getElementById('regUser').value;
  const p = document.getElementById('regPass').value;
  if (!u || u.length < 3) { document.getElementById('regMsg').textContent = '用户名至少3位'; return; }
  if (!p || p.length < 6) { document.getElementById('regMsg').textContent = '密码至少6位'; return; }
  document.getElementById('regMsg').textContent = '注册中...';
  try {
    const r = await fetch('<?= API_BASE ?>/users/register', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({username: u, password: p})
    });
    const d = await r.json();
    if (d.access_token) {
      token = d.access_token;
            closeModals();
      updateLoginUI();
      loadWallpapers();
      showToast('✅ 注册成功');
    } else {
      document.getElementById('regMsg').className = 'msg error';
      document.getElementById('regMsg').textContent = d.detail || '注册失败';
    }
  } catch(e) {
    document.getElementById('regMsg').className = 'msg error';
    document.getElementById('regMsg').textContent = '网络错误';
  }
}

// ===== Actions =====
function doDownload(id) {
  if (!token) { showLogin(); return; }
  window.open('/download.php?id=' + id + '&token=' + encodeURIComponent(token), '_blank');
  showToast('\u2705 \u4e0b\u8f7d\u5df2\u5f00\u59cb');
}

async function doLike(id) {
  if (!token) { showLogin(); return; }
  try {
    const r = await fetch(`<?= API_BASE ?>/wallpapers/${id}/like`, {
      method:'POST',
      headers: {'Authorization': 'Bearer '+token}
    });
    if (r.ok) {
      showToast('✅ 操作成功');
      loadWallpapers();
      if (currentWallpaper && currentWallpaper.id === id) {
        currentWallpaper = null;
        closeDetail();
      }
    } else if (r.status === 401) {
      token = ''; updateLoginUI(); showLogin();
    }
  } catch(e) {}
}

// ===== UI =====
function updateLoginUI() {
  const s = document.getElementById('loginStatus');
  if (token) {
    s.innerHTML = `<span class="user-info">👤 已登录 <button class="btn btn-ghost btn-sm" onclick="doLogout()">退出</button></span>`;
  } else {
    s.innerHTML = `<button class="btn btn-p btn-sm" onclick="showLogin()">登录</button>`;
  }
}

async function doLogout() {
  token = '';
    updateLoginUI();
  loadWallpapers();
  showToast('已退出');
}

function goPage(dir) {
  currentPage += dir;
  loadWallpapers();
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

// ===== Filter Events =====
document.querySelectorAll('.filter-btn[data-cat]').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.filter-btn[data-cat]').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    currentCat = this.dataset.cat;
    currentPage = 1;
    loadWallpapers();
  });
});

document.querySelectorAll('.filter-btn[data-device]').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.filter-btn[data-device]').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    currentDevice = this.dataset.device;
    currentPage = 1;
    loadWallpapers();
  });
});

document.getElementById('sortSelect').addEventListener('change', function() {
  currentSort = this.value;
  currentPage = 1;
  loadWallpapers();
});

// ===== Keyboard =====
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDetail();
});


</script>

</body>
</html>
