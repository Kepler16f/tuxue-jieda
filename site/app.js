/* 图学基础教程习题解答 · 移动端 Web 应用（无框架，v4 模块题表） */
(function () {
  'use strict';

  var VERSION = '0.3.1';
  var BUILD = '2026-10-15';
  var DATA = window.INDEX_DATA;
  var view = document.getElementById('view');
  var topTitle = document.getElementById('title');
  var btnBack = document.getElementById('btn-back');

  if (!DATA || !DATA.pages) {
    view.innerHTML = '<div class="loaderr">索引数据未加载（缺少 data/index.js）</div>';
    return;
  }

  /* ---------- 模型（v4: modules 结构） ---------- */
  var PAGES = DATA.pages;
  var PAGE_ITEMS = {};
  var ITEMS = {};
  var ORDER = [];
  PAGES.forEach(function (pg) {
    PAGE_ITEMS[pg.page] = pg.items;
    pg.items.forEach(function (it) {
      ITEMS[it.id] = it;
      ORDER.push(it.id);
    });
  });
  var PAGENO = PAGES.map(function (p) { return p.page; });

  /* 用户校正的标签（教材页码/题号），存 localStorage */
  var CORR = {};
  try { CORR = JSON.parse(localStorage.getItem('corrections') || '{}'); } catch (e) {}
  function labelOf(it) { return CORR[it.id] || it.label; }
  function saveCorr() {
    try { localStorage.setItem('corrections', JSON.stringify(CORR)); } catch (e) {}
  }

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function fmtText(s) {
    if (!s) return '';
    var t = s.replace(/\r\n?/g, '\n').replace(/^[0-9A-Z]{1,4},\s*/, '');
    return esc(t);
  }
  function chipLabel(it) {
    // 从 label 提取短标签: "第42题" -> "42", "第19题(1)" -> "19(1)"
    var m = /^第(\d+)题(?:\((\d+)\))?(·变式)?$/.exec(it.label || '');
    if (m) return m[1] + (m[2] ? '(' + m[2] + ')' : '') + (m[3] ? '变' : '');
    return (it.tihao || it.id).slice(0, 8);
  }
  function snippet(it) {
    var t = (it.text || '').replace(/\r\n?/g, ' ').replace(/^[0-9A-Z]{1,4},\s*/, '').trim();
    return t.slice(0, 56);
  }
  function h(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else if (k.slice(0, 2) === 'on') n.addEventListener(k.slice(2), attrs[k]);
      else n.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  /* ---------- 外观 ---------- */
  var mql = window.matchMedia('(prefers-color-scheme: dark)');
  function appearance() {
    try { return localStorage.getItem('appearance') || 'auto'; } catch (e) { return 'auto'; }
  }
  function applyAppearance() {
    var ap = appearance();
    if (ap === 'auto') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', ap);
  }
  mql.addEventListener('change', function () { if (appearance() === 'auto') applyAppearance(); });
  applyAppearance();

  /* ---------- 图片查看器 ---------- */
  var viewer = document.getElementById('viewer');
  var vImg = document.getElementById('viewer-img');
  var vCount = document.getElementById('v-count');
  var vState = { list: [], idx: 0, scale: 1, tx: 0, ty: 0 };

  function applyTransform() {
    vImg.style.transform = 'translate(' + vState.tx + 'px,' + vState.ty + 'px) scale(' + vState.scale + ')';
  }
  function openViewer(list, idx) {
    vState.list = list; vState.idx = idx || 0;
    vState.scale = 1; vState.tx = 0; vState.ty = 0;
    showViewerImage();
    viewer.hidden = false;
    document.body.style.overflow = 'hidden';
  }
  function showViewerImage() {
    var item = vState.list[vState.idx];
    vImg.src = item.src;
    vImg.alt = item.cap || '';
    vCount.textContent = (vState.idx + 1) + ' / ' + vState.list.length;
    vState.scale = 1; vState.tx = 0; vState.ty = 0;
    applyTransform();
  }
  function closeViewer() {
    viewer.hidden = true;
    document.body.style.overflow = '';
    vImg.src = '';
  }
  document.getElementById('viewer-close').addEventListener('click', closeViewer);
  document.getElementById('v-prev').addEventListener('click', function () {
    if (vState.idx > 0) { vState.idx--; showViewerImage(); }
  });
  document.getElementById('v-next').addEventListener('click', function () {
    if (vState.idx < vState.list.length - 1) { vState.idx++; showViewerImage(); }
  });

  (function viewerGestures() {
    var pts = {};
    var last = null, pinch0 = null, swipe0 = null;
    var lastTap = 0;
    function pdist() {
      var ks = Object.keys(pts);
      if (ks.length < 2) return 0;
      var a = pts[ks[0]], b = pts[ks[1]];
      return Math.hypot(a.x - b.x, a.y - b.y);
    }
    viewer.addEventListener('pointerdown', function (e) {
      pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      if (Object.keys(pts).length === 1) {
        last = { x: e.clientX, y: e.clientY, tx: vState.tx, ty: vState.ty };
        swipe0 = { x: e.clientX, y: e.clientY };
      } else if (Object.keys(pts).length === 2) {
        pinch0 = { d: pdist(), scale: vState.scale };
      }
      viewer.setPointerCapture(e.pointerId);
    });
    viewer.addEventListener('pointermove', function (e) {
      if (!(e.pointerId in pts)) return;
      pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      var n = Object.keys(pts).length;
      if (n >= 2 && pinch0) {
        var k = pdist() / (pinch0.d || 1);
        vState.scale = Math.min(6, Math.max(1, pinch0.scale * k));
        if (vState.scale === 1) { vState.tx = 0; vState.ty = 0; }
        applyTransform();
      } else if (n === 1 && last && vState.scale > 1) {
        vState.tx = last.tx + (e.clientX - last.x);
        vState.ty = last.ty + (e.clientY - last.y);
        applyTransform();
      }
    });
    viewer.addEventListener('pointerup', function (e) {
      delete pts[e.pointerId];
      if (Object.keys(pts).length < 2) pinch0 = null;
      var now = Date.now();
      if (swipe0 && Math.abs(e.clientX - swipe0.x) < 8 && Math.abs(e.clientY - swipe0.y) < 8) {
        if (now - lastTap < 320) {
          if (vState.scale > 1) { vState.scale = 1; vState.tx = 0; vState.ty = 0; }
          else { vState.scale = 2.5; }
          applyTransform();
          lastTap = 0;
          return;
        }
        lastTap = now;
      }
      if (swipe0 && vState.scale === 1) {
        var dx = e.clientX - swipe0.x, dy = e.clientY - swipe0.y;
        if (Math.abs(dx) > 60 && Math.abs(dy) < 50) {
          if (dx < 0 && vState.idx < vState.list.length - 1) { vState.idx++; showViewerImage(); }
          else if (dx > 0 && vState.idx > 0) { vState.idx--; showViewerImage(); }
        }
      }
      last = null; swipe0 = null;
    });
    viewer.addEventListener('pointercancel', function (e) { delete pts[e.pointerId]; });
  })();

  /* ---------- 轮播（逐帧播放） ---------- */
  function buildCarousel(images, cap) {
    if (!images.length) return null;
    var list = images.map(function (src, i) {
      return { src: src, cap: (cap || '') + ' ' + (i + 1) + '/' + images.length };
    });
    if (images.length === 1) {
      return h('div', { class: 'imgwrap' }, [
        h('img', { src: images[0], loading: 'lazy', alt: cap || '',
          onclick: function () { openViewer(list, 0); } })
      ]);
    }
    var idx = 0, timer = null;
    var stage = h('img', { loading: 'lazy', alt: cap || '' });
    var cnt = h('span', { class: 'cnt' });
    var btnPlay = h('button', { class: 'play', text: '▶', 'aria-label': '播放' });
    var btnPrev = h('button', { text: '‹', 'aria-label': '上一张' });
    var btnNext = h('button', { text: '›', 'aria-label': '下一张' });
    function show(i) {
      idx = (i + images.length) % images.length;
      stage.src = images[idx];
      cnt.textContent = (idx + 1) + ' / ' + images.length;
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } btnPlay.textContent = '▶'; }
    function play() {
      stop();
      if (images.length < 2) return;
      btnPlay.textContent = '❚❚';
      timer = setInterval(function () {
        if (idx >= images.length - 1) { stop(); return; }
        show(idx + 1);
      }, 1200);
    }
    btnPlay.addEventListener('click', function () { timer ? stop() : play(); });
    btnPrev.addEventListener('click', function () { stop(); show(idx - 1); });
    btnNext.addEventListener('click', function () { stop(); show(idx + 1); });
    stage.addEventListener('click', function () { stop(); openViewer(list, idx); });
    show(0);
    return h('div', { class: 'car' }, [
      h('div', { class: 'car-stage' }, [stage]),
      h('div', { class: 'car-ctl' }, [btnPrev, btnPlay, cnt, btnNext])
    ]);
  }

  /* ---------- 标签页（内容驱动：没内容就不出标签） ---------- */
  var openTab = {};

  function tabsFor(it) {
    var tabs = [];
    if (it.question.length || it.n_question.length || it.frames_s.length) tabs.push(['q', '题目']);
    if (it.answer.length || it.n_answer.length || it.frames_a.length) tabs.push(['a', '答案']);
    if (it.e_series.length || Object.keys(it.letters || {}).length) tabs.push(['st', '演示']);
    if (it.videos.length) tabs.push(['vid', '动画']);
    return tabs;
  }

  function renderQ(body, it) {
    function paint() {
      clear(body);
      var seg = variantSeg(it, 'q', paint);
      if (seg) body.appendChild(seg);
      var imgs = (it.__vq === 'n' || !it.question.length) ? it.n_question.slice() : it.question.slice();
      var car = buildCarousel(imgs, '题图');
      if (car) body.appendChild(car);
      if (it.frames_s.length) {
        body.appendChild(h('div', { class: 'subsec' }, [
          h('div', { class: 'subh', text: '作图过程' }),
          buildCarousel(it.frames_s, '过程')
        ]));
      }
      if (!imgs.length && !it.frames_s.length)
        body.appendChild(h('div', { class: 'hint pad', text: '该题未收录题图。' }));
    }
    paint();
  }

  function renderA(body, it) {
    function paint() {
      clear(body);
      var seg = variantSeg(it, 'a', paint);
      if (seg) body.appendChild(seg);
      var imgs = (it.__va === 'n' || !it.answer.length) ? it.n_answer.slice() : it.answer.slice();
      var car = buildCarousel(imgs, '答案');
      if (car) body.appendChild(car);
      if (it.frames_a.length) {
        body.appendChild(h('div', { class: 'subsec' }, [
          h('div', { class: 'subh', text: '解答过程' }),
          buildCarousel(it.frames_a, '解答')
        ]));
      }
      if (!imgs.length && !it.frames_a.length)
        body.appendChild(h('div', { class: 'hint pad', text: '未收录答案图。' }));
    }
    paint();
  }

  function renderSt(body, it) {
    clear(body);
    var letters = Object.keys(it.letters || {}).sort();
    if (letters.length) {
      var cur = it.__letter || letters[0];
      it.__letter = cur;
      var seg = h('div', { class: 'seg' });
      letters.forEach(function (L) {
        seg.appendChild(h('button', { text: '图 ' + L, class: cur === L ? 'on' : '',
          onclick: function () { it.__letter = L; renderSt(body, it); } }));
      });
      body.appendChild(h('div', { class: 'subsec' }, [
        h('div', { class: 'subh', text: '组合体三视图（' + letters.length + ' 个变体）' }),
        seg,
        h('img', { src: it.letters[cur], style: 'max-width:100%;border-radius:10px;border:1px solid var(--line);background:#fff',
          onclick: function () { openViewer(letters.map(function (L) { return { src: it.letters[L], cap: '图 ' + L }; }), letters.indexOf(cur)); } })
      ]));
    }
    if (it.e_series.length) {
      body.appendChild(h('div', { class: 'subsec' }, [
        h('div', { class: 'subh', text: '展开过程' }),
        buildCarousel(it.e_series.map(function (e) { return e.img; }), '展开')
      ]));
    }
    if (!body.children.length) body.appendChild(h('div', { class: 'hint pad', text: '本题无演示内容。' }));
  }

  function renderVid(body, it) {
    clear(body);
    it.videos.forEach(function (v) {
      body.appendChild(h('div', { class: 'vidblock' }, [
        h('video', { controls: 'controls', preload: 'none', poster: v.poster, src: v.src }),
        h('div', { class: 'vcap', text: '解题动画' })
      ]));
    });
    if (!it.videos.length) body.appendChild(h('div', { class: 'hint pad', text: '本题无动画。' }));
  }

  var RENDERERS = { q: renderQ, a: renderA, st: renderSt, vid: renderVid };

  function variantSeg(it, which, onChange) {
    var plain = which === 'q' ? it.question : it.answer;
    var nvar = which === 'q' ? it.n_question : it.n_answer;
    if (!plain.length || !nvar.length) return null;
    var cur = it['__v' + which];
    if (cur === undefined) cur = 'p';
    it['__v' + which] = cur;
    var seg = h('div', { class: 'seg' });
    [['p', '原题'], ['n', '变式']].forEach(function (opt) {
      seg.appendChild(h('button', { text: opt[1], class: cur === opt[0] ? 'on' : '',
        onclick: function () { it['__v' + which] = opt[0]; onChange(); } }));
    });
    return seg;
  }

  /* ---------- 单题内容面板 ---------- */
  function renderProblem(container, it) {
    clear(container);
    container.classList.remove('split');
    var tabs = tabsFor(it);
    var text = it.text;
    if (text && tabs.length) container.classList.add('split');
    if (text) container.appendChild(h('div', { class: 'qtext card-lite', html: fmtText(text) }));

    if (tabs.length) {
      var tab = openTab[it.id];
      if (!tab || !tabs.some(function (t) { return t[0] === tab; })) tab = tabs[0][0];
      openTab[it.id] = tab;
      var tabRow = h('div', { class: 'tabs' });
      var content = h('div', { class: 'pf-content' });
      tabs.forEach(function (t) {
        var b = h('button', { text: t[1], class: tab === t[0] ? 'on' : '' });
        b.addEventListener('click', function () {
          openTab[it.id] = t[0];
          Array.prototype.forEach.call(tabRow.children, function (x) { x.classList.remove('on'); });
          b.classList.add('on');
          RENDERERS[t[0]](content, it);
        });
        tabRow.appendChild(b);
      });
      container.appendChild(tabRow);
      container.appendChild(content);
      RENDERERS[tab](content, it);
      if (it.movies.length && !it.videos.length) {
        content.appendChild(h('div', { class: 'hint pad anim-note', html:
          '（原课件含 Director 交互式逐步作图动画：' +
          esc(it.movies.map(function (m) { return m.stem.replace(/^jieP/, ''); }).join('、')) +
          '，逐帧内容已在图中给出）' }));
      }
    } else if (it.movies.length && !it.videos.length) {
      container.appendChild(h('div', { class: 'hint pad anim-note', text: '本题仅有 Director 交互动画（未收录）。' }));
    }
    try { localStorage.setItem('resume', it.id); } catch (e) {}
  }

  /* ---------- 视图：题库首页（模块列表） ---------- */
  var searchQuery = '';
  function viewBank() {
    setChrome('bank');
    topTitle.textContent = '图学基础教程习题解答';
    clear(view);
    view.appendChild(h('div', { class: 'searchbox' }, [
      h('input', { type: 'search', placeholder: '搜索：题干关键词', value: searchQuery,
        oninput: function (e) { searchQuery = e.target.value; renderSearch(); } })
    ]));
    var box = h('div', {});
    view.appendChild(box);
    renderSearch();

    function renderSearch() {
      clear(box);
      var q = searchQuery.trim();
      if (q) { renderSearchResults(box, q); return; }

      var resume = null;
      try { resume = localStorage.getItem('resume'); } catch (e) {}
      if (resume && ITEMS[resume]) {
        var rit = ITEMS[resume];
        box.appendChild(h('div', { class: 'card tap', onclick: function () { go('#/i/' + rit.id); } }, [
          h('div', { class: 'rowtitle' }, [
            h('span', { class: 'chip', text: '继续上次' }),
            h('b', { text: labelOf(rit) })
          ]),
          h('div', { class: 'snip hint', text: snippet(rit) })
        ]));
      }

      var chunk = 8;
      for (var i = 0; i < PAGENO.length; i += chunk) {
        var slice = PAGENO.slice(i, i + chunk);
        box.appendChild(h('div', { class: 'grouph', text: 'P' + slice[0] + ' – P' + slice[slice.length - 1] }));
        var grid = h('div', { class: 'pgrid' });
        slice.forEach(function (p) {
          grid.appendChild(h('div', { class: 'pit', onclick: function () { go('#/p/' + p); } }, [
            h('b', { text: 'P' + p }),
            h('span', { text: PAGE_ITEMS[p].length + ' 题' })
          ]));
        });
        box.appendChild(grid);
      }
    }
  }

  function renderSearchResults(box, q) {
    var hits = [];
    for (var i = 0; i < ORDER.length; i++) {
      var it = ITEMS[ORDER[i]];
      if (it.text && it.text.indexOf(q) !== -1) hits.push(it);
      if (hits.length >= 80) break;
    }
    box.appendChild(h('div', { class: 'hint', text: '命中 ' + hits.length + ' 条' + (hits.length >= 80 ? '（截断）' : '') }));
    hits.forEach(function (it) {
      box.appendChild(h('div', { class: 'card tap', onclick: function () { go('#/i/' + it.id); } }, [
        h('div', { class: 'rowtitle' }, [
          h('span', { class: 'chip', text: 'P' + it.page }),
          h('b', { text: labelOf(it) })
        ]),
        h('div', { class: 'snip hint', text: snippet(it) })
      ]));
    });
  }

  /* ---------- 视图：页（题号芯片条 + 全屏单题快速切换） ---------- */
  var pageCur = {};

  function viewPage(page, curId) {
    var items = PAGE_ITEMS[page];
    if (!items) { notFound(); return; }
    setChrome('bank');
    var cur = (curId && ITEMS[curId]) ? curId : (pageCur[page] || items[0].id);
    pageCur[page] = cur;
    topTitle.textContent = '第 ' + page + ' 页 · ' + labelOf(ITEMS[cur]);

    clear(view);
    var bar = h('div', { class: 'qbar' });
    items.forEach(function (it) {
      bar.appendChild(h('button', { class: 'qchip' + (it.id === cur ? ' on' : ''), text: chipLabel(it),
        onclick: function () {
          pageCur[page] = it.id;
          history.replaceState(null, '', '#/p/' + page + '/' + it.id);
          viewPage(page, it.id);
        } }));
    });
    view.appendChild(bar);
    var body = h('div', { class: 'pf' });
    view.appendChild(body);
    renderProblem(body, ITEMS[cur]);
    window.scrollTo(0, 0);
  }

  /* ---------- 视图：全屏单题（搜索/直达，跨模块上下题） ---------- */
  function viewItem(id) {
    var it = ITEMS[id];
    if (!it) { notFound(); return; }
    setChrome('bank');
    topTitle.textContent = 'P' + it.page + ' ' + labelOf(it);
    clear(view);
    var body = h('div', { class: 'pf' });
    view.appendChild(body);
    renderProblem(body, it);

    var pos = ORDER.indexOf(id);
    var prev = pos > 0 ? ITEMS[ORDER[pos - 1]] : null;
    var next = pos < ORDER.length - 1 ? ITEMS[ORDER[pos + 1]] : null;
    var nav = h('div', { class: 'pfnav' });
    var b1 = h('button', { class: 'iconbtn', text: prev ? '‹ ' + labelOf(prev) : '‹ 上一题' });
    var b2 = h('button', { class: 'iconbtn', text: next ? labelOf(next) + ' ›' : '下一题 ›' });
    if (prev) b1.addEventListener('click', function () { go('#/i/' + prev.id); }); else b1.disabled = true;
    if (next) b2.addEventListener('click', function () { go('#/i/' + next.id); }); else b2.disabled = true;
    nav.appendChild(b1); nav.appendChild(b2);
    view.appendChild(nav);
    window.scrollTo(0, 0);
  }

  /* ---------- 视图：设置 ---------- */
  function viewSettings() {
    setChrome('settings');
    topTitle.textContent = '设置';
    clear(view);

    var ap = appearance();
    var seg = h('div', { class: 'seg wide' });
    [['auto', '跟随系统'], ['light', '浅色'], ['dark', '深色']].forEach(function (opt) {
      var b = h('button', { text: opt[1], class: ap === opt[0] ? 'on' : '' });
      b.addEventListener('click', function () {
        try { localStorage.setItem('appearance', opt[0]); } catch (e) {}
        applyAppearance();
        viewSettings();
      });
      seg.appendChild(b);
    });
    view.appendChild(h('div', { class: 'card' }, [
      h('div', { class: 'set-h', text: '外观' }), seg
    ]));

    var st = DATA.stats || {};
    view.appendChild(h('div', { class: 'card' }, [
      h('div', { class: 'set-h', text: '内容统计' }),
      h('div', { class: 'hint', html:
        '题目 <b>' + (st.items || 0) + '</b> 道 · 页码 <b>' + (st.pages || 0) + '</b> 页<br>' +
        '图片 <b>' + (st.images || 0) + '</b> 张 · 动画视频 <b>' + (st.videos || 0) + '</b> 个' })
    ]));

    view.appendChild(h('div', { class: 'card tap', onclick: function () {
      try { localStorage.removeItem('resume'); } catch (e) {}
      toast('已清除阅读记录');
    } }, [
      h('div', { class: 'set-row' }, [
        h('span', { text: '清除阅读记录' }),
        h('span', { class: 'hint', text: '清空"继续上次"位置' })
      ])
    ]));

    view.appendChild(h('div', { class: 'card tap', onclick: function () {
      CORR = {};
      saveCorr();
      toast('已重置全部校正标签');
      viewSettings();
    } }, [
      h('div', { class: 'set-row' }, [
        h('span', { text: '重置校正标签' }),
        h('span', { class: 'hint', text: '清除自定义页码/题号' })
      ])
    ]));

    view.appendChild(h('div', { class: 'card' }, [
      h('div', { class: 'set-h', text: '关于' }),
      h('div', { class: 'hint', html:
        '《图学基础教程习题解答》<br>版本 <b>v' + VERSION + '</b>（' + BUILD + '）<br>' +
        '题目按教材页码排列，结构以原版课件程序调用为准重建；<br>' +
        '教材页码/题号可在题目页长按标题校正。<br>开发者: <b>Kepler16f</b><br>完全离线可用，供个人学习。' })
    ]));
  }

  var toastTimer = null;
  function toast(msg) {
    var t = document.getElementById('toast');
    if (!t) { t = h('div', { id: 'toast' }); document.body.appendChild(t); }
    t.textContent = msg;
    t.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('show'); }, 1800);
  }

  function notFound() {
    clear(view);
    topTitle.textContent = '未找到';
    view.appendChild(h('div', { class: 'card hint', text: '内容不存在。' }));
  }

  /* ---------- 校正模式：长按标题改标签 ---------- */
  var pressTimer = null;
  document.addEventListener('pointerdown', function (e) {
    var title = e.target.closest && e.target.closest('#title');
    if (!title) return;
    pressTimer = setTimeout(function () {
      pressTimer = null;
      var m = (location.hash || '').match(/^#\/(?:i|p\/[^/]+)\/(.+)$/);
      if (!m) return;
      var it = ITEMS[decodeURIComponent(m[1])];
      if (!it) return;
      var cur = labelOf(it);
      var input = prompt('校正题目标签（页码/题号），留空恢复默认：', cur);
      if (input === null) return;
      if (input.trim() === '') delete CORR[it.id];
      else CORR[it.id] = input.trim();
      saveCorr();
      route();
      toast('标签已' + (input.trim() === '' ? '恢复默认' : '更新'));
    }, 600);
  });
  document.addEventListener('pointerup', function () { if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });
  document.addEventListener('pointercancel', function () { if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });

  /* ---------- 导航 ---------- */
  function go(hash) { location.hash = hash; }
  function parentHash() {
    var h = location.hash || '#/';
    if (/^#\/p\/\d+\/.+/.test(h)) return '#/p/' + h.split('/')[2];
    if (/^#\/p\/\d+$/.test(h)) return '#/';
    if (/^#\/i\//.test(h)) {
      var it = ITEMS[decodeURIComponent(h.split('/')[2])];
      return it ? '#/p/' + it.page : '#/';
    }
    if (h === '#/settings') return '#/';
    return null;
  }
  btnBack.addEventListener('click', function () {
    var p = parentHash();
    if (p) go(p);
  });
  function setChrome(name) {
    ['bank', 'settings'].forEach(function (t) {
      var b = document.querySelector('.tabbar .tab[data-tab="' + t + '"]');
      if (b) b.classList.toggle('on', t === name);
    });
    btnBack.hidden = !parentHash();
  }

  /* ---------- 路由 ---------- */
  function route() {
    var parts = (location.hash || '').replace(/^#\/?/, '').split('/').filter(Boolean);
    if (parts.length === 0 || parts[0] === 'bank') viewBank();
    else if (parts[0] === 'settings') viewSettings();
    else if (parts[0] === 'p' && parts[1]) viewPage(parseInt(parts[1], 10), parts[2] ? decodeURIComponent(parts[2]) : null);
    else if (parts[0] === 'i' && parts[1]) viewItem(decodeURIComponent(parts[1]));
    else viewBank();
  }
  window.addEventListener('hashchange', route);
  document.querySelectorAll('.tabbar .tab').forEach(function (b) {
    b.addEventListener('click', function () {
      go(b.getAttribute('data-tab') === 'bank' ? '#/' : '#/settings');
    });
  });

  route();

  if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  }
})();
