"""Web-based admin dashboard router."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Inline HTML Templates ────────────────────────────────────────────────────

ADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>多点壁纸 - 管理后台登录</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#0f0f23;min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#16162a;border-radius:16px;padding:40px;width:360px;text-align:center}
.box h2{color:#fff;margin-bottom:8px}
.box p{color:#666;font-size:13px;margin-bottom:28px}
input{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none;margin-bottom:12px}
input:focus{border-color:#ff6b6b}
.btn{width:100%;height:44px;background:#ff6b6b;color:#fff;border:none;border-radius:22px;font-size:15px;cursor:pointer;margin-top:8px}
.btn:hover{opacity:0.9}
.msg{color:#ff4757;font-size:12px;margin-top:10px;min-height:18px}
</style>
</head>
<body>
<div class="box">
  <h2>🖼️ 多点壁纸</h2>
  <p>管理员登录</p>
  <input type="text" id="username" placeholder="用户名" autocomplete="off"/>
  <input type="password" id="password" placeholder="密码" autocomplete="off"/>
  <button class="btn" onclick="doLogin()">登录</button>
  <div class="msg" id="msg"></div>
</div>
<script>
async function doLogin() {
  const u = document.getElementById('username').value;
  const p = document.getElementById('password').value;
  if (!u || !p) { document.getElementById('msg').textContent='请填写用户名和密码'; return; }
  const fd = new FormData();
  fd.append('username', u); fd.append('password', p);
  const r = await fetch('/api/v1/users/login', {method:'POST', body:fd});
  const d = await r.json();
  if (r.ok && d.access_token) {
    localStorage.setItem('admin_token', d.access_token);
    document.cookie = 'admin_token=' + d.access_token + ';path=/;max-age=86400;SameSite=Lax';
    window.location.href = '/admin/';
  } else {
    document.getElementById('msg').textContent = d.detail || '登录失败';
  }
}
document.getElementById('password').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });
if (localStorage.getItem('admin_token')) window.location.href = '/admin/';
</script>
</div>
</body>
</html>"""


HEADER_COMMON = """<div class="header">
  <button class="menu-toggle" onclick="toggleSidebar()">☰</button>
  <h1>🖼️ 多点壁纸 <span>管理后台</span></h1>
  <span style="flex:1"></span>
  <button class="logout-btn" onclick="localStorage.removeItem('admin_token');document.cookie='admin_token=;path=/;max-age=0';window.location.href='/admin/login'">退出</button>
</div>"""


SIDEBAR_COMMON = """<div class="sidebar" id="sidebar">
  <nav class="nav">
    <div class="nav-group">
      <span class="nav-title">内容</span>
      <a href="/admin/" id="navDash" data-icon="📊">📊 数据概览</a>
      <a href="/admin/submissions" id="navSub" data-icon="✅">✅ 审核</a>
      <a href="/admin/wallpapers" id="navWp" data-icon="🖼️">🖼️ 壁纸管理</a>
      <a href="/admin/categories" id="navCat" data-icon="📁">📁 分类管理</a>
      <a href="/admin/upload" id="navUpload" data-icon="⬆️">⬆️ 上传壁纸</a>
    </div>
    <div class="nav-group">
      <span class="nav-title">用户</span>
      <a href="/admin/users" id="navUsers" data-icon="👥">👥 用户管理</a>
      <a href="/admin/feedback" id="navFb" data-icon="💬">💬 用户反馈</a>
    </div>
    <div class="nav-group">
      <span class="nav-title">设置</span>
      <a href="/admin/config" id="navConfig" data-icon="🔔">🔔 通知配置</a>
      <a href="/admin/config/site" id="navSiteCfg" data-icon="🌐">🌐 站点设置</a>
      <a href="/admin/config/auth" id="navAuth" data-icon="🔐">🔐 认证配置</a>
      <a href="/admin/config/storage" id="navStorage" data-icon="💾">💾 存储配置</a>
      <a href="/admin/config/smtp" id="navSmtp" data-icon="📧">📧 邮箱配置</a>
      <a href="/admin/docs" id="navDocs" data-icon="📚" target="_blank">📚 API 文档</a>
      <a href="/admin/config/sms" id="navSms" data-icon="📱">📱 短信配置</a>
      <a href="/admin/config/debug" id="navDbgCfg" data-icon="🔍">🔍 调试配置</a>
      <a href="/admin/debug-logs" id="navDbgLog" data-icon="📋">📋 调试日志</a>
    </div>
  </nav>
</div>"""

