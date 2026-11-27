/* DEV DASHBOARD — control room landing engine.
   All vignettes are deterministic functions of loop time: no drift, no orphans. */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ============ theme switcher ============ */
  var body = document.body;
  function setTheme(name, save) {
    body.setAttribute("data-theme", name);
    $$(".swatch").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-set-theme") === name ? "true" : "false");
    });
    if (save) { try { localStorage.setItem("dd-theme", name); } catch (e) {} }
  }
  $$(".swatch").forEach(function (b) {
    b.addEventListener("click", function () { setTheme(b.getAttribute("data-set-theme"), true); });
  });
  try {
    var saved = localStorage.getItem("dd-theme");
    if (saved && $('.swatch[data-set-theme="' + saved + '"]')) setTheme(saved, false);
  } catch (e) {}

  /* ============ boot sequence ============ */
  var sysText = "SYS.STATUS: NOMINAL";
  var sysEl = $("#sysline-text");
  if (reduced) {
    body.classList.add("booted");
    sysEl.textContent = sysText;
  } else {
    setTimeout(function () { body.classList.add("booted"); }, 60);
    var si = 0;
    var typeSys = function () {
      if (si <= sysText.length) {
        sysEl.textContent = sysText.slice(0, si);
        si++;
        setTimeout(typeSys, 34);
      }
    };
    setTimeout(typeSys, 250);
  }

  /* ============ scroll reveals ============ */
  var revealEls = $$("[data-reveal]");
  if (reduced || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  /* ============ HERO MOCK ============ */
  var SVCS = {
    "api-server":   { cpu: 1.4, mem: 52,  jitter: 0.9,  age: 842 },
    "postgres":     { cpu: 2.6, mem: 63,  jitter: 1.4,  age: 707 },
    "web-frontend": { cpu: 4.2, mem: 118, jitter: 2.2,  age: 571 },
    "worker":       { cpu: 7.5, mem: 41,  jitter: 3.4,  age: 728 }
  };
  var svcEls = {};
  Object.keys(SVCS).forEach(function (name) {
    var el = $('.svc[data-svc="' + name + '"]');
    if (!el) return;
    svcEls[name] = {
      el: el,
      dot: $(".svc-dot", el),
      state: $(".svc-state", el),
      cpu: $(".svc-cpu", el),
      mem: $(".svc-mem", el),
      up: $(".svc-up", el),
      pid: $(".svc-pid", el),
      spark: $("polyline", el),
      backoffBar: $(".svc-backoff i", el),
      stateDefault: $(".svc-state", el).textContent,
      data: [],
      cpuNow: SVCS[name].cpu,
      memNow: SVCS[name].mem,
      crashed: false,
      flick: false
    };
    for (var i = 0; i < 22; i++) svcEls[name].data.push(SVCS[name].cpu);
  });

  function drawSpark(s) {
    var d = s.data, n = d.length, max = 12;
    var pts = [];
    for (var i = 0; i < n; i++) {
      var x = (i / (n - 1)) * 62 + 1;
      var y = 18 - Math.min(d[i] / max, 1) * 16;
      pts.push(x.toFixed(1) + "," + y.toFixed(1));
    }
    s.spark.setAttribute("points", pts.join(" "));
  }

  function fmtAge(sec) {
    if (sec < 0) sec = 0;
    var m = Math.floor(sec / 60), s = Math.floor(sec % 60);
    return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
  }

  /* metrics ticking */
  var metricsTimer = null;
  function tickMetrics() {
    Object.keys(svcEls).forEach(function (name) {
      var s = svcEls[name], base = SVCS[name];
      if (s.crashed) {
        s.cpuNow = 0; s.memNow = Math.max(0, s.memNow - 8);
      } else {
        s.cpuNow += (Math.random() - 0.5) * base.jitter;
        s.cpuNow = Math.max(0.2, Math.min(base.cpu * 2.4, s.cpuNow));
        s.cpuNow += (base.cpu - s.cpuNow) * 0.12; /* mean reversion */
        s.memNow += (Math.random() - 0.48) * 1.6;
        s.memNow = Math.max(base.mem * 0.85, Math.min(base.mem * 1.25, s.memNow));
      }
      s.cpu.textContent = s.cpuNow.toFixed(1) + "%";
      s.mem.textContent = Math.round(s.memNow) + " MB";
      s.data.push(s.cpuNow);
      if (s.data.length > 22) s.data.shift();
      drawSpark(s);
    });
  }
  Object.keys(svcEls).forEach(function (n) { drawSpark(svcEls[n]); });

  /* log stream */
  var logsEl = $("#insp-logs");
  var LOG_POOL = [
    ["api", "GET /api/state 200 · 2ms"],
    ["web", "vite hmr update /src/App.tsx"],
    ["pg", "checkpoint complete · 14 buffers"],
    ["worker", "job #412 finished in 0.8s"],
    ["api", "POST /api/services 201 · 5ms"],
    ["web", "compiled in 212ms"],
    ["pg", "connection received 127.0.0.1:51922"],
    ["worker", "queue depth 0 · idle"],
    ["api", "GET /api/ports 200 · 3ms"],
    ["web", "hmr client connected"],
    ["pg", "autovacuum: worker analyzing"],
    ["worker", "job #413 picked up"]
  ];
  function ts() {
    var d = new Date();
    var p = function (n) { return (n < 10 ? "0" : "") + n; };
    return p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
  }
  function pushLog(html, cls) {
    if (!logsEl) return;
    var div = document.createElement("div");
    div.className = "lg-line" + (cls ? " " + cls : "");
    div.innerHTML = '<span class="lg-t">' + ts() + "</span> " + html;
    logsEl.appendChild(div);
    while (logsEl.children.length > 24) logsEl.removeChild(logsEl.firstChild);
  }
  function tickLog() {
    var l = LOG_POOL[Math.floor(Math.random() * LOG_POOL.length)];
    pushLog('<span class="lg-ok">[' + l[0] + "]</span> " + l[1]);
  }

  /* toasts */
  var toastsEl = $("#mock-toasts");
  function makeToast() {
    var t = document.createElement("div");
    t.className = "toast";
    t.innerHTML = '<span class="t-dot"></span><span class="t-msg"></span>';
    toastsEl.appendChild(t);
    return t;
  }
  var toastCrash = toastsEl ? makeToast() : null;
  var toastOk = toastsEl ? makeToast() : null;
  if (toastOk) toastOk.classList.add("toast-ok");

  /* scenario state — deterministic in loop time */
  var LOOP = 14000, CRASH_AT = 4.0;
  var lastIter = -1;
  var msState = $("#msb-state"), msCount = $("#ms-count");
  var baseAges = {};
  Object.keys(SVCS).forEach(function (n) { baseAges[n] = SVCS[n].age; });
  var t0 = performance.now();

  function mockFrame(now) {
    var elapsed = (now - t0) / 1000;
    var iter = Math.floor(elapsed / (LOOP / 1000));
    var phase = elapsed % (LOOP / 1000); /* seconds into loop */
    var target = iter % 2 === 0 ? "worker" : "postgres";
    var backoff = iter % 2 === 0 ? 2 : 5;
    var restart = CRASH_AT + backoff;

    if (iter !== lastIter) {
      lastIter = iter;
      baseAges[target] = 0 - restart; /* uptime restarts at restart time */
    }

    Object.keys(svcEls).forEach(function (name) {
      var s = svcEls[name];
      var isTarget = name === target;
      var crashed = isTarget && phase >= CRASH_AT && phase < restart;
      var flickering = isTarget && phase >= restart && phase < restart + 0.7;

      if (crashed !== s.crashed) {
        s.crashed = crashed;
        s.el.classList.toggle("crashed", crashed);
        s.state.textContent = crashed ? "crashed · exit 1" : s.stateDefault;
        if (!crashed && flickering) {
          pushLog('<span class="lg-ok">[dash]</span> ' + name + " restarted · pid " + (20000 + Math.floor(Math.random() * 9000)), "lg-ok");
        }
        if (crashed) {
          pushLog('<span class="lg-err">[' + name + "]</span> FATAL uncaught exception · exit 1", "lg-err");
        }
      }
      if (flickering !== s.flick) {
        s.flick = flickering;
        s.el.classList.toggle("flicker", flickering);
      }

      /* backoff strip */
      if (crashed) {
        var p = Math.min((phase - CRASH_AT) / backoff, 1);
        s.backoffBar.style.transform = "scaleX(" + p.toFixed(3) + ")";
      } else {
        s.backoffBar.style.transform = "scaleX(0)";
      }

      /* uptime */
      var age = baseAges[name] + phase + Math.floor(elapsed / (LOOP / 1000)) * 0;
      if (!isTarget) age = baseAges[name] + elapsed;
      if (crashed) {
        if (s.up.textContent !== "--:--") s.up.textContent = "--:--";
      } else {
        var a = isTarget ? (phase < CRASH_AT ? SVCS[name].age + phase : phase - restart) : SVCS[name].age + elapsed;
        s.up.textContent = fmtAge(Math.max(0, a));
      }
    });

    /* toasts */
    if (toastCrash) {
      var showC = phase >= CRASH_AT + 0.15 && phase < CRASH_AT + 2.9;
      toastCrash.classList.toggle("show", showC);
      if (showC) $(".t-msg", toastCrash).textContent = target + " crashed: restarting in " + backoff + "s";
      var showO = phase >= restart + 0.1 && phase < restart + 2.8;
      toastOk.classList.toggle("show", showO);
      if (showO) $(".t-msg", toastOk).textContent = target + " restarted · uptime reset";
    }

    /* statusbar */
    var anyDown = phase >= CRASH_AT && phase < restart;
    var txt = anyDown ? "3 UP · 1 DOWN" : "4 UP · 0 DOWN";
    if (msState && msState.textContent !== txt) {
      msState.textContent = txt;
      msState.style.color = anyDown ? "var(--err)" : "var(--ok)";
    }
    if (msCount) {
      var c = anyDown ? "3/4" : "4/4";
      if (msCount.textContent !== c) msCount.textContent = c;
    }
  }

  /* ============ backoff vignette ============ */
  var boStage = $("#bo-stage");
  var boPlayhead = $("#bo-playhead");
  var boTicks = $$(".bo-tick");
  var boPulses = $$(".bo-pulse");
  var boSegs = $$(".bo-seglabel");
  var boCircuit = $("#bo-circuit");
  var boReset = $("#bo-reset");
  var BO_LOOP = 12, BO_SWEEP = 9.5;
  var CX = [0.02, 0.07, 0.195, 0.445, 0.945];
  var BOF = [0.05, 0.125, 0.25, 0.5]; /* backoff as fraction of 40s window */
  var boW = 0;
  function measureBo() { if (boStage) boW = boStage.clientWidth; }
  measureBo();
  window.addEventListener("resize", measureBo);

  /* reposition pulses onto their crash ticks */
  boPulses.forEach(function (p, i) { p.style.setProperty("--x", (CX[i] * 100) + "%"); });

  var boState = { hits: [], pulses: [], circuit: false, reset: false, segs: [] };

  function backoffFrame(now) {
    if (!boStage) return;
    var t = (now / 1000) % BO_LOOP;
    var prog = Math.min(t / BO_SWEEP, 1); /* saturates at 1 after the sweep */
    var CLEAR = 11.2; /* manual-start reset moment */

    boPlayhead.style.transform = "translateX(" + (Math.min(t / BO_SWEEP, 1) * boW).toFixed(1) + "px)";
    boPlayhead.style.opacity = t < 10.6 ? "1" : "0";

    boTicks.forEach(function (tick, i) {
      var hit = t < CLEAR && prog >= CX[i];
      if (boState.hits[i] !== hit) {
        boState.hits[i] = hit;
        tick.classList.toggle("hit", hit);
      }
    });
    boPulses.forEach(function (p, i) {
      var at = CX[i] + BOF[i] * 0.8;
      var fire = t < CLEAR && prog >= at && prog < at + 0.09 && t < BO_SWEEP;
      if (fire && !boState.pulses[i]) {
        p.classList.remove("fire");
        void p.offsetWidth; /* restart the css animation */
        p.classList.add("fire");
      }
      boState.pulses[i] = fire;
    });
    boSegs.forEach(function (seg, i) {
      var lit = t < BO_SWEEP && prog >= CX[i] && prog < CX[i + 1];
      if (boState.segs[i] !== lit) {
        boState.segs[i] = lit;
        seg.classList.toggle("lit", lit);
      }
    });
    /* circuit opens when the playhead passes the 5th crash, holds, cleared by manual start */
    var open = t >= 9.36 && t < CLEAR;
    if (boState.circuit !== open) {
      boState.circuit = open;
      boCircuit.classList.toggle("open", open);
    }
    var rpulse = t >= 10.5 && t < CLEAR;
    if (boState.reset !== rpulse) {
      boState.reset = rpulse;
      boReset.classList.toggle("pulse", rpulse);
    }
    /* loop-boundary fade masks the reset */
    var fade = t > BO_LOOP - 0.7 ? Math.max(0, 1 - (t - (BO_LOOP - 0.7)) / 0.35) : t < 0.35 ? t / 0.35 : 1;
    boStage.style.opacity = Math.min(1, Math.max(0.05, fade)).toFixed(2);
  }

  /* ============ ports vignette ============ */
  var portRows = $$(".port-row");
  var portsStage = $("#ports-stage");
  var PT_LOOP = 11;
  var portState = [];
  function portsFrame(now) {
    if (!portsStage) return;
    var t = (now / 1000) % PT_LOOP;
    portRows.forEach(function (row, i) {
      var appear = 0.6 + i * 1.5;
      var on = t >= appear;
      var locked = t >= appear + 0.75;
      var key = i * 4;
      if (portState[key] !== on) { portState[key] = on; row.classList.toggle("on", on); }
      if (portState[key + 1] !== locked) { portState[key + 1] = locked; row.classList.toggle("locked", locked); }
    });
    var fade = t > PT_LOOP - 0.8 ? Math.max(0.05, 1 - (t - (PT_LOOP - 0.8)) / 0.4) : t < 0.4 ? t / 0.4 : 1;
    portsStage.style.opacity = Math.min(1, fade).toFixed(2);
    if (t > PT_LOOP - 0.4 && portState[0]) {
      portRows.forEach(function (row, i) {
        row.classList.remove("on", "locked");
        portState[i * 4] = false; portState[i * 4 + 1] = false;
      });
    }
  }

  /* ============ events vignette ============ */
  var evRows = $$(".ev-row");
  var evStage = $("#ev-stage");
  var EV_LOOP = 10;
  var evState = [];
  function eventsFrame(now) {
    if (!evStage) return;
    var t = (now / 1000) % EV_LOOP;
    evRows.forEach(function (row, i) {
      var on = t >= 0.5 + i * 1.05;
      if (evState[i] !== on) { evState[i] = on; row.classList.toggle("on", on); }
    });
    var fade = t > EV_LOOP - 0.8 ? Math.max(0.05, 1 - (t - (EV_LOOP - 0.8)) / 0.4) : t < 0.4 ? t / 0.4 : 1;
    evStage.style.opacity = Math.min(1, fade).toFixed(2);
    if (t > EV_LOOP - 0.4 && evState[0]) {
      evRows.forEach(function (row, i) { row.classList.remove("on"); evState[i] = false; });
    }
  }

  /* ============ mcp vignette ============ */
  var REQ = '{"method":"tools/call","params":{"name":"service_state","arguments":{"name":"postgres"}}}';
  var RESP = '{\n  "name": "postgres",  "state": "running",  "pid": 4104,\n  "cpu": 1.8,  "mem_mb": 62,  "ports": [5432],\n  "uptime_s": 4210,  "restarts": 0\n}';
  var MCP_LOOP = 13;
  var mcpTyped = $("#mcp-typed"), mcpResp = $("#mcp-resp");
  var mcpLastN = -1, mcpLastR = -1;
  function mcpFrame(now) {
    if (!mcpTyped) return;
    var t = (now / 1000) % MCP_LOOP;
    var n = 0, r = 0;
    if (t >= 0.5) n = Math.min(REQ.length, Math.floor((t - 0.5) * 38));
    if (t >= 4.2) r = Math.min(RESP.length, Math.floor((t - 4.2) * 90));
    if (t > MCP_LOOP - 0.6) { n = 0; r = 0; }
    if (n !== mcpLastN) { mcpLastN = n; mcpTyped.textContent = REQ.slice(0, n); }
    if (r !== mcpLastR) { mcpLastR = r; mcpResp.textContent = RESP.slice(0, r); }
  }

  /* ============ master loop ============ */
  var lastMetrics = 0, lastLog = 0;
  function frame(now) {
    mockFrame(now);
    backoffFrame(now);
    portsFrame(now);
    eventsFrame(now);
    mcpFrame(now);
    if (now - lastMetrics > 700) { lastMetrics = now; tickMetrics(); }
    if (now - lastLog > 850) { lastLog = now; tickLog(); }
    requestAnimationFrame(frame);
  }

  if (reduced) {
    /* static nominal states — everything readable, nothing moves */
    Object.keys(svcEls).forEach(function (n) { drawSpark(svcEls[n]); });
    tickMetrics();
    for (var li = 0; li < 8; li++) tickLog();
    boTicks.forEach(function (t) { t.classList.add("hit"); });
    boSegs.forEach(function (s) { s.classList.add("lit"); });
    boCircuit.classList.add("open");
    boReset.classList.add("pulse");
    portRows.forEach(function (r) { r.classList.add("on", "locked"); });
    evRows.forEach(function (r) { r.classList.add("on"); });
    if (mcpTyped) { mcpTyped.textContent = REQ; mcpResp.textContent = RESP; }
  } else {
    requestAnimationFrame(frame);
  }

  /* ============ env reveal ============ */
  var eye = $("#env-eye"), secret = $("#env-secret");
  if (eye && secret) {
    eye.addEventListener("click", function () {
      var open = eye.getAttribute("aria-pressed") === "true";
      eye.setAttribute("aria-pressed", open ? "false" : "true");
      eye.setAttribute("aria-label", open ? "Reveal secret" : "Hide secret");
      secret.textContent = open ? "••••••••••" : "dtok_9f3ac71b";
    });
  }

  /* ============ download: live release meta + magnetic hover ============ */
  var dlMeta = $("#dl-version");
  if (dlMeta && window.fetch) {
    fetch("https://api.github.com/repos/dvinerlove/dev-dashboard/releases/latest")
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (j) {
        var d = new Date(j.published_at);
        var date = isNaN(d) ? "" : d.toISOString().slice(0, 10);
        dlMeta.textContent = (j.tag_name ? j.tag_name.toUpperCase() : "LATEST") + " · PUBLISHED " + date + " · GITHUB RELEASES";
      })
      .catch(function () { dlMeta.textContent = "LATEST RELEASE · GITHUB"; });
  }

  var dlBtn = $("#dl-btn");
  if (dlBtn && !reduced && window.matchMedia("(pointer: fine)").matches) {
    var raf = null;
    dlBtn.addEventListener("mousemove", function (e) {
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = null;
        var r = dlBtn.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) / r.width;
        var dy = (e.clientY - (r.top + r.height / 2)) / r.height;
        dlBtn.style.transform = "translate(" + (dx * 7).toFixed(1) + "px," + (dy * 5).toFixed(1) + "px)";
      });
    });
    dlBtn.addEventListener("mouseleave", function () {
      dlBtn.style.transform = "";
    });
  }
})();
