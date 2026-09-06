import {loadData,buildRecords} from "./api.js";
import {applyFilters} from "./filters.js";
import {currency,median,unique} from "./utils.js";

const el=id=>document.getElementById(id);
const state={records:[],meta:null,view:"university"};

function addOptions(selectId,items){
  const select=el(selectId);
  for(const item of items){
    const option=document.createElement("option");
    option.value=item.value;
    option.textContent=item.label;
    select.append(option);
  }
}

function populateFilters(records){
  const universities=unique(records.map(r=>JSON.stringify({value:r.university.university_id,label:r.university.name}))).map(JSON.parse).sort((a,b)=>a.label.localeCompare(b.label));
  const majors=unique(records.map(r=>JSON.stringify({value:r.major.major_id,label:r.major.name}))).map(JSON.parse).sort((a,b)=>a.label.localeCompare(b.label));
  const states=unique(records.map(r=>r.university.state).filter(Boolean)).sort().map(value=>({value,label:value}));
  const types=unique(records.map(r=>r.university.type).filter(Boolean)).sort().map(value=>({value,label:value}));
  addOptions("universityFilter",universities);
  addOptions("majorFilter",majors);
  addOptions("stateFilter",states);
  addOptions("typeFilter",types);
}

function currentFilters(){
  return {
    query:el("searchInput").value,
    university:el("universityFilter").value,
    major:el("majorFilter").value,
    state:el("stateFilter").value,
    institutionType:el("typeFilter").value,
    maxTuition:el("tuitionFilter").value,
  };
}

function groupRecords(records,keyFn){
  const groups=new Map();
  for(const record of records){
    const key=keyFn(record);
    if(!groups.has(key)) groups.set(key,[]);
    groups.get(key).push(record);
  }
  return [...groups.values()];
}

function groupValue(records,sort){
  if(sort==="earnings1") return median(records.map(r=>r.salary?.earnings_1yr));
  if(sort==="earnings4") return median(records.map(r=>r.salary?.earnings_4yr));
  if(sort==="tuition") return median(records.map(r=>r.tuition?.tuition));
  if(sort==="acceptance") return median(records.map(r=>r.admissions?.acceptance_rate));
  return null;
}

function compareNullable(a,b,direction){
  const aMissing=a==null || !Number.isFinite(a);
  const bMissing=b==null || !Number.isFinite(b);
  if(aMissing&&bMissing) return 0;
  if(aMissing) return 1;
  if(bMissing) return -1;
  return direction==="desc"?b-a:a-b;
}

function sortGroups(groups,view,sort){
  return [...groups].sort((a,b)=>{
    if(sort==="name"){
      const aName=view==="university"?a[0].university.name:a[0].major.name;
      const bName=view==="university"?b[0].university.name:b[0].major.name;
      return aName.localeCompare(bName);
    }
    const direction=(sort==="tuition"||sort==="acceptance")?"asc":"desc";
    const metric=compareNullable(groupValue(a,sort),groupValue(b,sort),direction);
    if(metric!==0) return metric;
    const aName=view==="university"?a[0].university.name:a[0].major.name;
    const bName=view==="university"?b[0].university.name:b[0].major.name;
    return aName.localeCompare(bName);
  });
}

function sortRows(records,view,sort){
  return [...records].sort((a,b)=>{
    const aName=view==="university"?a.major.name:a.university.name;
    const bName=view==="university"?b.major.name:b.university.name;
    if(sort==="name" || ((sort==="tuition"||sort==="acceptance")&&view==="university")) return aName.localeCompare(bName);
    const field=sort==="earnings1"?"earnings_1yr":sort==="earnings4"?"earnings_4yr":null;
    let aValue,bValue,direction;
    if(field){aValue=a.salary?.[field];bValue=b.salary?.[field];direction="desc";}
    else if(sort==="tuition"){aValue=a.tuition?.tuition;bValue=b.tuition?.tuition;direction="asc";}
    else if(sort==="acceptance"){aValue=a.admissions?.acceptance_rate;bValue=b.admissions?.acceptance_rate;direction="asc";}
    const metric=compareNullable(aValue,bValue,direction);
    return metric!==0?metric:aName.localeCompare(bName);
  });
}

function acceptance(record){return record.admissions?.acceptance_rate==null?"—":`${record.admissions.acceptance_rate}%`;}

