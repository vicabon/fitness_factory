#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 抓取健身工廠課表，產生 index.html（GitHub Pages）

用法：
    python generate.py
輸出 index.html，push 到 GitHub 後即可在 GitHub Pages 瀏覽。
"""
import sys, json, os
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')
from scraper import fetch_all_courses, REGIONS

OUT = os.path.join(os.path.dirname(__file__), 'index.html')

# 課程名稱黑名單關鍵字（含任一者不列出）
SKIP_KEYWORDS = ['停課', '暫停', '師資考核']

WEEKDAY_ORDER = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']


def serialize_courses(courses):
    out = []
    for c in courses:
        name = c['course_name']
        if any(kw in name for kw in SKIP_KEYWORDS):
            continue
        d = c['actual_date']
        out.append({
            'region':      c['region'],
            'store':       c['store'],
            'weekday':     c['weekday'],
            'date':        d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d),
            'date_label':  d.strftime('%m/%d') if hasattr(d, 'strftime') else '',
            'course_name': name,
            'course_time': c['course_time'],
            'teacher':     c['teacher'],
            'is_sub':      c.get('is_substitute', False),
        })
    return out


def build_store_chips():
    """Build store chip HTML grouped by region."""
    html = ''
    for region, info in REGIONS.items():
        html += f'<div class="store-region-label">{region}</div>'
        html += '<div class="chip-row store-chips">'
        for s in info['stores']:
            html += f'<label class="chip on" data-val="{s}">{s}</label>'
        html += '</div>'
    return html


# ── CSS ──────────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft JhengHei",sans-serif;
     background:#f0f3f8;color:#1a1a2e;min-height:100vh;font-size:14px}

/* header */
.hdr{background:linear-gradient(135deg,#0d1b2a,#1b4f72);color:#fff;
     padding:14px 18px;position:sticky;top:0;z-index:200;
     box-shadow:0 2px 8px rgba(0,0,0,.4)}
.hdr-row{display:flex;align-items:center;justify-content:space-between;gap:10px}
.hdr h1{font-size:17px;font-weight:700;letter-spacing:.3px}
.hdr p{font-size:11px;opacity:.65;margin-top:3px}
.btn-update{background:#e94560;color:#fff;border:none;border-radius:8px;
            padding:8px 14px;font-size:13px;font-weight:700;cursor:pointer;
            white-space:nowrap;flex-shrink:0;transition:background .15s}
.btn-update:hover{background:#c73652}

/* wrap */
.wrap{max-width:1080px;margin:0 auto;padding:12px 12px}

/* filter card */
.filter-card{background:#fff;border-radius:12px;
             box-shadow:0 1px 6px rgba(0,0,0,.08);margin-bottom:12px}
.filter-toggle{display:flex;align-items:center;justify-content:space-between;
               padding:12px 16px;cursor:pointer;user-select:none;
               border-radius:12px;transition:background .15s}
.filter-toggle:hover{background:#f4f7fb}
.filter-toggle .ftitle{font-weight:700;font-size:13px;color:#1b4f72}
.filter-toggle .farrow{font-size:16px;color:#9ab;transition:transform .2s}
.filter-toggle.open .farrow{transform:rotate(180deg)}
.filter-body{padding:0 16px 16px;display:none}
.filter-body.open{display:block}

/* filter sections */
.fsec{margin-top:14px}
.fsec-label{font-size:11px;font-weight:700;color:#9aabbf;text-transform:uppercase;
            letter-spacing:.8px;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.fsec-label a{font-size:11px;font-weight:600;text-transform:none;letter-spacing:0}

/* filter grid (2-col on wide) */
.fg{display:grid;grid-template-columns:1fr 1fr;gap:0 24px}
@media(max-width:600px){.fg{grid-template-columns:1fr}}

/* chips */
.chip-row{display:flex;flex-wrap:wrap;gap:5px}
.chip{display:inline-flex;align-items:center;gap:4px;background:#f4f7fb;
      border:1.5px solid #dde3ed;border-radius:20px;padding:6px 12px;
      font-size:13px;cursor:pointer;transition:all .15s;user-select:none;
      min-height:34px;line-height:1;white-space:nowrap;color:#6b7280}
.chip:hover{border-color:#1b4f72;background:#e8f0fb;color:#1b4f72}
.chip.on{border-color:#1b4f72;background:#1b4f72;color:#fff;font-weight:600}
.chip.on::before{content:"✓ ";font-size:11px;opacity:.9}
.chip:not(.on){opacity:.65}

/* cname chips */
.cname-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:4px 6px;
            max-height:200px;overflow-y:auto;padding-right:2px}
.cname-grid .chip{border-radius:8px;font-size:12px;padding:5px 9px;min-height:30px}
@media(max-width:600px){
  .cname-grid{grid-template-columns:repeat(2,1fr);max-height:160px}
}

/* store chips */
.store-region-label{font-size:11px;font-weight:700;color:#9aabbf;
                    margin-top:8px;margin-bottom:4px;letter-spacing:.5px}
.store-chips .chip{font-size:12px;padding:5px 10px;min-height:30px;border-radius:8px}

/* teacher input */
.ti{width:100%;border:1px solid #dde3ed;border-radius:8px;
    padding:8px 12px;font-size:13px;background:#f9fafc;outline:none}
.ti:focus{border-color:#1b4f72;background:#fff}

/* buttons row */
.brow{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;align-items:center}
.btn{padding:9px 18px;border-radius:8px;border:none;cursor:pointer;
     font-size:13px;font-weight:600;transition:all .15s}
.bp{background:#1b4f72;color:#fff}.bp:hover{background:#154360}
.bs{background:#e8ecf1;color:#556}.bs:hover{background:#d4d9e1}
.note{font-size:11px;color:#aaa;width:100%;margin-top:2px}

/* result bar */
.rbar{display:flex;justify-content:space-between;align-items:center;
      padding:9px 14px;background:#fff;border-radius:10px;
      box-shadow:0 1px 4px rgba(0,0,0,.06);margin-bottom:10px;font-size:13px}
.rcount{font-weight:700;color:#1b4f72}
.drange{color:#aaa;font-size:12px}

/* TABLE desktop */
.tbl-wrap{background:#fff;border-radius:12px;overflow:hidden;
          box-shadow:0 1px 6px rgba(0,0,0,.07)}
table{width:100%;border-collapse:collapse}
thead tr{background:#1b4f72;color:#fff}
th{padding:10px 14px;text-align:left;font-size:11px;font-weight:700;
   letter-spacing:.5px;white-space:nowrap}
td{padding:9px 14px;border-bottom:1px solid #f0f3f8;vertical-align:middle}
tr.cr:hover td{background:#f5f8fc}
tr.wh td{background:#e8f4fd;color:#154360;font-weight:700;font-size:12px;
          padding:6px 14px;border-top:2px solid #bee3f8}
.wd{font-weight:700;color:#1b4f72;white-space:nowrap}
.dt{font-size:11px;color:#9ab;display:block}
.rbadge{display:inline-block;padding:2px 9px;border-radius:10px;
        font-size:11px;font-weight:700;white-space:nowrap}
.r1{background:#dbeafe;color:#1e40af}.r2{background:#d1fae5;color:#065f46}
.clink{color:#1b4f72;text-decoration:none;font-weight:600}
.clink:hover{color:#c0392b;text-decoration:underline}
.sub-b{display:inline-block;padding:2px 7px;border-radius:9px;font-size:11px;
       font-weight:700;background:#fde8e8;color:#9b1c1c;margin-left:5px;vertical-align:middle}
.ctime{font-family:monospace;font-size:12px;color:#4a5568;white-space:nowrap}
.tch{color:#6b7280}
.nodata{text-align:center;padding:50px;color:#a0aec0;font-size:15px}

/* CARD mobile */
.card-list{display:none}
.card-item{background:#fff;border-radius:12px;margin-bottom:10px;
           padding:13px 15px;box-shadow:0 1px 5px rgba(0,0,0,.07);
           border-left:4px solid #1b4f72}
.card-item.sub{border-left-color:#e53e3e}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.card-cname{font-weight:700;font-size:15px;color:#1b4f72;line-height:1.3;text-decoration:none}
.card-cname:hover{color:#c0392b}
.card-sub{display:inline-block;padding:2px 7px;border-radius:9px;font-size:11px;
          font-weight:700;background:#fde8e8;color:#9b1c1c;margin-left:5px;vertical-align:middle}
.card-time{font-size:13px;color:#555;font-family:monospace;white-space:nowrap;flex-shrink:0}
.card-meta{display:flex;gap:7px;margin-top:7px;flex-wrap:wrap;align-items:center}
.card-badge{font-size:11px;font-weight:700;padding:2px 9px;border-radius:10px}
.card-store{font-size:13px;color:#2d3748;font-weight:600}
.card-tch{font-size:13px;color:#555;margin-top:5px}
.card-tch span{color:#888;font-size:12px}

@media(max-width:700px){
  .tbl-wrap{display:none}
  .card-list{display:block}
  .hdr h1{font-size:15px}
  th:nth-child(2),td:nth-child(2){display:none}
}

/* update modal */
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);
          z-index:500;align-items:center;justify-content:center;padding:16px}
.modal-bg.open{display:flex}
.modal{background:#fff;border-radius:14px;padding:24px;max-width:420px;width:100%;
       box-shadow:0 8px 32px rgba(0,0,0,.2)}
.modal h3{font-size:16px;font-weight:700;color:#1b4f72;margin-bottom:6px}
.modal p{font-size:13px;color:#555;margin-bottom:14px;line-height:1.5}
.modal label{font-size:12px;font-weight:700;color:#888;display:block;margin-bottom:5px}
.modal input{width:100%;border:1px solid #dde3ed;border-radius:8px;
             padding:8px 12px;font-size:13px;margin-bottom:14px;outline:none}
.modal input:focus{border-color:#1b4f72}
.modal-btns{display:flex;gap:8px;justify-content:flex-end}
.modal-status{font-size:13px;margin-top:10px;padding:8px 12px;border-radius:8px;display:none}
.modal-status.ok{background:#d1fae5;color:#065f46;display:block}
.modal-status.err{background:#fde8e8;color:#9b1c1c;display:block}
.modal-status.info{background:#dbeafe;color:#1e40af;display:block}
"""

