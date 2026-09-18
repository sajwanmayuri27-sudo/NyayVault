/* =========================================================
   NyayVault — dashboard controller
   ========================================================= */

const ICONS = {
  overview: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>`,
  cases: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/></svg>`,
  upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 16V4M12 4l-4 4M12 4l4 4"/><path d="M4 16v3a2 2 0 002 2h12a2 2 0 002-2v-3"/></svg>`,
  redaction: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="16" rx="1"/><rect x="6" y="8" width="8" height="2.4" fill="currentColor" stroke="none"/><rect x="6" y="13" width="12" height="2.4" fill="currentColor" stroke="none"/></svg>`,
  audio: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v4"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>`,
  verify: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z"/><path d="M9 12l2 2 4-4"/></svg>`,
  exif: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="1"/><circle cx="12" cy="12" r="3.2"/></svg>`,
  report: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/><path d="M9 13h6M9 17h6"/></svg>`,
  docket: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 3h10a1 1 0 011 1v16l-3-2-3 2-3-2-3 2V4a1 1 0 011-1z"/></svg>`,
  timeline: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4v16h16"/><circle cx="8" cy="14" r="1.6" fill="currentColor" stroke="none"/><circle cx="13" cy="9" r="1.6" fill="currentColor" stroke="none"/><circle cx="18" cy="12" r="1.6" fill="currentColor" stroke="none"/></svg>`,
  courtroom: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 21h16M6 21V10M18 21V10M4 10l8-6 8 6M9 21v-6h6v6"/></svg>`,
  users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="9" cy="8" r="3.2"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><circle cx="18" cy="8.6" r="2.4"/><path d="M16 14.2c2.6.4 4.3 2.3 4.3 5.3"/></svg>`,
  auditlogs: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16M4 12h16M4 18h10"/><circle cx="20" cy="18" r="1.6" fill="currentColor" stroke="none"/></svg>`,
};

const NAV_CONFIG = {
  io: ["overview", "cases", "upload", "redaction", "audio", "search"],
  forensic: ["overview", "cases", "verify", "exif", "report"],
  judge: ["overview", "docket", "timeline", "courtroom"],
  admin: ["overview", "users", "auditlogs"],
};

const ROLE_META = {
  io: { labelKey: "role_io", descKey: "work_io", initials: "IO" },
  forensic: { labelKey: "role_forensic", descKey: "work_forensic", initials: "FS" },
  judge: { labelKey: "role_judge", descKey: "work_judge", initials: "JC" },
  admin: { labelKey: "role_admin", descKey: "work_admin", initials: "AD" },
};

const state = {
  role: "io",
  user: "officer.sharma",
  section: "overview",
  caseId: null,
  docId: null,
};

/* ---------------- boot ---------------- */
function fmtDate(value){
  if(!value) return "—";
  try { return new Date(value).toLocaleString(); } catch(_) { return value; }
}
function mapDoc(d){
  return { id:d.id, name:d.name, type:d.type, uploader:"Evidence User", time:fmtDate(d.uploaded_at), hash:d.hash_display || (d.hash_sha256||"").slice(0,12), status:d.status, exif:d.exif || {device:"—",gps:"—",imei:"—",created:"—"} };
}
async function loadLiveData(){
  const basic = await NV_API.cases();
  const details = await Promise.all(basic.map(c=>NV_API.caseDetail(c.id)));
  NV_CASES = details.map(c=>({id:c.id, number:c.number, title:c.title, status:c.status, docs:(c.documents||[]).map(mapDoc)}));
  if(NV_CASES.length) state.caseId = NV_CASES[0].id;
  if(state.role === "admin"){
    const [users, logs] = await Promise.all([NV_API.users(), NV_API.audit()]);
    const userMap = Object.fromEntries(users.map(u=>[u.id,u.full_name]));
    NV_USERS = users.map(u=>({id:u.id,name:u.full_name,role:({io:"Investigating Officer",forensic:"Forensic Specialist",judge:"Judge / Court",admin:"Administrator"})[u.role]||u.role,badge:u.badge_id,status:u.status}));
    NV_AUDIT_LOG = logs.map(l=>({time:fmtDate(l.timestamp),user:userMap[l.user_id]||"System",role:l.role||"",ip:l.ip_address||"—",action:l.action,detail:l.detail}));
  }
}

