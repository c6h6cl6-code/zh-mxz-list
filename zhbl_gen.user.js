// ==UserScript==
// @name         ZHBL Rule Generator
// @namespace    https://github.com/c6h6cl6-code/
// @version      1.0
// @description  Adds a button to extract Zhihu user ID and name
// @author       C6H6Cl6
// @match        https://www.zhihu.com/people/*
// @grant        GM_setClipboard
// ==/UserScript==

(function () {
  'use strict';

  // Create button
  const btn = document.createElement('button');
  btn.textContent = 'Get ZHBL Rule';
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

  btn.addEventListener('click', () => {
    try {
      // Extract urlToken from URL
      const urlToken = location.pathname.split('/').filter(p => p)[1].split('?')[0];
      if (!urlToken) throw new Error("Cannot extract urlToken from URL.");

      // Read raw JSON
      const rawData = document.querySelector('#js-initialData')?.textContent;
      if (!rawData) throw new Error("Cannot find js-initialData element.");

      const data = JSON.parse(rawData);
      const userObj = data?.initialState?.entities?.users?.[urlToken];
      if (!userObj) throw new Error(`User object not found for urlToken "${urlToken}".`);

      const userID = userObj.id;
      const name = userObj.name || "(no name)";
      const result = `u,0,${urlToken},${userID},${name}`;

      console.log(result);
      GM_setClipboard(result, { type: 'text', mimetype: 'text/plain' });
      prompt("Copied to clipboard:", result);
    } catch (e) {
      console.error("Error:", e.message);
      alert("Error: " + e.message);
    }
  });

  window.addEventListener('load', () => {
    document.body.appendChild(btn);
  });
})();