# ── JavaScript ────────────────────────────────────────────────────────────────
JS = r"""
const WEEKDAY_ORDER = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日'];

// ── 課程名稱清單（去重排序）────────────────────────────────────────────────
const allCnames = [...new Set(COURSES.map(c => c.course_name))]
  .sort((a,b) => a.localeCompare(b,'zh-TW'));

function buildCnameGrid() {
  const grid = document.getElementById('cnameGrid');
  grid.innerHTML = allCnames.map(n =>
    `<label class="chip on" data-val="${n}">${n}</label>`
  ).join('');
  // 事件委派：防止 label 雙觸發
  grid.addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    chip.classList.toggle('on');
    applyFilter();
  });
}

// ── store chips：事件委派（防止 label 雙觸發）─────────────────────────────
document.querySelectorAll('.store-chips').forEach(container => {
  container.addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    chip.classList.toggle('on');
    applyFilter();
  });
});
function toggleAllStores(on) {
  document.querySelectorAll('.store-chips .chip').forEach(c => {
    on ? c.classList.add('on') : c.classList.remove('on');
  });
  applyFilter();
}

// ── 讀取篩選狀態 ──────────────────────────────────────────────────────────
function selectedCnames() {
  const all  = document.querySelectorAll('#cnameGrid .chip');
  const on   = [...all].filter(c => c.classList.contains('on')).map(c => c.dataset.val);
  return on.length === all.length ? null : on; // null = 全部
}
function selectedStores() {
  const all = document.querySelectorAll('.store-chips .chip');
  const on  = [...all].filter(c => c.classList.contains('on')).map(c => c.dataset.val);
  return on.length === all.length ? [] : on;   // [] = 全部
}
function teacherFilter() {
  return document.getElementById('teacherInput').value
    .split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
}

function toggleAllCnames(on) {
  document.querySelectorAll('#cnameGrid .chip').forEach(c => {
    on ? c.classList.add('on') : c.classList.remove('on');
  });
  applyFilter();
}

// ── 篩選 + 渲染 ──────────────────────────────────────────────────────────
function applyFilter() {
  const cnames   = selectedCnames();
  const stores   = selectedStores();
  const teachers = teacherFilter();

  // 今日日期字串 YYYY-MM-DD（本地時間）
  const today = new Date();
  const todayStr = today.getFullYear() + '-'
    + String(today.getMonth()+1).padStart(2,'0') + '-'
    + String(today.getDate()).padStart(2,'0');

  let rows = COURSES.filter(c => {
    if(c.date < todayStr)  return false;   // 過去日期略過
    if(stores.length  && !stores.includes(c.store))   return false;
    if(cnames && !cnames.includes(c.course_name))     return false;
    if(teachers.length && !teachers.some(t => c.teacher.toLowerCase().includes(t))) return false;
    return true;
  });

  rows.sort((a,b) =>
    a.date.localeCompare(b.date)
    || a.course_time.localeCompare(b.course_time)
    || a.store.localeCompare(b.store,'zh-TW')
  );

  renderTable(rows);
  renderCards(rows);
  document.getElementById('rcount').textContent = '共 ' + rows.length + ' 筆課程';
}

function subBadge(c) {
  return c.is_sub ? '<span class="sub-b">代課</span>' : '';
}

function renderTable(rows) {
  const tbody  = document.getElementById('tblBody');
  const noData = document.getElementById('tableNoData');
  if (!rows.length) { tbody.innerHTML=''; noData.style.display='block'; return; }
  noData.style.display = 'none';

  let html = '', prevKey = '';
  rows.forEach(c => {
    const key = c.weekday + c.date;
    if (key !== prevKey) {
      html += '<tr class="wh"><td colspan="6">&#9658; ' + c.weekday + '&nbsp;&nbsp;' + c.date_label + '</td></tr>';
      prevKey = key;
    }
    const rCls = c.region === '北一區' ? 'r1' : 'r2';
    const url  = 'https://www.fitnessfactory.com.tw/tw/course/' + encodeURIComponent(c.course_name);
    html += '<tr class="cr" data-wd="' + c.weekday + '">'
      + '<td class="wd">' + c.weekday + '<span class="dt">' + c.date_label + '</span></td>'
      + '<td><span class="rbadge ' + rCls + '">' + c.region + '</span></td>'
      + '<td>' + c.store + '</td>'
      + '<td><a class="clink" href="' + url + '" target="_blank">' + c.course_name + '</a>' + subBadge(c) + '</td>'
      + '<td class="ctime">' + c.course_time + '</td>'
      + '<td class="tch">' + c.teacher + '</td>'
      + '</tr>';
  });
  tbody.innerHTML = html;

  tbody.querySelectorAll('tr.cr').forEach(tr => {
    tr.addEventListener('mouseenter', () => {
      const wd = tr.dataset.wd;
      tbody.querySelectorAll('tr.cr[data-wd="' + wd + '"]').forEach(r => r.style.background='#edf5ff');
    });
    tr.addEventListener('mouseleave', () => {
      tbody.querySelectorAll('tr.cr').forEach(r => r.style.background='');
    });
  });
}

function renderCards(rows) {
  const list   = document.getElementById('cardList');
  const noData = document.getElementById('cardNoData');
  if (!rows.length) { list.innerHTML=''; noData.style.display='block'; return; }
  noData.style.display = 'none';

  let html = '', prevKey = '';
  rows.forEach(c => {
    const key = c.weekday + c.date;
    if (key !== prevKey) {
      html += '<div style="font-size:12px;font-weight:700;color:#1b4f72;padding:8px 4px 4px;letter-spacing:.3px">'
            + '&#9658; ' + c.weekday + '&nbsp;' + c.date_label + '</div>';
      prevKey = key;
    }
    const rCls   = c.region === '北一區' ? 'r1' : 'r2';
    const subCls = c.is_sub ? ' sub' : '';
    const url    = 'https://www.fitnessfactory.com.tw/tw/course/' + encodeURIComponent(c.course_name);
    html += '<div class="card-item' + subCls + '">'
      + '<div class="card-top">'
      + '<div><a class="card-cname" href="' + url + '" target="_blank">' + c.course_name + '</a>'
      + (c.is_sub ? '<span class="card-sub">代課</span>' : '') + '</div>'
      + '<div class="card-time">' + c.course_time + '</div>'
      + '</div>'
      + '<div class="card-meta">'
      + '<span class="rbadge card-badge ' + rCls + '">' + c.region + '</span>'
      + '<span class="card-store">' + c.store + '</span>'
      + '</div>'
      + '<div class="card-tch"><span>老師：</span>' + c.teacher + '</div>'
      + '</div>';
  });
  list.innerHTML = html;
}

// ── 篩選面板開關 ──────────────────────────────────────────────────────────
function toggleFilter() {
  document.getElementById('ftoggle').classList.toggle('open');
  document.getElementById('fbody').classList.toggle('open');
}
function resetFilter() {
  document.querySelectorAll('#cnameGrid .chip').forEach(c => c.classList.add('on'));
  document.querySelectorAll('.store-chips .chip').forEach(c => c.classList.add('on'));
  document.getElementById('teacherInput').value = '';
  applyFilter();
}

// ── 更新課表（GitHub Actions trigger）────────────────────────────────────
function openUpdateModal() {
  document.getElementById('updateModal').classList.add('open');
  document.getElementById('modalStatus').className = 'modal-status';
  document.getElementById('modalStatus').textContent = '';
  const saved = localStorage.getItem('gh_token') || '';
  document.getElementById('ghToken').value = saved;
}
function closeUpdateModal() {
  document.getElementById('updateModal').classList.remove('open');
}

function getGitHubInfo() {
  const host = window.location.hostname;
  const path = window.location.pathname;
  const m = host.match(/^(.+)\.github\.io$/);
  if (!m) return null;
  const owner = m[1];
  const segments = path.split('/').filter(Boolean);
  const repo = segments.length > 0 ? segments[0] : owner + '.github.io';
  return { owner, repo };
}

async function triggerUpdate() {
  const token = document.getElementById('ghToken').value.trim();
  if (!token) { showStatus('err', '請輸入 GitHub Personal Access Token'); return; }

  const info = getGitHubInfo();
  if (!info) {
    showStatus('err', '本機開啟無法觸發，請執行 python generate.py 後 push');
    return;
  }

  localStorage.setItem('gh_token', token);
  showStatus('info', '觸發中...');

  try {
    const resp = await fetch(
      'https://api.github.com/repos/' + info.owner + '/' + info.repo
      + '/actions/workflows/update-schedule.yml/dispatches',
      {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token,
          'Accept': 'application/vnd.github+json',
          'Content-Type': 'application/json',
          'X-GitHub-Api-Version': '2022-11-28',
        },
        body: JSON.stringify({ ref: 'main' }),
      }
    );
    if (resp.status === 204) {
      showStatus('ok', '已觸發更新！約 3-5 分鐘後重新整理頁面即可看到最新課表。');
    } else {
      const data = await resp.json().catch(() => ({}));
      showStatus('err', '失敗：' + (data.message || 'HTTP ' + resp.status));
    }
  } catch(e) {
    showStatus('err', '網路錯誤：' + e.message);
  }
}

function showStatus(type, msg) {
  const el = document.getElementById('modalStatus');
  el.className = 'modal-status ' + type;
  el.textContent = msg;
}

// ── 初始化 ────────────────────────────────────────────────────────────────
buildCnameGrid();

// 預設課程名稱：含「瑜珈」且排除指定課程
const YOGA_EXCLUDE = new Set(['體適能瑜珈','瑜珈提斯','陰瑜珈']);
document.querySelectorAll('#cnameGrid .chip').forEach(c => {
  const n = c.dataset.val;
  const on = n.includes('瑜珈') && !YOGA_EXCLUDE.has(n);
  on ? c.classList.add('on') : c.classList.remove('on');
});

// 預設廠館
const DEFAULT_STORES = new Set([
  '台北萬隆','台北長春','台北信義','台北健康','台北中山北',
  '新北板橋','新北雙和','新北中和','新北新埔','新北三重'
]);
document.querySelectorAll('.store-chips .chip').forEach(c => {
  DEFAULT_STORES.has(c.dataset.val) ? c.classList.add('on') : c.classList.remove('on');
});

if (window.innerWidth > 700) toggleFilter(); // 桌機預設展開
applyFilter();
"""