document.addEventListener("DOMContentLoaded", async ()=>{
  const role = localStorage.getItem("nv_role");
  const user = localStorage.getItem("nv_user");
  const token = localStorage.getItem("nv_token");
  if(!role || !user || !token){ window.location.href = "/login.html"; return; }
  state.role = role; state.user = user;
  try{
    const me = await NV_API.me();
    state.role = me.role; state.user = me.username;
    localStorage.setItem("nv_role", me.role);
    await loadLiveData();
  }catch(err){ alert(err.message); return; }

  document.getElementById("logoutBtn").addEventListener("click", async ()=>{
    await NV_API.logout();
    ["nv_token","nv_role","nv_user","nv_full_name"].forEach(k=>localStorage.removeItem(k));
    window.location.href = "/login.html";
  });
  document.querySelectorAll(".lang-switch button").forEach(btn=>btn.addEventListener("click", ()=>setTimeout(renderAll,0)));
  document.getElementById("modalBackdrop").addEventListener("click", e=>{ if(e.target.id === "modalBackdrop") closeModal(); });
  renderAll();
});

function renderAll(){
  renderTopbarUser();
  renderSidebar();
  renderSection(state.section);
}

function renderTopbarUser(){
  const meta = ROLE_META[state.role];
  document.getElementById("userAvatar").textContent = meta.initials;
  document.getElementById("userName").textContent = state.user;
  document.getElementById("userRoleLabel").textContent = t(meta.labelKey);
}

function renderSidebar(){
  const meta = ROLE_META[state.role];
  document.getElementById("roleCardIcon").outerHTML = ICONS[NAV_CONFIG[state.role][0]].replace("<svg ", '<svg id="roleCardIcon" ');
  document.getElementById("roleCardTitle").textContent = t(meta.labelKey);
  document.getElementById("roleCardDesc").textContent = t(meta.descKey);

  const list = document.getElementById("navList");
  list.innerHTML = NAV_CONFIG[state.role].map(id=>`
    <li class="nav-item ${state.section===id?'active':''}" data-nav="${id}">
      ${ICONS[id]}<span>${t("nav_"+id)}</span>
    </li>
  `).join("");
  list.querySelectorAll(".nav-item").forEach(el=>{
    el.addEventListener("click", ()=>{
      state.section = el.getAttribute("data-nav");
      renderSidebar();
      renderSection(state.section);
    });
  });
}

function renderSection(id){
  const main = document.getElementById("mainContent");
  main.innerHTML = SECTIONS[id] ? SECTIONS[id]() : "";
  if(HANDLERS[id]) HANDLERS[id]();
}

/* ---------------- small helpers ---------------- */
function findCase(id){ return NV_CASES.find(c=>c.id===id); }
function findDoc(caseObj, docId){ return caseObj.docs.find(d=>d.id===docId); }

function statusBadgeClass(status){
  return status==="active" ? "active" : status==="court" ? "court" : "closed";
}
function statusBadgeLabel(status){
  return status==="active" ? t("case_active") : status==="court" ? t("case_in_court") : t("case_closed");
}

function toast(msg, isError){
  const stack = document.getElementById("toastStack");
  const el = document.createElement("div");
  el.className = "toast" + (isError ? " error" : "");
  el.textContent = msg;
  stack.appendChild(el);
  setTimeout(()=>{ el.remove(); }, 3600);
}

function openModal(html){
  document.getElementById("modalBody").innerHTML = `<button class="modal-close" onclick="closeModal()">&times;</button>${html}`;
  document.getElementById("modalBackdrop").classList.remove("hidden");
}
function closeModal(){
  document.getElementById("modalBackdrop").classList.add("hidden");
}