COMMON_STYLES = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#0f0f23;color:#fff;min-height:100vh;display:flex}
/* ── Sidebar ── */
.sidebar{width:220px;background:#16162a;border-right:1px solid #2a2a3e;position:fixed;top:0;left:0;bottom:0;z-index:20;overflow-y:auto;overflow-x:hidden;transition:width .25s}
.sidebar.collapsed{width:60px}
.sidebar.collapsed .nav a{font-size:0;padding:12px 8px;text-align:center;border-left:none}
.sidebar.collapsed .nav a::before{font-size:18px;display:block;text-align:center}
.sidebar.collapsed .nav-title{display:none}
.sidebar.collapsed .nav a::after{content:attr(data-icon);font-size:18px}
/* ── Nav ── */
.nav{padding:8px 0}
.nav-group{margin-bottom:4px}
.nav-title{display:block;font-size:11px;color:#666;padding:8px 16px 4px;text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap}
.nav a{display:flex;align-items:center;gap:8px;padding:10px 16px;color:#aaa;text-decoration:none;font-size:13px;transition:.2s;border-left:3px solid transparent;white-space:nowrap}
.nav a:hover,.nav a.active{background:#1a1a2e;color:#fff;border-left-color:#ff6b6b}
/* ── Header ── */
.header{height:56px;display:flex;align-items:center;gap:12px;padding:0 16px;background:#16162a;border-bottom:1px solid #2a2a3e;position:sticky;top:0;z-index:10}
.header h1{font-size:18px;font-weight:bold;color:#fff;white-space:nowrap}
.header h1 span{color:#ff6b6b}
.menu-toggle{background:transparent;border:1px solid #444;color:#fff;padding:6px 10px;border-radius:8px;font-size:16px;cursor:pointer}
.logout-btn{background:transparent;border:1px solid #444;color:#888;padding:6px 16px;border-radius:20px;font-size:13px;cursor:pointer;white-space:nowrap}
/* ── Main ── */
.main{flex:1;margin-left:220px;transition:margin-left .25s;min-width:0}
.main.expanded{margin-left:60px}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:15}
/* ── Common components ── */
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;padding:24px}
.card{background:#16162a;border-radius:12px;padding:20px;text-align:center}
.card .num{font-size:32px;font-weight:bold;color:#ff6b6b}
.card .label{font-size:12px;color:#666;margin-top:6px}
.section{padding:0 24px 24px}
.section h2{font-size:15px;color:#888;margin-bottom:12px;padding-top:16px}
.list{display:flex;flex-direction:column;gap:10px}
.item{display:flex;align-items:center;background:#16162a;border-radius:12px;padding:14px;gap:14px}
.item img{width:60px;height:60px;border-radius:8px;object-fit:cover;background:#1a1a2e;flex-shrink:0}
.item .info{flex:1;min-width:0}
.item .title{font-size:14px;color:#fff;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.item .meta{font-size:12px;color:#666;margin-top:4px}
.item .actions{display:flex;gap:8px;flex-shrink:0;flex-wrap:wrap}
.btn{padding:6px 14px;border-radius:16px;font-size:12px;border:none;cursor:pointer}
.btn-ok{background:#2ecc71;color:#fff}
.btn-no{background:#e74c3c;color:#fff}
.btn-warn{background:#ff9800;color:#fff}
.btn-del{background:transparent;border:1px solid #e74c3c;color:#e74c3c}
.btn-del:hover{background:#e74c3c;color:#fff}
.btn-secondary{background:transparent;border:1px solid #444;color:#888}
.btn-test{background:transparent;border:1px solid #2ecc71;color:#2ecc71;padding:6px 14px;border-radius:16px;font-size:12px;cursor:pointer;margin-top:12px}
.btn-test:hover{background:#2ecc71;color:#fff}
.tabs{padding:16px 24px 0;display:flex;gap:8px;flex-wrap:wrap}
.tab{padding:8px 18px;border-radius:20px;font-size:13px;cursor:pointer;border:1px solid #2a2a3e;color:#666;transition:.2s}
.tab.active,.tab:hover{background:#ff6b6b;color:#fff;border-color:#ff6b6b}
.content{padding:16px 24px}
.pager{display:flex;align-items:center;justify-content:center;gap:12px;padding:20px}
.pager button{padding:6px 16px;border-radius:16px;border:1px solid #2a2a3e;background:#16162a;color:#aaa;cursor:pointer;font-size:13px}
.pager button:disabled{opacity:0.4;cursor:not-allowed}
.pager span{color:#666;font-size:13px}
.empty{text-align:center;padding:60px;color:#555;font-size:14px}
.tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;margin-right:4px}
.tag-pending,.tag-unlisted{background:#2a2a3e;color:#ff9800}
.tag-approved{background:#1a3a2a;color:#2ecc71}
.tag-rejected{background:#3a1a1a;color:#e74c3c}
.top{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.top input{flex:1;min-width:160px;height:38px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:13px;padding:0 12px;outline:none}
.top input:focus{border-color:#ff6b6b}
.top select{height:38px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:13px;padding:0 10px;outline:none}
.top button{padding:0 18px;height:38px;background:#ff6b6b;color:#fff;border:none;border-radius:8px;font-size:13px;cursor:pointer}
.table-wrap{overflow-x:auto;width:100%}
/* ── Responsive ── */
@media (max-width:900px){
  .sidebar{transform:translateX(-100%);width:220px}
  .sidebar.collapsed{width:220px}
  .menu-open .sidebar{transform:translateX(0)}
  .main{margin-left:0!important}
  .menu-open .overlay{display:block}
  .stats{grid-template-columns:repeat(2,1fr);padding:16px;gap:12px}
  .content{padding:12px}
  .section{padding:0 16px 16px}
  .top{gap:8px}
  .top input,.top select{min-width:120px}
  .item{flex-direction:column;align-items:flex-start;gap:10px}
  .item img{width:100%;height:auto;max-height:180px}
  .item .actions{width:100%;justify-content:flex-end}
}
@media (max-width:480px){
  .stats{grid-template-columns:1fr}
  .header h1{font-size:15px}
  .header h1 span{display:none}
}
.batch-bar{display:flex;align-items:center;gap:8px;padding:10px 0;margin-bottom:8px;flex-wrap:wrap}
.batch-bar select,.batch-bar input{height:32px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:6px;color:#fff;font-size:12px;padding:0 8px}
.batch-bar button{padding:6px 14px;border-radius:6px;border:none;font-size:12px;cursor:pointer}
.batch-bar span{color:#ff6b6b;font-size:13px;font-weight:bold;min-width:60px}
.wp-cb{width:18px;height:18px;accent-color:#ff6b6b;cursor:pointer;margin-right:8px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:999}
.modal-box{background:#1e1e35;border-radius:12px;padding:24px;width:420px;max-width:90%}
.modal-box h3{color:#fff;margin-bottom:16px}
.modal-box label{display:block;color:#888;font-size:12px;margin:8px 0 4px}
.modal-box input,.modal-box textarea,.modal-box select{width:100%;padding:8px 12px;background:#0f0f23;border:1px solid #2a2a3e;border-radius:6px;color:#fff;font-size:13px;margin-bottom:4px}
.modal-box textarea{resize:vertical}
.modal-actions{display:flex;gap:8px;margin-top:16px;justify-content:flex-end}
.modal-actions button{padding:8px 20px;border-radius:8px;border:none;font-size:13px;cursor:pointer}"""


PAGE_WRAPPER = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{TITLE} - 多点壁纸管理后台</title>
<style>{STYLES}</style>
</head>
<body>
{SIDEBAR}
<div class="overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="main" id="mainContent">
{HEADER}
{CONTENT}
</div>
<script>
(function(){
  const saved = localStorage.getItem('sidebar_collapsed');
  if (saved === '1') {
    document.getElementById('sidebar').classList.add('collapsed');
    document.getElementById('mainContent').classList.add('expanded');
  }
})();
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const mc = document.getElementById('mainContent');
  if (window.innerWidth <= 900) {
    document.body.classList.toggle('menu-open');
  } else {
    sb.classList.toggle('collapsed');
    mc.classList.toggle('expanded');
    localStorage.setItem('sidebar_collapsed', sb.classList.contains('collapsed') ? '1' : '0');
  }
}
function closeSidebar() {
  document.body.classList.remove('menu-open');
}
const token = localStorage.getItem('admin_token');
if (!token) { window.location.href='/admin/login'; throw 'no token'; }
async function api(path, opts={}) {
  const r = await fetch(path, {...opts, headers:{...opts.headers||{}, 'Authorization':'Bearer '+token}});
  if (r.status===401||r.status===403) { localStorage.removeItem('admin_token'); window.location.href='/admin/login'; }
  return r;
}
(function setActiveNav(){
  const path = window.location.pathname;
  const map = {'/admin/':'navDash','/admin/submissions':'navSub','/admin/wallpapers':'navWp','/admin/categories':'navCat','/admin/upload':'navUpload','/admin/users':'navUsers','/admin/config':'navConfig','/admin/config/site':'navSiteCfg','/admin/config/auth':'navAuth','/admin/config/storage':'navStorage','/admin/config/smtp':'navSmtp','/admin/config/sms':'navSms','/admin/config/debug':'navDbgCfg','/admin/debug-logs':'navDbgLog'};
  const id = map[path];
  if (!id) return;
  document.querySelectorAll('.nav a').forEach(a => a.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
})();
function esc(s) { if(!s)return''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function imgUrl(wp) {
  const u = wp.thumbnail_small_url || wp.thumbnail_720_url || wp.original_url || '';
  if (u.startsWith('http://') || u.startsWith('https://')) return u;
  return window.location.origin + u;
}
function formatTime(s) { try{return new Date(s).toLocaleString('zh-CN');}catch(e){return s||'';} }
function fmtStatus(s) {
  const m = {'pending':'⏳待审核','approved':'✅已上架','rejected':'❌已拒绝','unlisted':'📴已下架'};
  return m[s]||s;
}
{SCRIPTS}
</script>
</body>
</html>"""


def _page(title: str, content: str, scripts: str = "") -> str:
    return PAGE_WRAPPER.replace("{TITLE}", title)\
        .replace("{STYLES}", COMMON_STYLES)\
        .replace("{SIDEBAR}", SIDEBAR_COMMON)\
        .replace("{HEADER}", HEADER_COMMON)\
        .replace("{CONTENT}", content)\
        .replace("{SCRIPTS}", scripts)


# Shared standalone page prefix/suffix with sidebar layout
_STANDALONE_PRE = SIDEBAR_COMMON + """<div class="overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="main" id="mainContent">
""" + HEADER_COMMON

_STANDALONE_JS_TOP = """(function(){
  const saved = localStorage.getItem('sidebar_collapsed');
  if (saved === '1') {
    document.getElementById('sidebar').classList.add('collapsed');
    document.getElementById('mainContent').classList.add('expanded');
  }
})();
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const mc = document.getElementById('mainContent');
  if (window.innerWidth <= 900) {
    document.body.classList.toggle('menu-open');
  } else {
    sb.classList.toggle('collapsed');
    mc.classList.toggle('expanded');
    localStorage.setItem('sidebar_collapsed', sb.classList.contains('collapsed') ? '1' : '0');
  }
}
function closeSidebar() { document.body.classList.remove('menu-open'); }
const token = localStorage.getItem('admin_token');
if (!token) { window.location.href='/admin/login'; throw 'no token'; }
function esc(s) { if(!s)return''; return String(s).replace(/\u0026/g,'\u0026amp;').replace(/\u003c/g,'\u0026lt;').replace(/\u003e/g,'\u0026gt;'); }
function formatTime(s) { try{return new Date(s).toLocaleString('zh-CN');}catch(e){return s||'';} }
async function api(path, opts={}) {
  const r = await fetch(path, {...opts, headers:{...opts.headers||{}, 'Authorization':'Bearer '+token}});
  if (r.status===401||r.status===403) { localStorage.removeItem('admin_token'); window.location.href='/admin/login'; }
  return r;
}
(function setActiveNav(){
  const path = window.location.pathname;
  const map = {'/admin/':'navDash','/admin/submissions':'navSub','/admin/wallpapers':'navWp','/admin/categories':'navCat','/admin/upload':'navUpload','/admin/users':'navUsers','/admin/config':'navConfig','/admin/config/site':'navSiteCfg','/admin/config/auth':'navAuth','/admin/config/storage':'navStorage','/admin/config/smtp':'navSmtp','/admin/config/sms':'navSms','/admin/config/debug':'navDbgCfg','/admin/debug-logs':'navDbgLog'};
  const id = map[path];
  if (!id) return;
  document.querySelectorAll('.nav a').forEach(a => a.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
})();"""


# ─── Dashboard ────────────────────────────────────────────────────────────────

DASHBOARD_CONTENT = """<div class="stats">
    <div class="card"><div class="num" id="statPending">-</div><div class="label">待审核</div></div>
    <div class="card"><div class="num" id="statApproved">-</div><div class="label">已上架</div></div>
    <div class="card"><div class="num" id="statRejected">-</div><div class="label">已拒绝</div></div>
    <div class="card"><div class="num" id="statUnlisted">-</div><div class="label">已下架</div></div>
    <div class="card"><div class="num" id="statTotal">-</div><div class="label">壁纸总数</div></div>
  </div>
  <div class="section">
    <h2>最近投稿（待审核）</h2>
    <div class="list" id="recentList"><div class="empty">加载中...</div></div>
  </div>"""

DASHBOARD_SCRIPTS = """
async function loadStats() {
  try {
    const [p,a,re,un] = await Promise.all([
      api('/api/v1/admin/submissions?status=pending&size=1').then(r=>r.json()),
      api('/api/v1/admin/submissions?status=approved&size=1').then(r=>r.json()),
      api('/api/v1/admin/submissions?status=rejected&size=1').then(r=>r.json()),
      api('/api/v1/admin/submissions?status=unlisted&size=1').then(r=>r.json()),
    ]);
    document.getElementById('statPending').textContent=p.total||0;
    document.getElementById('statApproved').textContent=a.total||0;
    document.getElementById('statRejected').textContent=re.total||0;
    document.getElementById('statUnlisted').textContent=un.total||0;
    document.getElementById('statTotal').textContent=((p.total||0)+(a.total||0)+(re.total||0)+(un.total||0));
  } catch(e) {}
}
async function loadRecent() {
  const list = document.getElementById('recentList');
  try {
    const d = await (await api('/api/v1/admin/submissions?status=pending&size=20')).json();
    if (!d.items||d.items.length===0) { list.innerHTML='<div class="empty">暂无待审核投稿 🎉</div>'; return; }
      list.innerHTML = d.items.map(wp => `
      <div class="item">
        <img src="${imgUrl(wp)}" onerror="this.style.display='none'"/>
        <div class="info">
          <div class="title">${esc(wp.title)}</div>
          <div class="meta">${(wp.device_types||[]).join(' · ')} · 分类 ${(wp.category_ids||[]).join(', ')} · ${formatTime(wp.created_at)}</div>
          <div style="margin-top:4px">${(wp.tags||[]).map(t=>'<span class="tag tag-pending">'+esc(t)+'</span>').join('')}</div>
        </div>
        <div class="actions">
          <button class="btn btn-ok" onclick="review(${wp.id},true)">通过</button>
          <button class="btn btn-no" onclick="showReject(${wp.id})">拒绝</button>
        </div>
      </div>`).join('');
  } catch(e) { list.innerHTML='<div class="empty">加载失败</div>'; }
}
async function review(id, approve, reason='') {
  await api('/api/v1/admin/submissions/'+id, {method:'POST', body:JSON.stringify({approve,reject_reason:reason}),headers:{'Content-Type':'application/json'}});
  loadRecent(); loadStats();
}
function showReject(id) { const r=prompt('拒绝原因（可选）：'); review(id,false,r||''); }
loadStats(); loadRecent();
"""


# ─── Submissions (审核) ───────────────────────────────────────────────────────

SUBMISSIONS_CONTENT = """<div class="tabs">
  <div class="tab active" data-status="pending" onclick="setStatus('pending')">⏳ 待审核</div>
  <div class="tab" data-status="approved" onclick="setStatus('approved')">✅ 已上架</div>
  <div class="tab" data-status="rejected" onclick="setStatus('rejected')">❌ 已拒绝</div>
  <div class="tab" data-status="unlisted" onclick="setStatus('unlisted')">📴 已下架</div>
</div>
<div class="content">
  <div class="list" id="list"><div class="empty">加载中...</div></div>
  <div class="pager">
    <button id="prevBtn" onclick="changePage(-1)">上一页</button>
    <span id="pagerInfo"></span>
    <button id="nextBtn" onclick="changePage(1)">下一页</button>
  </div>
</div>
<div id="catModal" class="modal" style="display:none"><div class="modal-box">
  <h3>修改分类</h3>
  <input type="hidden" id="catEditId"/>
  <div id="catEditList" style="max-height:240px;overflow-y:auto"></div>
  <div class="modal-actions"><button onclick="saveCategories()" style="background:#ff6b6b;color:#fff">保存</button><button onclick="closeCatModal()">取消</button></div>
</div></div>"""

SUBMISSIONS_SCRIPTS = """
let currentStatus='pending', page=1, categories=[];
async function loadCategories() {
  try { const d = await (await api('/api/v1/admin/categories')).json(); categories = d.items||[]; } catch(e) {}
}
function catNames(ids) {
  if (!ids||ids.length===0) return '-';
  return ids.map(id=>(categories.find(c=>c.id===id)||{}).name||id).join(', ');
}
async function load() {
  const list = document.getElementById('list');
  const d = await (await api('/api/v1/admin/submissions?status='+currentStatus+'&page='+page+'&size=15')).json();
  if (!d.items||d.items.length===0) { list.innerHTML='<div class="empty">暂无内容</div>'; document.getElementById('pagerInfo').textContent=''; return; }
  list.innerHTML = d.items.map(wp => `
    <div class="item">
      <img src="${imgUrl(wp)}" onerror="this.style.display='none'"/>
      <div class="info">
        <div class="title">${esc(wp.title)}</div>
        <div class="meta">${(wp.device_types||[]).join(' · ')} · ${wp.width}x${wp.height} · 分类: ${catNames(wp.category_ids)} · ${formatTime(wp.created_at)}</div>
        <div style="margin-top:4px">${(wp.tags||[]).map(t=>'<span class="tag tag-'+currentStatus+'">'+esc(t)+'</span>').join('')}</div>
        ${wp.reject_reason?'<div style="margin-top:4px;font-size:11px;color:#e74c3c">拒绝原因: '+esc(wp.reject_reason)+'</div>':''}
      </div>
      <div class="actions">
        ${currentStatus==='pending'?`<button class="btn btn-ok" onclick="review(${wp.id},true)">通过</button>
        <button class="btn btn-no" onclick="doReject(${wp.id})">拒绝</button>
        <button class="btn btn-warn" onclick="openCatModal(${wp.id}, ${JSON.stringify(wp.category_ids||[]).replace(/"/g,'&quot;')})">分类</button>`:''}
        ${currentStatus==='approved'?`<button class="btn btn-warn" onclick="changeStatus(${wp.id},'unlisted')">下架</button>
        <button class="btn btn-warn" onclick="openCatModal(${wp.id}, ${JSON.stringify(wp.category_ids||[]).replace(/"/g,'&quot;')})">分类</button>`:''}
        ${currentStatus==='unlisted'?`<button class="btn btn-ok" onclick="changeStatus(${wp.id},'approved')">重新上架</button>
        <button class="btn btn-warn" onclick="openCatModal(${wp.id}, ${JSON.stringify(wp.category_ids||[]).replace(/"/g,'&quot;')})">分类</button>`:''}
        ${currentStatus==='rejected'?`<button class="btn btn-ok" onclick="changeStatus(${wp.id},'pending')">改为待审核</button>`:''}
      </div>
    </div>`).join('');
  document.getElementById('pagerInfo').textContent='第'+page+'页 / 共'+(d.pages||1)+'页 · '+(d.total||0)+'条';
  document.getElementById('prevBtn').disabled = page<=1;
  document.getElementById('nextBtn').disabled = page>=(d.pages||1);
}
function setStatus(s) { currentStatus=s; page=1; document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.status===s)); load(); }
function changePage(dir) { page+=dir; load(); }
async function review(id,approve,reason='') {
  await api('/api/v1/admin/submissions/'+id, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approve,reject_reason:reason})});
  load();
}
async function changeStatus(id,status) {
  const conf = {unlisted:'确定下架该壁纸？（不会删除文件）',approved:'确定重新上架该壁纸？',pending:'确定改为待审核？'};
  if (!confirm(conf[status]||'确定执行？')) return;
  await api('/api/v1/admin/wallpapers/'+id+'/status', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});
  load();
}
function doReject(id) { const r=prompt('拒绝原因（可选）：'); review(id,false,r||''); }
function openCatModal(id, selectedIds) {
  document.getElementById('catEditId').value = id;
  const box = document.getElementById('catEditList');
  box.innerHTML = categories.map(c => `
    <label style="display:flex;align-items:center;gap:8px;padding:8px 0;color:#fff;cursor:pointer">
      <input type="checkbox" class="cat-cb" value="${c.id}" ${(selectedIds||[]).includes(c.id)?'checked':''}/>
      ${esc(c.name)}
    </label>`).join('');
  document.getElementById('catModal').style.display='flex';
}
function closeCatModal() { document.getElementById('catModal').style.display='none'; }
async function saveCategories() {
  const id = parseInt(document.getElementById('catEditId').value);
  const selected = Array.from(document.querySelectorAll('.cat-cb:checked')).map(cb=>parseInt(cb.value));
  if (selected.length===0) { alert('请至少选择一个分类'); return; }
  const r = await api('/api/v1/admin/wallpapers/'+id+'/categories', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({category_ids:selected})});
  if (r.ok) { closeCatModal(); load(); } else { alert('保存失败'); }
}
loadCategories(); load();
"""


# ─── Wallpapers Management (壁纸管理) ─────────────────────────────────────────

WALLPAPERS_CONTENT = """<div class="content">
  <div class="top">
    <input type="text" id="searchInput" placeholder="搜索标题..."/>
    <select id="statusSelect">
      <option value="">全部状态</option>
      <option value="approved">已上架</option>
      <option value="pending">待审核</option>
      <option value="rejected">已拒绝</option>
      <option value="unlisted">已下架</option>
    </select>
    <select id="deviceSelect">
      <option value="">全部设备</option>
      <option value="portrait">竖屏</option>
      <option value="landscape">横屏</option>
      <option value="fold2">两折叠</option>
      <option value="fold3">三折叠</option>
    </select>
    <button onclick="doSearch()">搜索</button>
  </div>
  <div class="batch-bar" id="batchBar" style="display:none">
    <span id="batchCount">已选0项</span>
    <select id="batchCategory"><option value="">不改分类</option></select>
    <span style="color:#888;font-size:12px">设备:</span>
    <label style="font-size:12px;color:#ccc"><input type="checkbox" class="batchDev" value="portrait">竖屏</label>
    <label style="font-size:12px;color:#ccc"><input type="checkbox" class="batchDev" value="landscape">横屏</label>
    <label style="font-size:12px;color:#ccc"><input type="checkbox" class="batchDev" value="fold2">两折叠</label>
    <label style="font-size:12px;color:#ccc"><input type="checkbox" class="batchDev" value="fold3">三折叠</label>
    <input type="text" id="batchTitle" placeholder="批量修改标题(支持替换)" style="width:140px"/>
    <button onclick="batchApply()" style="background:#ff6b6b;color:#fff">批量应用</button>
    <button onclick="selectAll()">全选</button>
    <button onclick="clearSel()">取消</button>
  </div>
  <div class="list" id="list"><div class="empty">加载中...</div></div>
  <div class="pager">
    <button id="prevBtn" onclick="changePage(-1)">上一页</button>
    <span id="pagerInfo"></span>
    <button id="nextBtn" onclick="changePage(1)">下一页</button>
  </div>
</div>
<div id="editModal" class="modal" style="display:none"><div class="modal-box"><h3>编辑壁纸</h3>
  <input type="hidden" id="editId"/>
  <label>标题<input id="editTitle" style="width:100%"/></label>
  <label>描述<textarea id="editDesc" style="width:100%;height:60px"></textarea></label>
  <label>分类<div id="editCategory" style="display:flex;flex-wrap:wrap;gap:10px;margin:6px 0"></div></label>
  <label>设备类型<div style="display:flex;gap:12px;margin:4px 0">
    <label style="font-size:13px;color:#ccc"><input type="checkbox" class="editDev" value="portrait">竖屏</label>
    <label style="font-size:13px;color:#ccc"><input type="checkbox" class="editDev" value="landscape">横屏</label>
    <label style="font-size:13px;color:#ccc"><input type="checkbox" class="editDev" value="fold2">两折叠</label>
    <label style="font-size:13px;color:#ccc"><input type="checkbox" class="editDev" value="fold3">三折叠</label>
  </div></label>
  <label>标签<input id="editTags" placeholder="逗号分隔" style="width:100%"/></label>
  <div class="modal-actions"><button onclick="saveEdit()" style="background:#ff6b6b;color:#fff">保存</button><button onclick="closeEdit()">取消</button></div>
</div></div>"""

WALLPAPERS_SCRIPTS = """
let page=1,selectedIds=new Set(),allItems=[],categories=[];
async function loadCategories() {
  try { const d = await (await api('/api/v1/admin/categories')).json(); categories = d.items||[]; } catch(e) {}
}
function catNames(ids) {
  if (!ids||ids.length===0) return '-';
  return ids.map(id=>(categories.find(c=>c.id===id)||{}).name||id).join(', ');
}
async function load() {
  const search = document.getElementById('searchInput').value;
  const status = document.getElementById('statusSelect').value;
  const device = document.getElementById('deviceSelect').value;
  let path = '/api/v1/admin/wallpapers?page='+page+'&size=12';
  if (search) path += '&search='+encodeURIComponent(search);
  if (status) path += '&status='+status;
  if (device) path += '&device_type='+device;
  const d = await (await api(path)).json();
  allItems = d.items||[];
  const list = document.getElementById('list');
  if (!d.items||d.items.length===0) { list.innerHTML='<div class="empty">暂无壁纸</div>'; document.getElementById('batchBar').style.display='none'; return; }
  list.innerHTML = allItems.map(wp => `
    <div class="item">
      <input type="checkbox" class="wp-cb" value="${wp.id}" onchange="toggleSel(${wp.id},this.checked)" ${selectedIds.has(wp.id)?'checked':''}/>
      <img src="${imgUrl(wp)}" onerror="this.style.display='none'" style="width:60px;height:60px;object-fit:cover;border-radius:6px"/>
      <div class="info">
        <div class="title">${esc(wp.title)} <span class="tag tag-${wp.status}">${fmtStatus(wp.status)}</span></div>
        <div class="meta">${(wp.device_types||[]).join(' · ')} · ${wp.width}x${wp.height} · 分类: ${catNames(wp.category_ids)} · 下载${wp.downloads} · ♥${wp.likes} · ${new Date(wp.created_at).toLocaleDateString()}` + ` · 上传者: ${wp.author_name || (wp.author_id ? 'UID:'+wp.author_id : '—')}` + `</div>
      </div>
      <div class="actions">
        <button class="btn" onclick="openEdit(${wp.id})" style="font-size:11px;padding:4px 8px">编辑</button>
        ${wp.status==='approved'?`<button class="btn btn-warn" onclick="changeStatus(${wp.id},'unlisted')">下架</button>`:''}
        ${wp.status==='unlisted'?`<button class="btn btn-ok" onclick="changeStatus(${wp.id},'approved')">上架</button>`:''}
        <button class="btn btn-del" onclick="delWp(${wp.id})">删除</button>
      </div>
    </div>`).join('');
  document.getElementById('pagerInfo').textContent='第'+page+'页 / 共'+(d.pages||1)+'页 · '+(d.total||0)+'条';
  document.getElementById('prevBtn').disabled = page<=1;
  document.getElementById('nextBtn').disabled = page>=(d.pages||1);
  document.getElementById('batchBar').style.display='flex';
  updateBatchCount();
}
function doSearch() { page=1; selectedIds.clear(); load(); }
function changePage(dir) { page+=dir; load(); }
function toggleSel(id,checked) { if(checked)selectedIds.add(id); else selectedIds.delete(id); updateBatchCount(); }
function selectAll() { allItems.forEach(w=>selectedIds.add(w.id)); load(); }
function clearSel() { selectedIds.clear(); load(); }
function updateBatchCount() { document.getElementById('batchCount').textContent='已选'+selectedIds.size+'项'; }

async function changeStatus(id,status) {
  const conf = {unlisted:'确定下架该壁纸？',approved:'确定重新上架？'};
  if (!confirm(conf[status]||'确定？')) return;
  await api('/api/v1/admin/wallpapers/'+id+'/status', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});
  load();
}
async function delWp(id) {
  if (!confirm('确定永久删除此壁纸？')) return;
  const r = await api('/api/v1/wallpapers/'+id, {method:'DELETE'});
  if (r.ok) { load(); } else { alert('删除失败'); }
}
async function batchApply() {
  if (selectedIds.size===0) { alert('请先选择壁纸'); return; }
  const body = {ids:Array.from(selectedIds)};
  const cat = document.getElementById('batchCategory').value;
  const devs = Array.from(document.querySelectorAll('.batchDev:checked')).map(cb=>cb.value);
  const title = document.getElementById('batchTitle').value.trim();
  if (cat) body.category_id = parseInt(cat);
  if (devs.length>0) body.device_types = devs;
  if (title) body.title = title;
  if (!cat&&devs.length===0&&!title) { alert('请选择要修改的字段'); return; }
  const r = await api('/api/v1/admin/wallpapers/batch', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d = await r.json();
  selectedIds.clear();
  alert('已更新 '+d.updated+'/'+d.requested+' 项');
  load();
}

// Inline edit modal
async function openEdit(id) {
  const wp = allItems.find(w=>w.id===id); if(!wp) return;
  document.getElementById('editId').value=id;
  document.getElementById('editTitle').value=wp.title;
  document.getElementById('editDesc').value=wp.description||'';
  document.getElementById('editTags').value=(wp.tags||[]).join(',');
  // Check device type checkboxes
  const devs = wp.device_types||[];
  document.querySelectorAll('.editDev').forEach(cb=>{cb.checked=devs.includes(cb.value)});
  // Load categories as checkboxes
  try {
    const cats = await (await api('/api/v1/admin/categories')).json();
    const box = document.getElementById('editCategory');
    const selected = wp.category_ids||[];
    box.innerHTML = (cats.items||[]).map(c=>`
      <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:#ccc;cursor:pointer">
        <input type="checkbox" class="editCat" value="${c.id}" ${selected.includes(c.id)?'checked':''}/> ${esc(c.name)}
      </label>`).join('');
  } catch(e) {}
  document.getElementById('editModal').style.display='flex';
}
function closeEdit() { document.getElementById('editModal').style.display='none'; }
async function saveEdit() {
  const id = parseInt(document.getElementById('editId').value);
  const devs = Array.from(document.querySelectorAll('.editDev:checked')).map(cb=>cb.value);
  const cats = Array.from(document.querySelectorAll('.editCat:checked')).map(cb=>parseInt(cb.value));
  if (cats.length===0) { alert('请至少选择一个分类'); return; }
  const body = {
    title: document.getElementById('editTitle').value.trim(),
    description: document.getElementById('editDesc').value.trim(),
    category_ids: cats,
    device_types: devs,
    tags: document.getElementById('editTags').value.split(',').map(s=>s.trim()).filter(s=>s),
  };
  const r = await api('/api/v1/admin/wallpapers/'+id, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if (r.ok) { closeEdit(); load(); } else { alert('保存失败'); }
}

document.getElementById('searchInput').addEventListener('keydown', e => { if(e.key==='Enter') doSearch(); });
// Load categories for batch dropdown and names on init
(async()=>{ await loadCategories(); document.getElementById('batchCategory').innerHTML='<option value="">不改分类</option>'+(categories||[]).map(c=>`<option value="${c.id}">${c.name}</option>`).join(''); })();
load();
"""


# ─── Categories Management (分类管理) ─────────────────────────────────────────

CATEGORIES_CONTENT = """<div class="content">
  <div class="top">
    <input type="text" id="catName" placeholder="分类名称" style="flex:0.5"/>
    <input type="text" id="catSlug" placeholder="slug (如 fengjing)" style="flex:0.5"/>
    <input type="text" id="catIcon" placeholder="图标emoji" style="flex:0.2"/>
    <input type="number" id="catSort" placeholder="排序" value="0" style="flex:0.15"/>
    <button onclick="createCategory()">添加分类</button>
  </div>
  <div class="list" id="catList"><div class="empty">加载中...</div></div>
</div>"""

CATEGORIES_SCRIPTS = """
let categories = [];
async function loadCategories() {
  try {
    const d = await (await api('/api/v1/admin/categories')).json();
    categories = d.items||[];
    const list = document.getElementById('catList');
    if (categories.length===0) { list.innerHTML='<div class="empty">暂无分类</div>'; return; }
    list.innerHTML = categories.map(c => `
      <div class="item" style="border-left:4px solid #ff6b6b">
        <div class="info">
          <div class="title">${c.icon||''} ${esc(c.name)} (${esc(c.slug)})</div>
          <div class="meta">排序: ${c.sort} · ID: ${c.id} · 壁纸数量: ?</div>
        </div>
        <div class="actions">
          <button class="btn btn-warn" onclick="editCategory(${c.id})">编辑</button>
          <button class="btn btn-del" onclick="delCategory(${c.id})">删除</button>
        </div>
      </div>`).join('');
  } catch(e) { document.getElementById('catList').innerHTML='<div class="empty">加载失败</div>'; }
}
async function createCategory() {
  const name = document.getElementById('catName').value.trim();
  const slug = document.getElementById('catSlug').value.trim();
  const icon = document.getElementById('catIcon').value.trim();
  const sort = parseInt(document.getElementById('catSort').value)||0;
  if (!name || !slug) { alert('名称和slug不能为空'); return; }
  const r = await api('/api/v1/admin/categories', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,slug,icon,sort})});
  const d = await r.json();
  if (r.ok) {
    document.getElementById('catName').value=''; document.getElementById('catSlug').value='';
    document.getElementById('catIcon').value=''; document.getElementById('catSort').value='0';
    loadCategories();
  } else { alert(d.detail||'创建失败'); }
}
async function editCategory(id) {
  const c = categories.find(x=>x.id===id);
  if (!c) return;
  const name = prompt('分类名称：', c.name);
  if (!name) return;
  const slug = prompt('slug：', c.slug);
  if (!slug) return;
  const icon = prompt('图标emoji：', c.icon||'');
  const sort = parseInt(prompt('排序：', c.sort))||0;
  const r = await api('/api/v1/admin/categories/'+id, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,slug,icon,sort})});
  const d = await r.json();
  if (r.ok) loadCategories(); else alert(d.detail||'更新失败');
}
async function delCategory(id) {
  if (!confirm('确定删除此分类？如果分类下有壁纸将无法删除。')) return;
  const r = await api('/api/v1/admin/categories/'+id, {method:'DELETE'});
  if (r.ok) loadCategories(); else { const d=await r.json(); alert(d.detail||'删除失败'); }
}
loadCategories();
"""


# ─── Upload ───────────────────────────────────────────────────────────────────

ADMIN_UPLOAD_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>上传壁纸 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
label{display:block;font-size:13px;color:#888;margin:16px 0 6px}
input,select,textarea{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none}
textarea{height:auto;padding:10px 14px;min-height:80px}
input:focus,select:focus,textarea:focus{border-color:#ff6b6b}
input[type=file]{padding:10px 0;border:none;background:transparent}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.btn:hover{opacity:0.9}
.msg{margin-top:12px;font-size:13px;min-height:18px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>上传壁纸（管理员直发）</h2>
    <label>标题</label>
    <input type="text" id="title" placeholder="输入壁纸标题"/>
    <label>设备形态</label>
    <select id="device_type">
      <option value="portrait">竖屏</option>
      <option value="landscape">横屏</option>
      <option value="fold2">两折叠</option>
      <option value="fold3">三折叠</option>
    </select>
    <label>分类</label>
    <select id="category_id"></select>
    <label>标签（逗号分隔）</label>
    <input type="text" id="tags" placeholder="风景, 夜景"/>
    <label>说明</label>
    <textarea id="description" placeholder="可选说明"></textarea>
    <label>壁纸文件</label>
    <input type="file" id="file" accept="image/*"/>
    <button class="btn" onclick="doUpload()">上传并上架</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
async function loadCategories() {
  try {
    const d = await (await api('/api/v1/admin/categories')).json();
    const sel = document.getElementById('category_id');
    sel.innerHTML = (d.items||[]).map(c=>'<option value="'+c.id+'">'+(c.icon||'')+' '+esc(c.name)+'</option>').join('');
  } catch(e) { document.getElementById('msg').textContent='分类加载失败'; }
}
async function doUpload() {
  const title = document.getElementById('title').value;
  const device_type = document.getElementById('device_type').value;
  const category_id = document.getElementById('category_id').value;
  const tags = document.getElementById('tags').value;
  const description = document.getElementById('description').value;
  const fileInput = document.getElementById('file');
  const file = fileInput.files && fileInput.files[0];
  if (!title || !file) { document.getElementById('msg').textContent='请填写标题并选择文件'; return; }
  if (!category_id) { document.getElementById('msg').textContent='请选择分类'; return; }
  const fd = new FormData();
  fd.append('title', title); fd.append('device_type', device_type);
  fd.append('category_id', category_id); fd.append('tags', tags);
  fd.append('description', description); fd.append('file', file);
  try {
    const r = await api('/api/v1/admin/wallpapers', {method:'POST', body:fd});
    const text = await r.text();
    let d;
    try { d = JSON.parse(text); } catch { d = {detail: text || ('HTTP ' + r.status)}; }
    if (r.ok) {
      document.getElementById('msg').textContent='上传成功，ID: '+d.id;
      document.getElementById('title').value=''; document.getElementById('tags').value='';
      document.getElementById('description').value=''; fileInput.value='';
    } else {
      const msg = Array.isArray(d.detail) ? d.detail.map(x => x.msg || JSON.stringify(x)).join('; ') : (d.detail || '上传失败');
      document.getElementById('msg').textContent = msg;
    }
  } catch(e) { document.getElementById('msg').textContent = '上传请求失败: ' + e.message; }
}
function esc(s) { if(!s)return''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
loadCategories();
</script>
</div>
</body>
</html>"""


# ─── Users ────────────────────────────────────────────────────────────────────

ADMIN_USERS_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>用户管理 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:12px;text-align:left;border-bottom:1px solid #2a2a3e}
th{color:#888;font-weight:normal}
.tag-admin{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;background:#1a3a2a;color:#2ecc71}
.tag-user{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;background:#2a2a3e;color:#aaa}
.btn-toggle{background:#2a2a3e;color:#fff;padding:4px 10px;border-radius:12px;font-size:12px;border:none;cursor:pointer;margin-right:4px}
.btn-reset{background:#1a3a2a;color:#2ecc71;padding:4px 10px;border-radius:12px;font-size:12px;border:none;cursor:pointer;margin-right:4px}
.btn-del{background:#3a1a1a;color:#e74c3c;padding:4px 10px;border-radius:12px;font-size:12px;border:none;cursor:pointer}
.container{padding:24px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.7);display:none;align-items:center;justify-content:center;z-index:100}
.modal.active{display:flex}
.modal-box{background:#16162a;border-radius:12px;padding:24px;width:320px}
.modal-box input{width:100%;height:40px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;padding:0 12px;margin:10px 0}
.modal-box button{width:100%;height:40px;background:#ff6b6b;color:#fff;border:none;border-radius:20px;cursor:pointer;margin-top:10px}
.modal-box .cancel{margin-top:8px;background:#2a2a3e}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="table-wrap">
  <table>
    <thead><tr><th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th><th>注册时间</th><th>操作</th></tr></thead>
    <tbody id="userList"><tr><td colspan="6" class="empty">加载中...</td></tr></tbody>
  </table>
  </div>
</div>
<div class="modal" id="resetModal">
  <div class="modal-box">
    <h3>重置密码</h3>
    <input type="password" id="newPwd" placeholder="输入新密码（至少6位）"/>
    <button onclick="confirmReset()">确认重置</button>
    <button class="cancel" onclick="closeModal()">取消</button>
  </div>
</div>
<script>
const token = localStorage.getItem('admin_token');
if (!token) { window.location.href='/admin/login'; throw 'no token'; }
async function api(path, opts={}) {
  const r = await fetch(path, {method:opts.method||'GET', headers:{'Authorization':'Bearer '+token, ...(opts.headers||{})}, body:opts.body});
  if (r.status===401||r.status===403) { localStorage.removeItem('admin_token'); window.location.href='/admin/login'; }
  return r;
}
function esc(s) { if(!s)return''; var d={'&':'amp','<':'lt','>':'gt'}; return String(s).replace(/[&<>]/g,function(c){return'&'+d[c]+';';}); }
function formatTime(s) { try{return new Date(s).toLocaleString('zh-CN')}catch(e){return s||''} }
let users=[], resetId=null;

async function loadUsers() {
  try {
    const d = await (await api('/api/v1/admin/users')).json();
    users = Array.isArray(d)?d:(d.items||[]);
    const tbody = document.getElementById('userList');
    if (users.length===0) { tbody.innerHTML='<tr><td colspan="6" class="empty">暂无用户</td></tr>'; return; }
    tbody.innerHTML = users.map(function(u) {
      return '<tr><td>'+u.id+'</td><td>'+esc(u.username)+'</td><td>'+(u.email||'-')+'</td>'+
      '<td>'+(u.is_admin?'<span class="tag-admin">管理员</span>':'<span class="tag-user">普通用户</span>')+'</td>'+
      '<td>'+formatTime(u.created_at)+'</td>'+
      '<td><button class="btn-toggle" onclick="toggleAdmin('+u.id+','+(!u.is_admin)+')">'+(u.is_admin?'取消管理员':'设为管理员')+'</button>'+
      '<button class="btn-reset" onclick="openReset('+u.id+')">重置</button>'+
      '<button class="btn-del" onclick="delUser('+u.id+')">删除</button>'+
      '<a href="/admin/users/'+u.id+'/wallpapers" class="btn-toggle" style="display:inline-block;text-decoration:none;background:#1a2a3e;color:#5dade2">壁纸</a></td></tr>';
    }).join('');
  } catch(e) { document.getElementById('userList').innerHTML='<tr><td colspan="6" class="empty">加载失败</td></tr>'; }
}
async function toggleAdmin(id, val) {
  const r = await api('/api/v1/admin/users/'+id, {method:'PUT', body:JSON.stringify({is_admin:val}), headers:{'Content-Type':'application/json'}});
  if (r.ok) loadUsers(); else alert('操作失败');
}
function openReset(id) { resetId=id; document.getElementById('resetModal').classList.add('active'); }
function closeModal() { resetId=null; document.getElementById('resetModal').classList.remove('active'); }
async function confirmReset() {
  const pwd = document.getElementById('newPwd').value;
  if (!pwd || pwd.length<6) { alert('密码至少6位'); return; }
  const r = await api('/api/v1/admin/users/'+resetId+'/reset-password', {method:'POST', body:JSON.stringify({new_password:pwd}), headers:{'Content-Type':'application/json'}});
  if (r.ok) { alert('密码已重置'); closeModal(); } else alert('重置失败');
}
async function delUser(id) {
  if (!confirm('确定删除该用户？')) return;
  const r = await api('/api/v1/admin/users/'+id, {method:'DELETE'});
  if (r.ok) { loadUsers(); return; }
  const d = await r.json();
  if (d.detail && d.detail.indexOf('张') > -1) {
    if (confirm(d.detail + ' 是否强制删除（含壁纸）？')) {
      const r2 = await api('/api/v1/admin/users/'+id+'?force=true', {method:'DELETE'});
      if (r2.ok) loadUsers(); else alert('删除失败');
    }
  } else { alert('删除失败: ' + (d.detail || '')); }
}
loadUsers();
</script>
</div>
</body>
</html>"""


# ─── Config ───────────────────────────────────────────────────────────────────

ADMIN_CONFIG_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>通知配置 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
label{display:block;font-size:13px;color:#888;margin:16px 0 6px}
input{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none}
input:focus{border-color:#ff6b6b}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.btn:hover{opacity:0.9}
.btn-secondary{width:100%;height:46px;background:transparent;border:1px solid #ff6b6b;color:#ff6b6b;border-radius:23px;font-size:15px;cursor:pointer;margin-top:12px}
.msg{margin-top:12px;font-size:13px;min-height:18px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>Webhook 通知配置</h2>
    <label>Webhook URL</label>
    <input type="text" id="url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."/>
    <button class="btn" onclick="saveConfig()">保存配置</button>
    <button class="btn-secondary" onclick="testWebhook()">发送测试通知</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
async function loadConfig() {
  try {
    const d = await (await api('/api/v1/admin/config/webhook')).json();
    document.getElementById('url').value = d.url || '';
  } catch(e) { document.getElementById('msg').textContent='加载失败'; }
}
async function saveConfig() {
  const url = document.getElementById('url').value.trim();
  if (!url) { document.getElementById('msg').textContent='URL 不能为空'; return; }
  const r = await api('/api/v1/admin/config/webhook', {method:'PUT', body:JSON.stringify({url}), headers:{'Content-Type':'application/json'}});
  const d = await r.json();
  document.getElementById('msg').textContent = r.ok ? '保存成功' : (d.detail || '保存失败');
}
async function testWebhook() {
  const r = await api('/api/v1/admin/webhook-test', {method:'POST'});
  const d = await r.json();
  document.getElementById('msg').textContent = d.ok ? '测试通知已发送' : ('发送失败: '+(d.message||d.detail||''));
}
loadConfig();
</script>
</div>
</body>
</html>"""


# ─── Site Config ──────────────────────────────────────────────────────────────

ADMIN_SITE_CONFIG_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>站点设置 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
label{display:block;font-size:13px;color:#888;margin:16px 0 6px}
input,select{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none}
input:focus,select:focus{border-color:#ff6b6b}
.switch{display:flex;align-items:center;justify-content:space-between;margin:16px 0;padding:12px;background:#1a1a2e;border-radius:8px}
.switch span{font-size:14px;color:#fff}
.switch input{height:auto;width:auto;transform:scale(1.4);cursor:pointer}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.btn:hover{opacity:0.9}
.msg{margin-top:12px;font-size:13px;min-height:18px}
.hint{font-size:12px;color:#666;margin-top:4px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>站点设置</h2>
    <div class="switch">
      <span>允许用户上传壁纸</span>
      <input type="checkbox" id="upload_enabled"/>
    </div>
    <div class="hint">关闭后，普通用户将无法上传新壁纸；未上传过壁纸的用户也看不到“我的壁纸”入口。管理员仍可在后台上传。</div>
    <button class="btn" onclick="saveConfig()">保存配置</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
async function loadConfig() {
  try {
    const d = await (await api('/api/v1/admin/config/site')).json();
    document.getElementById('upload_enabled').checked = !!d.upload_enabled;
  } catch(e) { document.getElementById('msg').textContent='加载失败'; }
}
async function saveConfig() {
  const upload_enabled = document.getElementById('upload_enabled').checked;
  const r = await api('/api/v1/admin/config/site', {method:'PUT', body:JSON.stringify({upload_enabled}), headers:{'Content-Type':'application/json'}});
  const d = await r.json();
  document.getElementById('msg').textContent = r.ok ? '保存成功' : (d.detail || '保存失败');
}
loadConfig();
</script>
</div>
</body>
</html>"""


# ─── Auth Config ──────────────────────────────────────────────────────────────

ADMIN_AUTH_CONFIG_HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>认证配置 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
label{display:block;font-size:13px;color:#888;margin:16px 0 6px}
input,select{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none}
input:focus,select:focus{border-color:#ff6b6b}
.switch{display:flex;align-items:center;justify-content:space-between;margin:16px 0;padding:12px;background:#1a1a2e;border-radius:8px}
.switch span{font-size:14px;color:#fff}
.switch input{height:auto;width:auto;transform:scale(1.4);cursor:pointer}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.btn:hover{opacity:0.9}
.msg{margin-top:12px;font-size:13px;min-height:18px}
.hint{font-size:12px;color:#666;margin-top:4px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>注册与登录认证配置</h2>
    <div class="switch">
      <span>注册时邮箱必填</span>
      <input type="checkbox" id="require_email"/>
    </div>
    <div class="hint">关闭后用户注册可不填邮箱，但找回密码功能将不可用。</div>
    <div class="switch">
      <span>注册时启用邮箱验证码验证</span>
      <input type="checkbox" id="enable_email_verify"/>
    </div>
    <div class="hint">开启前请确保下方“邮箱 SMTP 配置”正确。</div>
    <div class="switch">
      <span>注册时启用短信验证码验证</span>
      <input type="checkbox" id="enable_sms_verify"/>
    </div>
    <div class="hint">开启前请确保下方“短信平台配置”正确。</div>
    <div class="switch">
      <span>启用华为账号登录</span>
      <input type="checkbox" id="enable_huawei_login"/>
    </div>
    <div class="hint">开启后需要在环境变量中配置 HUAWEI_CLIENT_ID / HUAWEI_CLIENT_SECRET。</div>
    <label>短信服务商</label>
    <select id="sms_provider">
      <option value="aliyun">阿里云短信</option>
      <option value="yunpian">云片</option>
    </select>
    <label>邮箱服务商</label>
    <select id="email_provider">
      <option value="smtp">SMTP</option>
    </select>
    <button class="btn" onclick="saveConfig()">保存配置</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
async function loadConfig() {
  try {
    const d = await (await api('/api/v1/admin/config/auth')).json();
    document.getElementById('require_email').checked = !!d.require_email;
    document.getElementById('enable_email_verify').checked = !!d.enable_email_verify;
    document.getElementById('enable_sms_verify').checked = !!d.enable_sms_verify;
    document.getElementById('enable_huawei_login').checked = !!d.enable_huawei_login;
    document.getElementById('sms_provider').value = d.sms_provider || 'aliyun';
    document.getElementById('email_provider').value = d.email_provider || 'smtp';
  } catch(e) { document.getElementById('msg').textContent='加载失败'; }
}
async function saveConfig() {
  const body = {
    require_email: document.getElementById('require_email').checked,
    enable_email_verify: document.getElementById('enable_email_verify').checked,
    enable_sms_verify: document.getElementById('enable_sms_verify').checked,
    enable_huawei_login: document.getElementById('enable_huawei_login').checked,
    sms_provider: document.getElementById('sms_provider').value,
    email_provider: document.getElementById('email_provider').value,
  };
  const r = await api('/api/v1/admin/config/auth', {method:'PUT', body:JSON.stringify(body), headers:{'Content-Type':'application/json'}});
  const d = await r.json();
  document.getElementById('msg').textContent = r.ok ? '保存成功' : (d.detail || '保存失败');
}
loadConfig();
</script>
</div>
</body>
</html>"""


# ─── Storage Config ───────────────────────────────────────────────────────────

ADMIN_STORAGE_CONFIG_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>存储配置 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
label{display:block;font-size:13px;color:#888;margin:16px 0 6px}
input,select{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none}
input:focus,select:focus{border-color:#ff6b6b}
.switch{display:flex;align-items:center;justify-content:space-between;margin:16px 0;padding:12px;background:#1a1a2e;border-radius:8px}
.switch span{font-size:14px;color:#fff}
.switch input{height:auto;width:auto;transform:scale(1.4);cursor:pointer}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.msg{margin-top:12px;font-size:13px;min-height:18px}
.hint{font-size:12px;color:#666;margin-top:4px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>壁纸存储配置</h2>
    <div class="switch">
      <span>启用对象存储（阿里云 OSS）</span>
      <input type="checkbox" id="enabled"/>
    </div>
    <div class="hint">关闭时使用服务器本地存储（/static）。开启后新上传的壁纸将存入 OSS，存量壁纸需运行迁移脚本。</div>
    <label>Bucket</label>
    <input type="text" id="bucket" placeholder="your-bucket-name"/>
    <label>Endpoint</label>
    <input type="text" id="endpoint" placeholder="https://oss-cn-hangzhou.aliyuncs.com"/>
    <label>AccessKey ID</label>
    <input type="text" id="access_key" placeholder="LTAI..."/>
    <label>AccessKey Secret</label>
    <input type="password" id="secret_key" placeholder="********"/>
    <label>CDN 域名（可选）</label>
    <input type="text" id="cdn_domain" placeholder="cdn.example.com（不含 https://）"/>
    <label>路径前缀</label>
    <input type="text" id="path_prefix" placeholder="wallpapers/"/>
    <div class="switch">
      <span>使用私有签名 URL（Bucket 不开公共读时启用）</span>
      <input type="checkbox" id="signed_url"/>
    </div>
    <div class="hint">开启后，返回给客户端的图片 URL 会带临时签名（7 天有效），无需设置 Bucket 公共读。</div>
    <button class="btn" onclick="saveConfig()">保存配置</button>
    <button class="btn-test" onclick="testOss()" style="margin-top:8px">🧪 测试 OSS 连接</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
async function loadConfig() {
  try {
    const d = await (await api('/api/v1/admin/config/storage')).json();
    document.getElementById('enabled').checked = !!d.enabled;
    document.getElementById('bucket').value = d.bucket || '';
    document.getElementById('endpoint').value = d.endpoint || '';
    document.getElementById('access_key').value = d.access_key || '';
    document.getElementById('secret_key').value = d.secret_key || '';
    document.getElementById('cdn_domain').value = d.cdn_domain || '';
    document.getElementById('path_prefix').value = d.path_prefix || 'wallpapers/';
    document.getElementById('signed_url').checked = !!d.signed_url;
  } catch(e) { document.getElementById('msg').textContent='加载失败'; }
}
async function saveConfig() {
  const body = {
    provider: 'aliyun_oss',
    enabled: document.getElementById('enabled').checked,
    bucket: document.getElementById('bucket').value.trim(),
    endpoint: document.getElementById('endpoint').value.trim(),
    access_key: document.getElementById('access_key').value.trim(),
    secret_key: document.getElementById('secret_key').value.trim(),
    cdn_domain: document.getElementById('cdn_domain').value.trim(),
    path_prefix: document.getElementById('path_prefix').value.trim() || 'wallpapers/',
    signed_url: document.getElementById('signed_url').checked,
  };
  const r = await api('/api/v1/admin/config/storage', {method:'PUT', body:JSON.stringify(body), headers:{'Content-Type':'application/json'}});
  const d = await r.json();
  document.getElementById('msg').textContent = r.ok ? '保存成功（新上传壁纸生效）' : (d.detail || '保存失败');
}
async function testOss() {
  document.getElementById('msg').textContent = '正在测试 OSS 连接...';
  try {
    const r = await api('/api/v1/admin/test-storage', {method:'POST'});
    const d = await r.json();
    document.getElementById('msg').innerHTML = (d.ok ? '<span style="color:#2ecc71">' : '<span style="color:#e74c3c">') + esc(d.message || d.detail || '') + '</span>';
  } catch(e) { document.getElementById('msg').textContent = '测试请求失败: ' + e.message; }
}
loadConfig();
</script>
</div>
</body>
</html>"""


# ─── SMTP Config ──────────────────────────────────────────────────────────────

ADMIN_SMTP_CONFIG_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>邮箱配置 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
label{display:block;font-size:13px;color:#888;margin:16px 0 6px}
input{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none}
input:focus{border-color:#ff6b6b}
.switch{display:flex;align-items:center;justify-content:space-between;margin:16px 0;padding:12px;background:#1a1a2e;border-radius:8px}
.switch span{font-size:14px;color:#fff}
.switch input{height:auto;width:auto;transform:scale(1.4);cursor:pointer}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.btn-secondary{width:100%;height:46px;background:transparent;border:1px solid #ff6b6b;color:#ff6b6b;border-radius:23px;font-size:15px;cursor:pointer;margin-top:12px}
.msg{margin-top:12px;font-size:13px;min-height:18px}
.hint{font-size:12px;color:#666;margin-top:4px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>邮箱 SMTP 配置</h2>
    <div class="switch">
      <span>启用该 SMTP 配置发送验证码</span>
      <input type="checkbox" id="enabled"/>
    </div>
    <div class="hint">关闭时回退到环境变量 EMAIL_SMTP_* 配置。</div>
    <label>SMTP 服务器</label>
    <input type="text" id="host" placeholder="smtp.qq.com / smtp.163.com"/>
    <label>端口</label>
    <input type="number" id="port" value="465"/>
    <label>账号</label>
    <input type="text" id="user" placeholder="noreply@example.com"/>
    <label>授权码 / 密码</label>
    <input type="password" id="password" placeholder="********"/>
    <label>发件人地址</label>
    <input type="text" id="from_addr" placeholder="默认使用账号"/>
    <label>发件人名称</label>
    <input type="text" id="from_name" placeholder="多点壁纸"/>
    <button class="btn" onclick="saveConfig()">保存配置</button>
    <div style="border-top:1px solid #2a2a3e;margin-top:16px;padding-top:16px">
      <label>发送测试邮件到</label>
      <div style="display:flex;gap:8px">
        <input type="email" id="testEmail" placeholder="admin@example.com" style="flex:1"/>
        <button class="btn-test" onclick="testSmtp()" style="white-space:nowrap">🧪 发送测试</button>
      </div>
    </div>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
async function loadConfig() {
  try {
    const d = await (await api('/api/v1/admin/config/smtp')).json();
    document.getElementById('enabled').checked = !!d.enabled;
    document.getElementById('host').value = d.host || '';
    document.getElementById('port').value = d.port || 465;
    document.getElementById('user').value = d.user || '';
    document.getElementById('password').value = d.password || '';
    document.getElementById('from_addr').value = d.from_addr || '';
    document.getElementById('from_name').value = d.from_name || '';
  } catch(e) { document.getElementById('msg').textContent='加载失败'; }
}
async function saveConfig() {
  const body = {
    enabled: document.getElementById('enabled').checked,
    host: document.getElementById('host').value.trim(),
    port: parseInt(document.getElementById('port').value)||465,
    user: document.getElementById('user').value.trim(),
    password: document.getElementById('password').value,
    from_addr: document.getElementById('from_addr').value.trim(),
    from_name: document.getElementById('from_name').value.trim(),
  };
  const r = await api('/api/v1/admin/config/smtp', {method:'PUT', body:JSON.stringify(body), headers:{'Content-Type':'application/json'}});
  const d = await r.json();
  document.getElementById('msg').textContent = r.ok ? '保存成功' : (d.detail || '保存失败');
}
async function testSmtp() {
  const email = document.getElementById('testEmail').value.trim();
  if (!email) { document.getElementById('msg').textContent = '请输入测试邮箱'; return; }
  document.getElementById('msg').textContent = '正在发送测试邮件...';
  try {
    const r = await api('/api/v1/admin/test-smtp?to_email=' + encodeURIComponent(email), {method:'POST'});
    const d = await r.json();
    document.getElementById('msg').innerHTML = (d.ok ? '<span style="color:#2ecc71">' : '<span style="color:#e74c3c">') + esc(d.message || d.detail || '') + '</span>';
  } catch(e) { document.getElementById('msg').textContent = '测试请求失败: ' + e.message; }
}
loadConfig();
</script>
</div>
</body>
</html>"""


# ─── SMS Config ───────────────────────────────────────────────────────────────

ADMIN_SMS_CONFIG_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>短信配置 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
label{display:block;font-size:13px;color:#888;margin:16px 0 6px}
input,select{width:100%;height:44px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:14px;padding:0 14px;outline:none}
input:focus,select:focus{border-color:#ff6b6b}
.switch{display:flex;align-items:center;justify-content:space-between;margin:16px 0;padding:12px;background:#1a1a2e;border-radius:8px}
.switch span{font-size:14px;color:#fff}
.switch input{height:auto;width:auto;transform:scale(1.4);cursor:pointer}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.msg{margin-top:12px;font-size:13px;min-height:18px}
.hint{font-size:12px;color:#666;margin-top:4px}
.group{border:1px solid #2a2a3e;border-radius:8px;padding:16px;margin-top:16px}
.group h3{font-size:14px;color:#ff6b6b;margin-bottom:4px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>短信平台配置</h2>
    <div class="switch">
      <span>启用该短信配置发送验证码</span>
      <input type="checkbox" id="enabled"/>
    </div>
    <div class="hint">关闭时回退到环境变量中的短信配置。</div>
    <label>服务商</label>
    <select id="provider" onchange="toggleProvider()">
      <option value="aliyun">阿里云短信</option>
      <option value="yunpian">云片</option>
    </select>
    <div class="group" id="groupAliyun">
      <h3>阿里云短信</h3>
      <label>AccessKey ID</label>
      <input type="text" id="aliyun_access_key_id" placeholder="LTAI..."/>
      <label>AccessKey Secret</label>
      <input type="password" id="aliyun_access_key_secret" placeholder="********"/>
      <label>签名</label>
      <input type="text" id="aliyun_sign_name" placeholder="多点壁纸"/>
      <label>模板 CODE</label>
      <input type="text" id="aliyun_template_code" placeholder="SMS_123456789"/>
    </div>
    <div class="group" id="groupYunpian" style="display:none">
      <h3>云片</h3>
      <label>API KEY</label>
      <input type="password" id="yunpian_api_key" placeholder="********"/>
    </div>
    <button class="btn" onclick="saveConfig()">保存配置</button>
    <div style="border-top:1px solid #2a2a3e;margin-top:16px;padding-top:16px">
      <label>发送测试短信到</label>
      <div style="display:flex;gap:8px">
        <input type="tel" id="testPhone" placeholder="13800138000" style="flex:1"/>
        <button class="btn-test" onclick="testSms()" style="white-space:nowrap">🧪 发送测试</button>
      </div>
    </div>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
function toggleProvider() {
  const p = document.getElementById('provider').value;
  document.getElementById('groupAliyun').style.display = p==='aliyun'?'block':'none';
  document.getElementById('groupYunpian').style.display = p==='yunpian'?'block':'none';
}
async function loadConfig() {
  try {
    const d = await (await api('/api/v1/admin/config/sms')).json();
    document.getElementById('enabled').checked = !!d.enabled;
    document.getElementById('provider').value = d.provider || 'aliyun';
    document.getElementById('aliyun_access_key_id').value = d.aliyun_access_key_id || '';
    document.getElementById('aliyun_access_key_secret').value = d.aliyun_access_key_secret || '';
    document.getElementById('aliyun_sign_name').value = d.aliyun_sign_name || '';
    document.getElementById('aliyun_template_code').value = d.aliyun_template_code || '';
    document.getElementById('yunpian_api_key').value = d.yunpian_api_key || '';
    toggleProvider();
  } catch(e) { document.getElementById('msg').textContent='加载失败'; }
}
async function saveConfig() {
  const body = {
    enabled: document.getElementById('enabled').checked,
    provider: document.getElementById('provider').value,
    aliyun_access_key_id: document.getElementById('aliyun_access_key_id').value.trim(),
    aliyun_access_key_secret: document.getElementById('aliyun_access_key_secret').value.trim(),
    aliyun_sign_name: document.getElementById('aliyun_sign_name').value.trim(),
    aliyun_template_code: document.getElementById('aliyun_template_code').value.trim(),
    yunpian_api_key: document.getElementById('yunpian_api_key').value.trim(),
  };
  const r = await api('/api/v1/admin/config/sms', {method:'PUT', body:JSON.stringify(body), headers:{'Content-Type':'application/json'}});
  const d = await r.json();
  document.getElementById('msg').textContent = r.ok ? '保存成功' : (d.detail || '保存失败');
}
async function testSms() {
  const phone = document.getElementById('testPhone').value.trim();
  if (!phone) { document.getElementById('msg').textContent = '请输入手机号'; return; }
  document.getElementById('msg').textContent = '正在发送测试短信...';
  try {
    const r = await api('/api/v1/admin/test-sms?phone=' + encodeURIComponent(phone), {method:'POST'});
    const d = await r.json();
    document.getElementById('msg').innerHTML = (d.ok ? '<span style="color:#2ecc71">' : '<span style="color:#e74c3c">') + esc(d.message || d.detail || '') + '</span>';
  } catch(e) { document.getElementById('msg').textContent = '测试请求失败: ' + e.message; }
}
loadConfig();
</script>
</div>
</body>
</html>"""


# ─── API Docs ─────────────────────────────────────────────────────────────────

ADMIN_DOCS_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>API 文档 - 多点壁纸管理后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#0f0f23;min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#16162a;border-radius:16px;padding:40px;width:400px;text-align:center}
.box h2{color:#fff;margin-bottom:20px}
.box a{display:block;padding:14px 20px;margin:10px 0;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:10px;color:#fff;text-decoration:none;font-size:15px;transition:.2s}
.box a:hover{background:#ff6b6b;border-color:#ff6b6b}
.loading{color:#666;font-size:13px;margin:20px 0}
</style>
</head>
<body>
<div class="box">
  <h2>📚 API 文档</h2>
  <div class="loading" id="loading">验证登录状态...</div>
  <div id="links" style="display:none">
    <a id="linkSwagger">📖 Swagger API 文档</a>
    <a id="linkRedoc">📄 ReDoc 文档</a>
    <a id="linkHealth">💚 健康检查</a>
    <a id="linkOpenapi">📦 OpenAPI JSON</a>
  </div>
</div>
<script>
(async function() {
  const token = localStorage.getItem('admin_token');
  if (!token) { window.location.href = '/admin/login'; return; }

  // Ensure cookie is set (fixes cookie loss after browser restart)
  document.cookie = 'admin_token=' + token + ';path=/;max-age=86400;SameSite=Lax;Secure';
  
  try {
    const r = await fetch('/api/v1/admin/users?page=1&size=1', {headers:{'Authorization':'Bearer '+token}});
    if (r.status===401||r.status===403) { localStorage.removeItem('admin_token'); window.location.href='/admin/login'; return; }
    if (!r.ok) throw new Error('auth failed');
    
    // Set links with token query param as fallback
    var tp = '?token=' + encodeURIComponent(token);
    document.getElementById('linkSwagger').href = '/docs' + tp;
    document.getElementById('linkSwagger').target = '_blank';
    document.getElementById('linkRedoc').href = '/redoc' + tp;
    document.getElementById('linkRedoc').target = '_blank';
    document.getElementById('linkHealth').href = '/health';
    document.getElementById('linkHealth').target = '_blank';
    document.getElementById('linkOpenapi').href = '/openapi.json' + tp;
    document.getElementById('linkOpenapi').target = '_blank';
    
    document.getElementById('loading').style.display='none';
    document.getElementById('links').style.display='block';
  } catch(e) {
    document.getElementById('loading').textContent='验证失败，请重新登录';
    setTimeout(()=>{ window.location.href='/admin/login'; }, 1500);
  }
})();
</script>
</div>
</body>
</html>"""


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.get("/login", response_class=HTMLResponse)
async def admin_login():
    return HTMLResponse(ADMIN_LOGIN_HTML)


@router.get("/docs", response_class=HTMLResponse)
async def admin_docs():
    return HTMLResponse(ADMIN_DOCS_HTML)


FEEDBACK_CONTENT = """<div class="page-header"><h2>💬 用户反馈</h2></div>
<div class="card">
  <table id="fb-table"><thead><tr><th>ID</th><th>姓名</th><th>邮箱</th><th>内容</th><th>时间</th><th>操作</th></tr></thead><tbody></tbody></table>
  <div id="fb-pagination"></div>
</div>"""

FEEDBACK_SCRIPTS = """
async function loadFeedback(page=1){
  const r=await fetch('/api/v1/admin/feedback?page='+page+'&size=30',{headers:{'Authorization':'Bearer '+localStorage.getItem('admin_token')}});
  const d=await r.json();
  const t=document.getElementById('fb-table').querySelector('tbody');
  t.innerHTML=d.map(f=>`<tr><td>${f.id}</td><td>${f.name}</td><td>${f.email}</td><td style="max-width:300px;word-break:break-all">${f.message}</td><td>${new Date(f.created_at).toLocaleString()}</td><td><button class="btn-sm danger" onclick="delFeedback(${f.id})">删除</button></td></tr>`).join('');
}
async function delFeedback(id){
  if(!confirm('确定删除?'))return;
  await fetch('/api/v1/admin/feedback/'+id,{method:'DELETE',headers:{'Authorization':'Bearer '+localStorage.getItem('admin_token')}});
  loadFeedback();
}
loadFeedback();
"""


@router.get("/feedback", response_class=HTMLResponse)
async def admin_feedback_page():
    return HTMLResponse(_page("用户反馈", FEEDBACK_CONTENT, FEEDBACK_SCRIPTS))


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    return HTMLResponse(_page("数据概览", DASHBOARD_CONTENT, DASHBOARD_SCRIPTS))


@router.get("/submissions", response_class=HTMLResponse)
async def admin_submissions_page():
    return HTMLResponse(_page("审核", SUBMISSIONS_CONTENT, SUBMISSIONS_SCRIPTS))


@router.get("/wallpapers", response_class=HTMLResponse)
async def admin_wallpapers_page():
    return HTMLResponse(_page("壁纸管理", WALLPAPERS_CONTENT, WALLPAPERS_SCRIPTS))


@router.get("/categories", response_class=HTMLResponse)
async def admin_categories_page():
    return HTMLResponse(_page("分类管理", CATEGORIES_CONTENT, CATEGORIES_SCRIPTS))


@router.get("/upload", response_class=HTMLResponse)
async def admin_upload_page():
    return HTMLResponse(ADMIN_UPLOAD_HTML)


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page():
    return HTMLResponse(ADMIN_USERS_HTML)


@router.get("/config", response_class=HTMLResponse)
async def admin_config_page():
    return HTMLResponse(ADMIN_CONFIG_HTML)

@router.get("/config/site", response_class=HTMLResponse)
async def admin_site_config_page():
    return HTMLResponse(ADMIN_SITE_CONFIG_HTML)

@router.get("/config/auth", response_class=HTMLResponse)
async def admin_auth_config_page():
    return HTMLResponse(ADMIN_AUTH_CONFIG_HTML)

@router.get("/config/storage", response_class=HTMLResponse)
async def admin_storage_config_page():
    return HTMLResponse(ADMIN_STORAGE_CONFIG_HTML)


@router.get("/config/smtp", response_class=HTMLResponse)
async def admin_smtp_config_page():
    return HTMLResponse(ADMIN_SMTP_CONFIG_HTML)


@router.get("/config/sms", response_class=HTMLResponse)
async def admin_sms_config_page():
    return HTMLResponse(ADMIN_SMS_CONFIG_HTML)


# ─── Debug Config ──────────────────────────────────────────────────────────────

ADMIN_DEBUG_CONFIG_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>调试配置 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.container{max-width:720px;margin:0 auto;padding:24px}
.card{background:#16162a;border-radius:12px;padding:24px}
h2{font-size:18px;margin-bottom:4px}
.sub{font-size:12px;color:#666;margin-bottom:20px}
.switch{display:flex;align-items:center;justify-content:space-between;margin:16px 0;padding:14px;background:#1a1a2e;border-radius:8px}
.switch span{font-size:14px;color:#fff}
.switch input{height:auto;width:auto;transform:scale(1.4);cursor:pointer}
.row{display:flex;align-items:center;justify-content:space-between;margin:16px 0;padding:14px;background:#1a1a2e;border-radius:8px}
.row label{font-size:14px;color:#fff}
.row input[type=number]{width:80px;height:36px;background:#0f0f23;border:1px solid #2a2a3e;border-radius:6px;color:#fff;text-align:center;font-size:14px}
.btn{width:100%;height:46px;background:#ff6b6b;color:#fff;border:none;border-radius:23px;font-size:15px;cursor:pointer;margin-top:24px}
.btn:hover{opacity:0.9}
.btn-sm{padding:8px 16px;border-radius:6px;font-size:13px;cursor:pointer;border:none}
.btn-danger{background:#ff4757;color:#fff}
.btn-outline{background:transparent;border:1px solid #ff6b6b;color:#ff6b6b}
.msg{margin-top:12px;font-size:13px;min-height:18px}
.hint{font-size:12px;color:#666;margin-top:4px}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div class="container">
  <div class="card">
    <h2>调试日志配置</h2>
    <p class="sub">开启后，App 所有请求将被记录到数据库，可通过调试日志页查看。</p>
    <div class="switch">
      <span>启用调试日志</span>
      <input type="checkbox" id="enabled" onchange="saveSwitch()"/>
    </div>
    <div class="hint">⚠ 频繁请求时会产生大量日志，建议仅在排查问题时开启，排查完毕即关闭。</div>
    <div class="row">
      <label>日志保留天数</label>
      <input type="number" id="retention" min="1" max="90" value="7" onchange="saveRetention()"/>
    </div>
    <div class="hint">超出保留天数的日志将被自动清理。</div>
    <button class="btn" onclick="window.location.href='/admin/debug-logs'">查看调试日志</button>
    <button class="btn-outline btn" style="margin-top:8px" onclick="clearExpired()">清理过期日志</button>
    <div class="msg" id="msg"></div>
  </div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
async function loadConfig() {
  try {
    const d = await (await api('/api/v1/admin/config/debug')).json();
    document.getElementById('enabled').checked = d.enabled;
    document.getElementById('retention').value = d.log_retention_days || 7;
  } catch(e) { document.getElementById('msg').textContent='加载失败'; }
}
async function saveSwitch() {
  const enabled = document.getElementById('enabled').checked;
  document.getElementById('msg').textContent = '保存中...';
  const r = await api('/api/v1/admin/config/debug', {method:'PUT', body:JSON.stringify({enabled}), headers:{'Content-Type':'application/json'}});
  document.getElementById('msg').textContent = r.ok ? (enabled ? '调试日志已开启' : '调试日志已关闭') : '保存失败';
}
async function saveRetention() {
  const days = parseInt(document.getElementById('retention').value) || 7;
  const r = await api('/api/v1/admin/config/debug', {method:'PUT', body:JSON.stringify({log_retention_days:days}), headers:{'Content-Type':'application/json'}});
  document.getElementById('msg').textContent = r.ok ? '已更新' : '保存失败';
}
async function clearExpired() {
  if (!confirm('确认清理超过保留天数的日志？')) return;
  const r = await api('/api/v1/admin/debug-logs/expired', {method:'DELETE'});
  const d = await r.json();
  document.getElementById('msg').textContent = d.ok ? '已清理 ' + d.deleted + ' 条过期日志' : '清理失败';
}
loadConfig();
</script>
</div>
</body>
</html>"""


# ─── Debug Logs ────────────────────────────────────────────────────────────────

ADMIN_DEBUG_LOGS_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>调试日志 - 多点壁纸管理后台</title>
<style>
""" + COMMON_STYLES + """
.top-bar{display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap}
.top-bar input{height:36px;background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;color:#fff;font-size:13px;padding:0 12px;outline:none}
.top-bar input:focus{border-color:#ff6b6b}
.top-bar input[type=text]{flex:1;min-width:200px}
.btn-sm{padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;border:none}
.btn-danger{background:#ff4757;color:#fff}
.btn-outline{background:transparent;border:1px solid #ff6b6b;color:#ff6b6b}
.btn-page{padding:4px 10px;border-radius:4px;font-size:12px;cursor:pointer;border:1px solid #2a2a3e;background:#1a1a2e;color:#aaa;margin:0 2px}
.btn-page.active{background:#ff6b6b;color:#fff;border-color:#ff6b6b}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:10px 8px;color:#888;border-bottom:1px solid #2a2a3e;white-space:nowrap}
td{padding:8px;border-bottom:1px solid #1a1a2e;vertical-align:top}
td.method{font-weight:bold;white-space:nowrap}
td.path{max-width:260px;word-break:break-all}
td.body{max-width:300px;word-break:break-all;color:#888}
td.status.ok{color:#4caf50}td.status.err{color:#ff4757}
td.time{white-space:nowrap;color:#666}
tr:hover{background:#1a1a2e}
.empty{text-align:center;padding:60px;color:#666}
.total{font-size:12px;color:#666;margin-top:8px}
.pages{display:flex;gap:4px;margin-top:12px;flex-wrap:wrap}
</style>
</head>
<body>
""" + _STANDALONE_PRE + """
<div style="padding:20px;max-width:1400px;margin:0 auto">
  <h2 style="margin-bottom:4px;font-size:18px">📋 调试日志</h2>
  <p style="font-size:12px;color:#666;margin-bottom:16px">记录 App 所有 API 请求，用于排查问题。</p>
  <div class="top-bar">
    <input type="text" id="search" placeholder="搜索路径（如 /wallpapers）" onkeydown="if(event.key==='Enter')loadLogs(1)"/>
    <button class="btn-sm btn-outline" onclick="loadLogs(1)">搜索</button>
    <button class="btn-sm btn-danger" onclick="doClear()">清空全部</button>
    <a href="/admin/config/debug" class="btn-sm btn-outline" style="text-decoration:none">⚙ 调试配置</a>
  </div>
  <div id="tableArea"></div>
  <div id="pagesArea"></div>
</div>
<script>
""" + _STANDALONE_JS_TOP + """
let curPage = 1, curSearch = '';

async function loadLogs(page) {
  curPage = page;
  curSearch = document.getElementById('search').value.trim();
  const p = curSearch ? `&search=${encodeURIComponent(curSearch)}` : '';
  const d = await (await api(`/api/v1/admin/debug-logs?page=${page}&size=30`+p)).json();
  render(d);
}

function render(d) {
  if (!d.items || d.items.length === 0) {
    document.getElementById('tableArea').innerHTML = '<div class="empty">暂无日志' + (curSearch ? '（匹配"' + curSearch + '"）' : '') + '</div>';
    document.getElementById('pagesArea').innerHTML = '';
    return;
  }
  let html = `<table><thead><tr><th>时间</th><th>用户</th><th>方法</th><th>路径</th><th>请求体</th><th>状态</th><th>耗时</th><th>IP</th></tr></thead><tbody>`;
  for (const log of d.items) {
    const sc = log.response_status >= 400 ? 'err' : 'ok';
    const methodColor = {'GET':'#4caf50','POST':'#ff9800','PUT':'#2196f3','DELETE':'#ff4757'}[log.method] || '#fff';
    const user = log.username || (log.user_id ? 'UID:'+log.user_id : '匿名');
    html += `<tr>
      <td class="time">${fmt(log.created_at)}</td>
      <td style="white-space:nowrap;max-width:100px;overflow:hidden;text-overflow:ellipsis">${esc(user)}</td>
      <td class="method" style="color:${methodColor}">${log.method}</td>
      <td class="path">${esc(log.path+(log.query_string?'?'+log.query_string:''))}</td>
      <td class="body">${log.request_body ? esc(log.request_body.substring(0,200)) : '-'}</td>
      <td class="status ${sc}">${log.response_status}</td>
      <td>${log.duration_ms}ms</td>
      <td style="white-space:nowrap">${log.ip_address||'-'}</td></tr>`;
  }
  html += '</tbody></table>';
  html += `<div class="total">共 ${d.total} 条 · 第 ${curPage} / ${Math.ceil(d.total/30) || 1} 页</div>`;
  document.getElementById('tableArea').innerHTML = html;

  let pgs = '';
  const tp = Math.ceil(d.total/30) || 1;
  for (let i = 1; i <= Math.min(tp, 20); i++) {
    pgs += `<button class="btn-page${i===curPage?' active':''}" onclick="loadLogs(${i})">${i}</button>`;
  }
  if (tp > 20) pgs += `<span style="color:#666;font-size:12px">...${tp}</span>`;
  document.getElementById('pagesArea').innerHTML = `<div class="pages">${pgs}</div>`;
}

async function doClear() {
  if (!confirm('确认清空所有调试日志？此操作不可恢复。')) return;
  const r = await api('/api/v1/admin/debug-logs', {method:'DELETE'});
  const d = await r.json();
  if (d.ok) { loadLogs(1); }
}

function fmt(s){ if(!s) return ''; const d = new Date(s+'Z'); return d.toLocaleString('zh-CN',{hour12:false}); }
function esc(s){ const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

loadLogs(1);
</script>
</body>
</html>"""


@router.get("/users/{user_id}/wallpapers", response_class=HTMLResponse)
async def admin_user_wp_page(user_id: int):
    """查看单个用户上传的壁纸。"""
    from backend.database import SessionLocal
    from backend.models import User, Wallpaper
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        uname = user.username if user else str(user_id)
        wp_count = db.query(Wallpaper).filter(Wallpaper.author_id == user_id).count()
    finally:
        db.close()

    html = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>$UNAME 的壁纸 - 多点壁纸管理后台</title>
<link rel="icon" href="/favicon_64.png" type="image/png"/>
<style>""" + COMMON_STYLES + """
.container{padding:24px;max-width:1000px;margin:0 auto}
.top-bar{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.top-bar a,.top-bar button{padding:6px 14px;border-radius:6px;font-size:13px;text-decoration:none;cursor:pointer;border:none}
.btn-back{background:#2a2a3e;color:#aaa}
.btn-danger{background:#ff4757;color:#fff}
.btn-transfer{background:#1a3a2a;color:#2ecc71}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px;text-align:left;border-bottom:1px solid #2a2a3e}
th{color:#888;font-weight:normal}
.status-pending{color:#f39c12} .status-approved{color:#2ecc71} .status-rejected{color:#e74c3c} .status-unlisted{color:#aaa}
.empty{text-align:center;padding:60px;color:#666}
</style></head><body>""" + _STANDALONE_PRE + """
<div class="container">
  <div class="top-bar">
    <a href="/admin/users" class="btn-back">&larr; 返回用户列表</a>
    <span style="flex:1;font-size:16px;font-weight:bold;color:#fff">$UNAME 上传的壁纸</span>
    <span style="font-size:12px;color:#888">共 $COUNT 张</span>
    <button class="btn-transfer" onclick="doReassign()">全部转移给管理员</button>
    <button class="btn-danger" onclick="doDeleteUser()">删除此用户</button>
  </div>
  <div id="list"><div class="empty">加载中...</div></div>
</div>
<script>
var token=localStorage.getItem('admin_token');
if(!token){location.href='/admin/login'}
function esc(s){if(!s)return'';var d={'&':'amp','<':'lt','>':'gt'};return String(s).replace(/[&<>]/g,function(c){return'&'+d[c]+';'})}
function formatTime(s){try{return new Date(s).toLocaleString('zh-CN')}catch(e){return s||''}}
async function api(path,opts){
  opts=opts||{};
  var r=await fetch(path,{method:opts.method||'GET',headers:Object.assign({'Authorization':'Bearer '+token},opts.headers||{}),body:opts.body});
  if(r.status===401||r.status===403){localStorage.removeItem('admin_token');location.href='/admin/login'}
  return r
}
var WUID=$UID,WUNAME='$UNAME';
async function load(){
  try{
    var d=await(await api('/api/v1/admin/users/'+WUID+'/wallpapers?size=100')).json();
    var items=d.items||[];
    if(!items.length){document.getElementById('list').innerHTML='<div class="empty">暂无壁纸</div>';return}
    document.getElementById('list').innerHTML='<table><thead><tr><th>ID</th><th>标题</th><th>状态</th><th>设备</th><th>大小</th><th>日期</th></tr></thead><tbody>'+items.map(function(w){
      return'<tr><td>'+w.id+'</td><td>'+esc(w.title)+'</td><td class=status-'+w.status+'>'+w.status+'</td><td>'+(w.device_types||[]).join(' &middot; ')+'</td><td>'+Math.round((w.file_size||0)/1024)+'KB</td><td>'+formatTime(w.created_at)+'</td></tr>';
    }).join('')+'</tbody></table>';
  }catch(e){document.getElementById('list').innerHTML='<div class="empty">加载失败</div>'}
}
async function doReassign(){
  if(!confirm('确认将该用户所有壁纸转移给管理员？'))return;
  var r=await api('/api/v1/admin/users/'+WUID+'/reassign-wallpapers?target_user_id=1',{method:'POST'});
  var d=await r.json();
  if(d.ok){alert('已转移 '+d.reassigned+' 张');location.reload()}else{alert('操作失败: '+(d.detail||''))}
}
async function doDeleteUser(){
  if(!confirm('确定删除该用户及其所有壁纸？'))return;
  var r=await api('/api/v1/admin/users/'+WUID+'?force=true',{method:'DELETE'});
  if(r.ok){alert('已删除');location.href='/admin/users'}else{alert('删除失败')}
}
load();
</script></body></html>"""
    html = html.replace('$UNAME', uname).replace('$UID', str(user_id)).replace('$COUNT', str(wp_count))
    return HTMLResponse(html)


@router.get("/config/debug", response_class=HTMLResponse)
async def admin_debug_config_page():
    return HTMLResponse(ADMIN_DEBUG_CONFIG_HTML)


@router.get("/debug-logs", response_class=HTMLResponse)
async def admin_debug_logs_page():
    return HTMLResponse(ADMIN_DEBUG_LOGS_HTML)

