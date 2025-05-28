// ==UserScript==
// @name         Zhihu Blocklist Sync (ZHBL)
// @namespace    https://github.com/c6h6cl6-code/
// @version      1.2.0
// @description  在知乎过滤设置页一键同步 ZHBL 黑名单（namespace→generation 本地保存，账号隔离）
// @author       C6H6Cl6
// @match        https://www.zhihu.com/settings/filter*
// @grant        none
// @connect      raw.githubusercontent.com
// @connect      zhihu.com
// ==/UserScript==
(function () {
  'use strict';

  /* ────────────── 工具 ────────────── */
  function getCurrentUserToken() {
    const el = document.querySelector('[data-zop-usertoken]');
    if (!el) return 'anonymous';
    try {
      return JSON.parse(el.getAttribute('data-zop-usertoken')).urlToken || 'anonymous';
    } catch {
      return 'anonymous';
    }
  }

  /* ────────────── UI ────────────── */
  function insertButton() {
    const host = document.body;
    if (!host) return;

    const btn = document.createElement('button');
    btn.textContent = '同步黑名单（ZHBL）';
    btn.style.position = 'fixed';
    btn.style.top = '20px';
    btn.style.right = '20px';
    btn.style.zIndex = '9999';
    btn.style.padding = '8px 12px';
    btn.style.backgroundColor = '#0084FF';
    btn.style.color = '#fff';
    btn.style.border = 'none';
    btn.style.borderRadius = '4px';
    btn.style.cursor = 'pointer';
    btn.onclick = runSync;
    host.appendChild(btn);
  }

  /* ────────────── 主流程 ────────────── */
  async function runSync() {

    /* === 1. 初始化与持久化 === */
    const account      = getCurrentUserToken();                    // ← 现在才读取
    const LS_MAP_KEY   = `zhbl_ns_map_${account}`;

    let NS_GEN = {};
    try { NS_GEN = JSON.parse(localStorage.getItem(LS_MAP_KEY)) || {}; }
    catch { NS_GEN = {}; }

    function saveMap() {
      try { localStorage.setItem(LS_MAP_KEY, JSON.stringify(NS_GEN)); } catch {}
    }

    /* === 2. 读取首个列表地址 === */
    const DEFAULT_LIST =
      'https://raw.githubusercontent.com/c6h6cl6-code/zh-mxz-list/refs/heads/main/blocklist.txt';
    const firstList = prompt('请输入首个 ZHBL 列表地址', DEFAULT_LIST) || DEFAULT_LIST;

    /* === 3. 变量准备 === */
    const DELAY = 1000;
    const queue = [];
    const seen  = new Set();
    const NS_MAX = {};
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

    /* === 4. 小工具 === */
    async function id2token(uid) {
      try {
        const res = await fetch(`https://www.zhihu.com/people/${uid}`, { credentials: 'include' });
        const html = await res.text();
        const doc  = new DOMParser().parseFromString(html, 'text/html');
        const js   = doc.querySelector('#js-initialData');
        const data = js && JSON.parse(js.textContent);
        const uObj = Object.values(data?.initialState?.entities?.users || {}).find(u => u.id === uid);
        return uObj?.urlToken || null;
      } catch { return null; }
    }

    async function tryBlock(token, displayName) {
      try {
        const r = await fetch(
          `https://www.zhihu.com/api/v4/members/${token}/actions/block`,
          { method: 'POST', headers: { 'Content-Length': '0' }, credentials: 'include' },
        );
        if (r.ok) {
          console.log(`✅ 封禁成功: ${displayName}`);
          return true;
        }
        console.warn(`🔁 首次封禁失败 (${r.status}) → ${displayName}`);
        return false;
      } catch (e) {
        console.warn('🔁 封禁请求异常 →', e);
        return false;
      }
    }

    /* === 5. 递归解析 blocklist === */
    async function parseList(url) {
      if (seen.has(url)) return;
      seen.add(url);

      let text;
      try { text = await (await fetch(url)).text(); }
      catch (e) { console.error('[ZHBL] 读取失败:', url, e); return; }

      const lines = text.split(/\r?\n/);
      let title = null, ns = null;
      for (const l of lines) {
        const t = l.match(/^\s*!+\s*Title:\s*(.+)$/i);
        if (t) title = t[1].trim();
        const n = l.match(/^\s*!+\s*Namespace:\s*(.+)$/i);
        if (n) ns = n[1].trim();
        if (title && ns) break;
      }
      console.log(`[ZHBL] Blocklist Title: ${title || '(未声明 Title)'}`);
      if (ns && !NS_MAX.hasOwnProperty(ns)) NS_MAX[ns] = 0;

      let mode = 'full', threshold = null;
      if (!ns) {
        console.warn('[ZHBL] 未声明 Namespace → 完整处理');
      } else if (NS_GEN.hasOwnProperty(ns)) {
        mode = 'filtered';
        threshold = NS_GEN[ns];
        console.log(`[ZHBL] Namespace "${ns}" 已映射，代数 = ${threshold}`);
      } else {
        const ans = prompt(
          `检测到新的 Namespace "${ns}"。\n请输入 generation 阈值（留空/非法 = 完整处理）`, '',
        );
        const g = parseInt(ans, 10);
        if (!isNaN(g)) {
          NS_GEN[ns] = g;
          saveMap();
          mode = 'filtered';
          threshold = g;
          console.log(`[ZHBL] 新增映射 ${ns}=${g}`);
        } else {
          console.warn('[ZHBL] 无效输入 → 完整处理');
        }
      }

      for (const raw of lines) {
        const line = raw.trim();
        if (!line || /^[!#]/.test(line)) continue;

        if (line.startsWith('i,')) {
          const [, child] = line.split(',');
          if (child) await parseList(child.trim());
          continue;
        }

        if (line.startsWith('u,')) {
          const [, gStr, token, uid, name] = line.split(',');
          const gen = parseInt(gStr, 10);
          if (ns) NS_MAX[ns] = Math.max(NS_MAX[ns], isNaN(gen) ? 0 : gen);
          if (mode === 'filtered' && gen <= threshold) continue;
          queue.push({
            token: (token || '').trim(),
            userId: (uid || '').trim(),
            name:   (name  || '').trim(),
          });
        }
      }
    }

    /* === 6. 解析 & 执行封禁 === */
    console.log('[ZHBL] 解析列表开始:', firstList);
    await parseList(firstList);

    if (!queue.length) {
      console.log('[ZHBL] 没有符合条件的用户');
    } else {
      console.log(`[ZHBL] 待封禁 ${queue.length} 行，开始执行…`);
      for (const u of queue) {
        let token = u.token;
        let ok = false;
        if (token) ok = await tryBlock(token, u.name || token);

        if (!token || !ok) {
          const newToken = await id2token(u.userId);
          if (newToken && newToken !== token) {
            await tryBlock(newToken, u.name || newToken);
          } else {
            console.warn(`⚠️  跳过：无法获取有效 urlToken → ${u.userId} / ${u.name}`);
          }
        }
        await sleep(DELAY);
      }
      console.log('[ZHBL] 封禁流程结束，共处理 ' + queue.length + ' 行');
    }

    /* === 7. 合并代数 & 保存 === */
    for (const [ns, gen] of Object.entries(NS_MAX)) {
      NS_GEN[ns] = Math.max(NS_GEN[ns] || 0, gen);      // 只升不降
    }
    saveMap();

    const statsText = Object.entries(NS_GEN)
      .map(([ns, g]) => `${ns}: ${Math.max(1, g)}`)
      .join('\n');
    console.log('╭─ 各 Namespace 最高代数统计 ─\n' + statsText + '\n╰────────────────────────');
    alert('ZHBL 同步完成！\n\n' + statsText);
  }

  /* ────────────── 注入按钮 ────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', insertButton);
  } else {
    insertButton();
  }
})();
