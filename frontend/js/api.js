const NV_API = {
  token(){ return localStorage.getItem("nv_token"); },
  headers(extra={}){
    const h = {...extra};
    const token = this.token();
    if(token) h.Authorization = `Bearer ${token}`;
    return h;
  },
  async request(path, options={}){
    options.headers = this.headers(options.headers || {});
    const res = await fetch(path, options);
    if(res.status === 401){
      localStorage.removeItem("nv_token");
      localStorage.removeItem("nv_role");
      localStorage.removeItem("nv_user");
      if(!location.pathname.endsWith("login.html") && location.pathname !== "/") location.href = "/login.html";
    }
    if(!res.ok){
      let message = `Request failed (${res.status})`;
      try { const body = await res.json(); message = body.detail || message; } catch(_) {}
      throw new Error(message);
    }
    const type = res.headers.get("content-type") || "";
    return type.includes("application/json") ? res.json() : res;
  },
  login(username,password,role){
    return this.request("/api/auth/login", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({username,password,role})});
  },
  me(){ return this.request("/api/auth/me"); },
  cases(){ return this.request("/api/cases"); },
  caseDetail(id){ return this.request(`/api/cases/${encodeURIComponent(id)}`); },
  overview(){ return this.request("/api/cases/overview/summary"); },
  users(){ return this.request("/api/users"); },
  audit(caseId){ return this.request(`/api/audit-logs${caseId ? `?case_id=${encodeURIComponent(caseId)}` : ""}`); },
  search(q){ return this.request(`/api/search?q=${encodeURIComponent(q)}`); },
  verify(id){ return this.request(`/api/documents/${encodeURIComponent(id)}/verify`, {method:"POST"}); },
  approveUser(id){ return this.request(`/api/users/${encodeURIComponent(id)}/approve`, {method:"POST"}); },
  revokeUser(id){ return this.request(`/api/users/${encodeURIComponent(id)}/revoke`, {method:"POST"}); },
  present(id){ return this.request(`/api/cases/${encodeURIComponent(id)}/present`, {method:"POST"}); },
  async upload(caseId,file){ const fd=new FormData(); fd.append("file",file); return this.request(`/api/cases/${encodeURIComponent(caseId)}/documents`, {method:"POST",body:fd}); },
  async logout(){ try { await this.request("/api/auth/logout", {method:"POST"}); } catch(_) {} },
};