# ── HTML template ─────────────────────────────────────────────────────────────
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>健身工廠課表 | 北一區 / 北二區</title>
<style>__CSS__</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-row">
    <div>
      <h1>&#127947; 健身工廠課表查詢</h1>
      <p>北一區（台北市）/ 北二區（新北市）&#183; 早上至 18:00 &#183; __DATE_RANGE__</p>
    </div>
    <button class="btn-update" onclick="openUpdateModal()">&#8635; 更新課表</button>
  </div>
</div>

<div class="wrap">

  <!-- 篩選 -->
  <div class="filter-card">
    <div class="filter-toggle" id="ftoggle" onclick="toggleFilter()">
      <span class="ftitle">&#128269; 篩選條件</span>
      <span class="farrow" id="farrow">&#8964;</span>
    </div>
    <div class="filter-body" id="fbody">
      <div class="fg">

        <!-- 左欄：課程名稱 -->
        <div>
          <div class="fsec">
            <span class="fsec-label">
              課程名稱
              <a href="#" onclick="toggleAllCnames(true);return false" style="color:#1b4f72">全選</a>
              <span style="color:#ccc">/</span>
              <a href="#" onclick="toggleAllCnames(false);return false" style="color:#888">全消</a>
            </span>
            <div class="cname-grid" id="cnameGrid"></div>
          </div>
        </div>

        <!-- 右欄：指定廠館 + 授課老師 -->
        <div>
          <div class="fsec">
            <span class="fsec-label">
              指定廠館
              <a href="#" onclick="toggleAllStores(true);return false" style="color:#1b4f72">全選</a>
              <span style="color:#ccc">/</span>
              <a href="#" onclick="toggleAllStores(false);return false" style="color:#888">全消</a>
            </span>
            __STORE_CHIPS__
          </div>
          <div class="fsec" style="margin-top:16px">
            <span class="fsec-label">授課老師（逗號分隔多位）</span>
            <input type="text" id="teacherInput" class="ti"
                   placeholder="例：Jeremy, 威廉" oninput="applyFilter()">
          </div>
        </div>

      </div>
      <div class="brow">
        <button class="btn bp" onclick="applyFilter()">&#128269; 套用</button>
        <button class="btn bs" onclick="resetFilter()">重置</button>
        <span class="note">資料更新：__GENERATED_AT__</span>
      </div>
    </div>
  </div>

  <!-- 結果列 -->
  <div class="rbar">
    <span class="rcount" id="rcount">載入中...</span>
    <span class="drange">__DATE_RANGE__</span>
  </div>

  <!-- 表格（桌機） -->
  <div class="tbl-wrap" id="tableWrap">
    <table>
      <thead>
        <tr>
          <th>星期 / 日期</th><th>區域</th><th>廠館</th>
          <th>課程名稱</th><th>課程時間</th><th>授課老師</th>
        </tr>
      </thead>
      <tbody id="tblBody"></tbody>
    </table>
  </div>
  <div id="tableNoData" class="nodata" style="display:none">沒有符合條件的課程</div>

  <!-- Card 列表（手機） -->
  <div class="card-list" id="cardList"></div>
  <div id="cardNoData" class="nodata" style="display:none">沒有符合條件的課程</div>