async function hashText(str){
  try{
    const enc = new TextEncoder().encode(str);
    const buf = await crypto.subtle.digest("SHA-256", enc);
    return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,"0")).join("");
  }catch(e){
    // fallback pseudo-hash for restrictive contexts (e.g. plain file:// in some browsers)
    let h = 0;
    for(let i=0;i<str.length;i++){ h = (Math.imul(31,h) + str.charCodeAt(i)) | 0; }
    const seed = Math.abs(h).toString(16).padStart(8,"0");
    return (seed+seed+seed+seed).slice(0,64);
  }
}

/* =================================================================
   SECTION RENDERERS
   ================================================================= */
const SECTIONS = {

  overview(){
    const totalDocs = NV_CASES.reduce((n,c)=>n+c.docs.length,0);
    const pending = NV_CASES.reduce((n,c)=>n+c.docs.filter(d=>d.status!=="verified").length,0);
    const activeCases = NV_CASES.filter(c=>c.status==="active").length;

    return `
      <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-value">${activeCases}</div><div class="kpi-label">${t("kpi_active_cases")}</div></div>
        <div class="kpi-card"><div class="kpi-value">${pending}</div><div class="kpi-label">${t("kpi_pending_verify")}</div></div>
        <div class="kpi-card"><div class="kpi-value">${totalDocs}</div><div class="kpi-label">${t("kpi_evidence_items")}</div></div>
        <div class="kpi-card"><div class="kpi-value">${NV_AUDIT_LOG.length}</div><div class="kpi-label">${t("kpi_audit_events")}</div></div>
      </div>

      <div class="two-col">
        <div class="panel">
          <div class="panel-head"><h3>${t("nav_cases")}</h3></div>
          ${NV_CASES.map(c=>`
            <div class="case-list-item" data-case="${c.id}">
              <span class="case-num">${c.number}</span>
              <div class="case-title">${c.title}</div>
              <div class="case-meta">
                <span class="status-badge ${statusBadgeClass(c.status)}">${statusBadgeLabel(c.status)}</span>
                <span>${c.docs.length} ${t("docs_count")}</span>
              </div>
            </div>
          `).join("")}
        </div>

        <div class="panel">
          <div class="panel-head"><h3>${t("section_auditlogs")}</h3></div>
          <div class="timeline">
            ${NV_AUDIT_LOG.slice(0,5).map(logItemHTML).join("")}
          </div>
        </div>
      </div>
    `;
  },

  cases(){
    return caseWorkspaceHTML({ showActions: state.role !== "judge", readOnly: false });
  },

  docket(){
    return caseWorkspaceHTML({ showActions: false, readOnly: true });
  },

  upload(){
    return `
      <div class="panel">
        <div class="panel-head">
          <div><h3>${t("section_upload")}</h3><p>${t("section_upload_desc")}</p></div>
        </div>
        <div class="dropzone" id="dropzone">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 16V4M12 4l-4 4M12 4l4 4"/><path d="M4 16v3a2 2 0 002 2h12a2 2 0 002-2v-3"/></svg>
          <div>${t("drop_hint")}</div>
          <input type="file" id="fileInput" style="display:none">
        </div>
        <div class="hash-result" id="hashResult">
          <div class="label">${t("hash_generated")} — SHA-256</div>
          <div class="hash-val" id="hashVal"></div>
        </div>
      </div>
    `;
  },

  redaction(){
    return `
      <div class="panel">
        <div class="panel-head"><div><h3>${t("section_redaction")}</h3></div></div>
        <div class="feature-split">
          <div class="mini-card">
            <h4>${t("redaction_pdf")}</h4>
            <p>${t("redaction_pdf_desc")}</p>
            <button class="btn-ghost run-redaction" data-target="pdf">${t("btn_run_redaction")}</button>
            <div class="hash-result" id="redact-pdf-result" style="margin-top:14px;">
              <div class="label">Aadhaar •• •••• 8241 → <b>████ •••• ████</b></div>
              <div class="label">Phone +91 98••••••12 → <b>+91 ██████████</b></div>
            </div>
          </div>
          <div class="mini-card">
            <h4>${t("redaction_cctv")}</h4>
            <p>${t("redaction_cctv_desc")}</p>
            <button class="btn-ghost run-redaction" data-target="cctv">${t("btn_run_redaction")}</button>
            <div class="hash-result" id="redact-cctv-result" style="margin-top:14px;">
              <div class="label">2 faces blurred · 1 licence plate blurred (frame 00:14–00:52)</div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  audio(){
    return `
      <div class="panel">
        <div class="panel-head"><div><h3>${t("section_audio")}</h3><p>${t("section_audio_desc")}</p></div></div>
        <button class="btn-primary" id="transcribeBtn">${t("btn_transcribe")}</button>
        <div id="transcriptBox" style="margin-top:18px;"></div>
      </div>
    `;
  },

  search(){
    return `
      <div class="panel">
        <div class="panel-head"><div><h3>${t("section_search")}</h3><p>${t("section_search_desc")}</p></div></div>
        <div class="field">
          <div class="input-shell">
            ${ICONS.search}
            <input type="text" id="caseSearchInput" data-i18n-ph="search_case_ph" placeholder="${t('search_case_ph')}">
          </div>
        </div>
        <div class="search-results" id="caseSearchResults"></div>
      </div>
    `;
  },

  verify(){
    const c = findCase(state.caseId);
    const doc = state.docId ? findDoc(c, state.docId) : c.docs[0];
    return `
      <div class="case-content-grid panel" style="padding:0;">
        <div class="case-list-col">${caseListHTML(state.caseId)}</div>
        <div class="doc-vault-col" style="padding:20px 20px 20px 22px;">
          <div class="panel-head"><div><h3>${t("section_verify")}</h3><p>${t("section_verify_desc")}</p></div></div>
          ${docListHTML(c, doc ? doc.id : null, { showActions:false, showStatus:true, selectable:true })}
          <button class="btn-primary" id="verifyBtn" style="margin-top:16px;">${t("btn_verify")}</button>
          <div class="hash-result" id="verifyResult" style="margin-top:16px;"></div>
        </div>
      </div>
    `;
  },

  exif(){
    const c = findCase(state.caseId);
    const doc = state.docId ? findDoc(c, state.docId) : c.docs[0];
    return `
      <div class="case-content-grid panel" style="padding:0;">
        <div class="case-list-col">${caseListHTML(state.caseId)}</div>
        <div class="doc-vault-col" style="padding:20px 20px 20px 22px;">
          <div class="panel-head"><div><h3>${t("section_exif")}</h3><p>${t("section_exif_desc")}</p></div></div>
          ${docListHTML(c, doc ? doc.id : null, { showActions:false, showStatus:false, selectable:true })}
          ${doc ? `
            <table class="exif-table" style="margin-top:18px;">
              <tr><td>${t("exif_device")}</td><td>${doc.exif.device}</td></tr>
              <tr><td>${t("exif_gps")}</td><td>${doc.exif.gps}</td></tr>
              <tr><td>${t("exif_imei")}</td><td>${doc.exif.imei}</td></tr>
              <tr><td>${t("exif_created")}</td><td>${doc.exif.created}</td></tr>
            </table>
          ` : ""}
        </div>
      </div>
    `;
  },

  report(){
    return `
      <div class="panel">
        <div class="panel-head"><div><h3>${t("section_report")}</h3><p>${t("section_report_desc")}</p></div></div>
        ${caseListHTML(state.caseId)}
        <button class="btn-primary" id="generateReportBtn" style="margin-top:16px;">${t("btn_generate_report")}</button>
      </div>
    `;
  },

  timeline(){
    return `
      <div class="panel">
        <div class="panel-head"><div><h3>${t("section_timeline")}</h3><p>${t("section_timeline_desc")}</p></div></div>
        ${caseListHTML(state.caseId)}
        <div class="timeline" style="margin-top:20px;">
          ${NV_AUDIT_LOG.map(logItemHTML).join("")}
        </div>
      </div>
    `;
  },

  courtroom(){
    const c = findCase(state.caseId);
    const doc = c.docs[0];
    return `
      <div class="panel">
        <div class="panel-head"><div><h3>${t("section_courtroom")}</h3><p>${t("section_courtroom_desc")}</p></div></div>
        ${caseListHTML(state.caseId)}
        <button class="btn-primary" id="presentBtn" style="margin-top:16px;">${t("btn_present")}</button>
      </div>
    `;
  },

  users(){
    return `
      <div class="panel">
        <div class="panel-head">
          <div><h3>${t("section_users")}</h3><p>${t("section_users_desc")}</p></div>
          <button class="btn-primary" id="addUserBtn">${t("btn_add_user")}</button>
        </div>
        <table class="data-table">
          <thead><tr><th>${t("th_name")}</th><th>${t("th_role")}</th><th>${t("th_badge")}</th><th>${t("th_status")}</th><th>${t("th_action")}</th></tr></thead>
          <tbody id="usersTableBody">
            ${NV_USERS.map((u,i)=>userRowHTML(u,i)).join("")}
          </tbody>
        </table>
      </div>
    `;
  },

  auditlogs(){
    return `
      <div class="panel">
        <div class="panel-head"><div><h3>${t("section_auditlogs")}</h3><p>${t("section_auditlogs_desc")}</p></div></div>
        <table class="data-table">
          <thead><tr><th>${t("th_time")}</th><th>${t("th_user")}</th><th>${t("th_ip")}</th><th>${t("th_event")}</th></tr></thead>
          <tbody id="auditTableBody">
            ${NV_AUDIT_LOG.map(auditRowHTML).join("")}
          </tbody>
        </table>
      </div>
    `;
  },
};

/* ---------------- shared HTML fragments ---------------- */

function caseWorkspaceHTML({ showActions, readOnly }){
  const c = findCase(state.caseId);
  return `
    <div class="case-content-grid panel" style="padding:0;">
      <div class="case-list-col">${caseListHTML(state.caseId)}</div>
      <div class="doc-vault-col" style="padding:20px 20px 20px 22px;">
        <div class="panel-head">
          <div><h3>${c.number} — ${c.title}</h3></div>
          ${(!readOnly && state.role==="io") ? `<button class="btn-ghost" id="uploadEvidenceBtn">${t("btn_upload")}</button>` : ""}
        </div>
        ${docListHTML(c, null, { showActions, showStatus:true, selectable:false, readOnly })}
      </div>
    </div>
  `;
}

function caseListHTML(activeCaseId){
  return `
    <div>
      ${NV_CASES.map(c=>`
        <div class="case-list-item ${c.id===activeCaseId?'active':''}" data-case="${c.id}">
          <span class="case-num">${c.number}</span>
          <div class="case-title">${c.title}</div>
          <div class="case-meta">
            <span class="status-badge ${statusBadgeClass(c.status)}">${statusBadgeLabel(c.status)}</span>
            <span>${c.docs.length} ${t("docs_count")}</span>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function docListHTML(caseObj, activeDocId, opts){
  opts = opts || {};
  return caseObj.docs.map(d=>`
    <div class="doc-card ${opts.selectable ? 'selectable' : ''}" data-doc="${d.id}" style="${opts.selectable ? 'cursor:pointer;' + (d.id===activeDocId ? 'border-color:var(--gold);' : '') : ''}">
      <div>
        <span class="doc-type-badge">${d.type}</span>
        <div class="doc-name" style="display:inline;">${d.name}</div>
        <div class="doc-meta">${d.uploader} · ${d.time} · <span class="hash-snip">${d.hash}</span></div>
      </div>
      <div style="display:flex; align-items:center; gap:14px;">
        ${opts.showStatus ? `<span class="doc-status ${d.status==='verified' ? 'verified' : 'tampered'}"><span class="dot"></span>${d.status==='verified' ? t('verify_ok') : t('verify_bad')}</span>` : ""}
        ${opts.showActions ? `
          <div class="doc-actions">
            <button class="btn-ghost preview-doc" data-doc="${d.id}">${t("nav_docket")}</button>
          </div>
        ` : ""}
      </div>
    </div>
  `).join("");
}

function logItemHTML(log){
  return `
    <div class="timeline-item">
      <div class="ti-top">
        <span class="ti-time">${log.time}</span>
        <span class="action-badge ${log.action}">${t("action_"+log.action)}</span>
        <span class="role-pill">${log.user}</span>
      </div>
      <div class="ti-detail">${log.detail}</div>
    </div>
  `;
}

function userRowHTML(u, i){
  return `
    <tr>
      <td>${u.name}</td>
      <td>${u.role}</td>
      <td class="hash-snip" style="display:inline-block; font-family: var(--font-mono);">${u.badge}</td>
      <td><span class="status-badge ${u.status==='approved' ? 'active' : 'court'}">${u.status==='approved' ? t('status_approved') : t('status_pending')}</span></td>
      <td>
        ${u.status==='pending'
          ? `<button class="btn-ghost user-approve" data-i="${i}">${t('btn_approve')}</button>`
          : `<button class="btn-ghost user-revoke" data-i="${i}">${t('btn_revoke')}</button>`}
      </td>
    </tr>
  `;
}

function auditRowHTML(log){
  return `
    <tr>
      <td class="hash-snip" style="font-family:var(--font-mono); border:none; background:none; padding:0;">${log.time}</td>
      <td>${log.user}</td>
      <td style="font-family: var(--font-mono);">${log.ip}</td>
      <td><span class="action-badge ${log.action}">${t("action_"+log.action)}</span> ${log.detail}</td>
    </tr>
  `;
}

/* =================================================================
   SECTION HANDLERS (wire up interactivity after render)
   ================================================================= */
const HANDLERS = {

  overview(){
    const CASE_SECTION_BY_ROLE = { io: "cases", forensic: "cases", judge: "docket", admin: null };
    document.querySelectorAll("#mainContent .case-list-item").forEach(el=>{
      el.addEventListener("click", ()=>{
        const target = CASE_SECTION_BY_ROLE[state.role];
        if(!target) return;
        state.caseId = el.getAttribute("data-case");
        state.section = target;
        renderSidebar();
        renderSection(target);
      });
    });
  },

  cases(){ wireCaseWorkspace(); },
  docket(){ wireCaseWorkspace(); },

  upload(){
    const dz = document.getElementById("dropzone");
    const input = document.getElementById("fileInput");
    const resultBox = document.getElementById("hashResult");
    const hashVal = document.getElementById("hashVal");

    async function process(file){
      if(!state.caseId){ toast("Select a case first", true); return; }
      resultBox.classList.remove("visible");
      try{
        const doc = await NV_API.upload(state.caseId, file);
        hashVal.textContent = doc.hash_sha256;
        resultBox.classList.add("visible");
        await loadLiveData();
        toast(`${t("hash_generated")}: ${doc.name}`);
      }catch(err){ toast(err.message, true); }
    }

    dz.addEventListener("click", ()=> input.click());
    input.addEventListener("change", ()=>{ if(input.files[0]) process(input.files[0]); });
    ["dragover","dragenter"].forEach(ev=> dz.addEventListener(ev, e=>{ e.preventDefault(); dz.classList.add("drag"); }));
    ["dragleave","drop"].forEach(ev=> dz.addEventListener(ev, e=>{ e.preventDefault(); dz.classList.remove("drag"); }));
    dz.addEventListener("drop", e=>{
      const f = e.dataTransfer.files[0];
      if(f) process(f);
    });
  },

  redaction(){
    document.querySelectorAll(".run-redaction").forEach(btn=>{
      btn.addEventListener("click", ()=>{
        const target = btn.getAttribute("data-target");
        const box = document.getElementById(`redact-${target}-result`);
        btn.disabled = true;
        btn.textContent = "…";
        setTimeout(()=>{
          box.classList.add("visible");
          btn.disabled = false;
          btn.textContent = t("btn_run_redaction");
          toast(t("section_redaction") + " — " + t("btn_run_redaction"));
        }, 900);
      });
    });
  },

  audio(){
    const btn = document.getElementById("transcribeBtn");
    const box = document.getElementById("transcriptBox");
    const lines = [
      ["00:02", "Caller: Main us jagah pahunch gaya hoon."],
      ["00:07", "Recipient: Theek hai, gaadi kis colour ki thi?"],
      ["00:11", "Caller: Laal rang ki thi, number clearly nahi dikha."],
      ["00:18", "Recipient: Theek hai, main forward kar deta hoon."],
    ];
    btn.addEventListener("click", ()=>{
      btn.disabled = true;
      box.innerHTML = `<div class="chip">${t("verify_running")}</div>`;
      setTimeout(()=>{
        box.innerHTML = lines.map(([ts,text])=>`<div class="transcript-line"><span class="ts">${ts}</span><span>${text}</span></div>`).join("");
        btn.disabled = false;
        toast(t("btn_transcribe") + " ✓");
      }, 1100);
    });
  },

  search(){
    const input = document.getElementById("caseSearchInput");
    const box = document.getElementById("caseSearchResults");
    input.addEventListener("keydown", (e)=>{
      if(e.key !== "Enter") return;
      const q = input.value.trim();
      if(!q){ box.innerHTML = ""; return; }
      box.innerHTML = `<div class="chip">Searching…</div>`;
      NV_API.search(q).then(results=>{
        box.innerHTML = results.length ? results.map(r=>`<div class="search-result-item"><div class="sr-case">${r.case_number}${r.document_name ? " — "+r.document_name : ""}</div>${r.snippet}</div>`).join("") : `<div class="search-result-item">No matches found.</div>`;
      }).catch(err=>{ box.innerHTML = `<div class="search-result-item">${err.message}</div>`; });
    });
  },

  verify(){
    const c = findCase(state.caseId);
    wireCaseListClicks(()=>{ state.docId = null; renderSection("verify"); });
    document.querySelectorAll("#mainContent .doc-card.selectable").forEach(el=>{
      el.addEventListener("click", ()=>{
        state.docId = el.getAttribute("data-doc");
        renderSection("verify");
      });
    });
    const btn = document.getElementById("verifyBtn");
    const result = document.getElementById("verifyResult");
    if(btn){
      btn.addEventListener("click", ()=>{
        const doc = state.docId ? findDoc(c, state.docId) : c.docs[0];
        btn.disabled = true;
        result.classList.add("visible");
        result.innerHTML = `<div class="label">${t("verify_running")}</div>`;
        NV_API.verify(doc.id).then(async verification=>{
          btn.disabled = false;
          const ok = verification.match;
          doc.status = verification.status;
          result.innerHTML = `<div class="label">${doc.name}</div><div class="doc-status ${ok ? 'verified' : 'tampered'}" style="font-size:14px;"><span class="dot"></span>${ok ? t('verify_ok') : t('verify_bad')}</div>`;
          toast(`${doc.name}: ${ok ? t('verify_ok') : t('verify_bad')}`, !ok);
        }).catch(err=>{ btn.disabled=false; result.innerHTML=`<div class="label">${err.message}</div>`; toast(err.message,true); });
      });
    }
  },

  exif(){
    wireCaseListClicks(()=>{ state.docId = null; renderSection("exif"); });
    document.querySelectorAll("#mainContent .doc-card.selectable").forEach(el=>{
      el.addEventListener("click", ()=>{
        state.docId = el.getAttribute("data-doc");
        renderSection("exif");
      });
    });
  },

  report(){
    wireCaseListClicks(()=> renderSection("report"));
    const btn = document.getElementById("generateReportBtn");
    btn.addEventListener("click", ()=>{
      btn.disabled = true;
      btn.textContent = "…";
      setTimeout(()=>{
        btn.disabled = false;
        btn.textContent = t("btn_generate_report");
        const c = findCase(state.caseId);
        toast(`${t('section_report')}: ${c.number}.pdf`);
      }, 1000);
    });
  },

  timeline(){
    wireCaseListClicks(()=> renderSection("timeline"));
  },

  courtroom(){
    wireCaseListClicks(()=> renderSection("courtroom"));
    document.getElementById("presentBtn").addEventListener("click", ()=>{
      const wmText = `${t("watermark_label")} ${state.user.toUpperCase()} · ${t(ROLE_META[state.role].labelKey).toUpperCase()}`;
      openModal(`
        <div class="presentation-view">
          <div class="clock" id="courtClock"></div>
          <div class="wm-overlay">${wmText.replace(/(.{22})/g,"$1\n")}</div>
          <div class="doc-mock">
            <strong>${findCase(state.caseId).number}</strong><br><br>
            ${findCase(state.caseId).title}<br><br>
            Evidence document rendered for court presentation. All viewer sessions are logged with timestamp and viewing officer.
          </div>
        </div>
      `);
      const clockEl = document.getElementById("courtClock");
      const tick = ()=>{ clockEl.textContent = new Date().toLocaleString(); };
      tick();
      const iv = setInterval(()=>{
        if(!document.getElementById("courtClock")){ clearInterval(iv); return; }
        tick();
      }, 1000);
      toast(t("btn_present") + " ✓");
    });
  },

  users(){
    document.getElementById("addUserBtn").addEventListener("click", ()=>{
      openModal(`
        <h3 class="font-head">${t("btn_add_user")}</h3>
        <div class="mock-form-grid" style="margin-top:14px;">
          <div class="field"><label>${t("th_name")}</label><div class="input-shell"><input type="text" placeholder="Insp. J. Doe"></div></div>
          <div class="field"><label>${t("th_badge")}</label><div class="input-shell"><input type="text" placeholder="IO-2400"></div></div>
        </div>
        <button class="btn-primary" style="margin-top:18px;" onclick="closeModal(); toast('${t('btn_add_user')} ✓');">${t("btn_add_user")}</button>
      `);
    });
    document.querySelectorAll(".user-approve").forEach(btn=>{
      btn.addEventListener("click", ()=>{
        const i = +btn.getAttribute("data-i");
        NV_API.approveUser(NV_USERS[i].id).then(()=>{ NV_USERS[i].status="approved"; renderSection("users"); toast(`${NV_USERS[i].name}: ${t('status_approved')}`); }).catch(err=>toast(err.message,true));
      });
    });
    document.querySelectorAll(".user-revoke").forEach(btn=>{
      btn.addEventListener("click", ()=>{
        const i = +btn.getAttribute("data-i");
        NV_API.revokeUser(NV_USERS[i].id).then(()=>{ NV_USERS[i].status="pending"; renderSection("users"); toast(`${NV_USERS[i].name}: ${t('btn_revoke')}`, true); }).catch(err=>toast(err.message,true));
      });
    });
  },

  auditlogs(){
    let n = 0;
    const iv = setInterval(()=>{
      const body = document.getElementById("auditTableBody");
      if(!body){ clearInterval(iv); return; }
      n++;
      if(n > 6){ clearInterval(iv); return; }
      const entry = {
        time: new Date().toLocaleTimeString(),
        user: "System",
        ip: "10.14.2." + (10+n),
        action: ["view","verify","upload"][n % 3],
        detail: "Live monitoring event",
      };
      body.insertAdjacentHTML("afterbegin", auditRowHTML(entry));
    }, 3000);
  },
};

function wireCaseListClicks(after){
  document.querySelectorAll("#mainContent .case-list-item").forEach(el=>{
    el.addEventListener("click", ()=>{
      state.caseId = el.getAttribute("data-case");
      after();
    });
  });
}

function wireCaseWorkspace(){
  wireCaseListClicks(()=> renderSection(state.section));
  const uploadBtn = document.getElementById("uploadEvidenceBtn");
  if(uploadBtn){
    uploadBtn.addEventListener("click", ()=>{ state.section="upload"; renderSidebar(); renderSection("upload"); });
  }
  document.querySelectorAll(".preview-doc").forEach(btn=>{
    btn.addEventListener("click", (e)=>{
      e.stopPropagation();
      const c = findCase(state.caseId);
      const doc = findDoc(c, btn.getAttribute("data-doc"));
      openModal(`
        <h3 class="font-head">${doc.name}</h3>
        <table class="exif-table" style="margin-top:10px;">
          <tr><td>${t("exif_device")}</td><td>${doc.exif.device}</td></tr>
          <tr><td>${t("exif_gps")}</td><td>${doc.exif.gps}</td></tr>
          <tr><td>${t("exif_created")}</td><td>${doc.exif.created}</td></tr>
          <tr><td>Hash</td><td>${doc.hash}</td></tr>
        </table>
      `);
    });
  });
}