function renderUniversityGroup(records,sort){
  const sorted=sortRows(records,"university",sort);
  const first=sorted[0];
  const university=first.university;
  const tuition=first.tuition?.tuition;
  const median1=median(sorted.map(r=>r.salary?.earnings_1yr));
  const rows=sorted.map(r=>`<tr><td>${r.major.name}</td><td class="metric">${currency(r.salary?.earnings_1yr)}</td><td class="metric">${currency(r.salary?.earnings_4yr)}</td></tr>`).join("");
  return `<details class="result-card"><summary><div class="result-main"><strong>${university.name}</strong><span>${university.city}, ${university.state} · ${university.type}</span></div><div class="result-stats"><span><small>Bachelor's programs</small><b>${sorted.length}</b></span><span><small>Median across bachelor's programs</small><b>${currency(median1)}</b></span><span><small>In-state tuition</small><b>${currency(tuition)}</b></span><span><small>Acceptance rate</small><b>${acceptance(first)}</b></span></div><span class="expand-label">View majors</span></summary><div class="result-table-wrap"><table class="result-table"><thead><tr><th>Major</th><th>1-year median earnings</th><th>4-year median earnings</th></tr></thead><tbody>${rows}</tbody></table></div></details>`;
}

function renderMajorGroup(records,sort){
  const sorted=sortRows(records,"major",sort);
  const first=sorted[0];
  const major=first.major;
  const median1=median(sorted.map(r=>r.salary?.earnings_1yr));
  const median4=median(sorted.map(r=>r.salary?.earnings_4yr));
  const medianTuition=median(sorted.map(r=>r.tuition?.tuition));
  const rows=sorted.map(r=>`<tr><td>${r.university.name}<br><small>${r.university.city}, ${r.university.state}</small></td><td class="metric">${currency(r.salary?.earnings_1yr)}</td><td class="metric">${currency(r.salary?.earnings_4yr)}</td><td class="metric">${currency(r.tuition?.tuition)}</td><td class="metric">${acceptance(r)}</td></tr>`).join("");
  return `<details class="result-card"><summary><div class="result-main"><strong>${major.name}</strong><span>Bachelor's field of study</span></div><div class="result-stats"><span><small>Universities</small><b>${sorted.length}</b></span><span><small>Median 1-year earnings</small><b>${currency(median1)}</b></span><span><small>Median 4-year earnings</small><b>${currency(median4)}</b></span><span><small>Median in-state tuition</small><b>${currency(medianTuition)}</b></span></div><span class="expand-label">View universities</span></summary><div class="result-table-wrap"><table class="result-table wide"><thead><tr><th>University</th><th>1-year median earnings</th><th>4-year median earnings</th><th>In-state tuition</th><th>Acceptance rate</th></tr></thead><tbody>${rows}</tbody></table></div></details>`;
}

function updateViewLabels(){
  const byUniversity=state.view==="university";
  el("browseEyebrow").textContent=byUniversity?"Browse by university":"Browse by major";
  el("browseTitle").textContent=byUniversity?"100 universities at a glance":"Compare majors across universities";
  for(const button of document.querySelectorAll(".view-button")){
    const active=button.dataset.view===state.view;
    button.classList.toggle("active",active);
    button.setAttribute("aria-pressed",String(active));
  }
}

function render(records){
  const sort=el("sortFilter").value;
  const groups=state.view==="university"
    ?groupRecords(records,r=>r.university.university_id)
    :groupRecords(records,r=>r.major.major_id);
  const sortedGroups=sortGroups(groups,state.view,sort);
  el("resultCount").textContent=state.view==="university"
    ?`${sortedGroups.length} universit${sortedGroups.length===1?"y":"ies"} · ${records.length} programs`
    :`${sortedGroups.length} major${sortedGroups.length===1?"":"s"} · ${records.length} university-programs`;
  el("universityCount").textContent=unique(records.map(r=>r.university.university_id)).length;
  el("majorCount").textContent=unique(records.map(r=>r.major.major_id)).length;
  el("programCount").textContent=records.length;
  el("medianSalary").textContent=currency(median(records.map(r=>r.salary?.earnings_1yr)));
  el("emptyState").hidden=records.length>0;
  el("browseGroups").innerHTML=sortedGroups.map(group=>state.view==="university"?renderUniversityGroup(group,sort):renderMajorGroup(group,sort)).join("");
  updateViewLabels();
}

function refresh(){render(applyFilters(state.records,currentFilters()));}

async function init(){
  try{
    const data=await loadData();
    state.meta=data.metadata;
    state.records=buildRecords(data);
    populateFilters(state.records);
    ["searchInput","universityFilter","majorFilter","stateFilter","typeFilter","tuitionFilter","sortFilter"].forEach(id=>el(id).addEventListener(id==="searchInput"?"input":"change",refresh));
    document.querySelectorAll(".view-button").forEach(button=>button.addEventListener("click",()=>{state.view=button.dataset.view;refresh();}));
    el("dataBadge").textContent=`${data.metadata.status} · ${data.metadata.current_year}`;
    refresh();
  }catch(error){
    console.error(error);
    el("dataBadge").textContent="Data load error";
    el("emptyState").hidden=false;
    el("emptyState").textContent="Unable to load project data.";
  }
}

init();