</div>

<!-- 更新課表 Modal -->
<div class="modal-bg" id="updateModal" onclick="if(event.target===this)closeUpdateModal()">
  <div class="modal">
    <h3>&#8635; 更新課表</h3>
    <p>透過 GitHub Actions 重新抓取課表並自動更新頁面。<br>
       需要具備 <strong>Actions: Write</strong> 權限的 Personal Access Token。</p>
    <label>GitHub Personal Access Token</label>
    <input type="password" id="ghToken" placeholder="ghp_xxxxxxxxxxxx">
    <div id="modalStatus" class="modal-status"></div>
    <div class="modal-btns">
      <button class="btn bs" onclick="closeUpdateModal()">取消</button>
      <button class="btn bp" onclick="triggerUpdate()">觸發更新</button>
    </div>
  </div>
</div>

<script>
const COURSES = __COURSES_JSON__;
__JS__
</script>
</body>
</html>
"""


def main():
    print('健身工廠課表產生器', flush=True)
    print('抓取中（北一區 + 北二區，約 2-3 分鐘）...', flush=True)

    courses, dates = fetch_all_courses()
    print(f'共取得 {len(courses)} 筆課程', flush=True)

    serialized = serialize_courses(courses)
    skipped = len(courses) - len(serialized)
    if skipped:
        print(f'過濾停課/暫停/師資考核：{skipped} 筆', flush=True)

    courses_json   = json.dumps(serialized, ensure_ascii=False)
    date_range     = f"{dates[0]} ~ {dates[-1]}" if len(dates) >= 2 else (dates[0] if dates else '')
    generated_at   = datetime.now().strftime('%Y-%m-%d %H:%M')

    html = HTML_TEMPLATE
    html = html.replace('__CSS__',          CSS)
    html = html.replace('__JS__',           JS)
    html = html.replace('__COURSES_JSON__', courses_json)
    html = html.replace('__STORE_CHIPS__',  build_store_chips())
    html = html.replace('__DATE_RANGE__',   date_range)
    html = html.replace('__GENERATED_AT__', generated_at)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'輸出完成 → {OUT}', flush=True)
    print()
    print('下一步：')
    print('  git add index.html')
    print('  git commit -m "Update course schedule"')
    print('  git push')


if __name__ == '__main__':
    main()
