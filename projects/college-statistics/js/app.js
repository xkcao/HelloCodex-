import {loadData,buildRecords} from "./api.js";
import {applyFilters} from "./filters.js";
import {currency,median,unique} from "./utils.js";

const el=id=>document.getElementById(id);
const state={records:[],meta:null};

function populateUniversities(records){
  const universities=unique(records.map(r=>JSON.stringify({id:r.university.university_id,name:r.university.name}))).map(JSON.parse).sort((a,b)=>a.name.localeCompare(b.name));
  for(const university of universities){const option=document.createElement("option");option.value=university.id;option.textContent=university.name;el("universityFilter").append(option);}
}

function populateMajors(records){
  const majors=unique(records.map(r=>JSON.stringify({id:r.major.major_id,name:r.major.name}))).map(JSON.parse).sort((a,b)=>a.name.localeCompare(b.name));
  for(const major of majors){const option=document.createElement("option");option.value=major.id;option.textContent=major.name;el("majorFilter").append(option);}
}

function currentFilters(){return {query:el("searchInput").value,university:el("universityFilter").value,major:el("majorFilter").value,maxTuition:el("tuitionFilter").value};}

function groupByUniversity(records){
  const groups=new Map();
  for(const record of records){
    const id=record.university.university_id;
    if(!groups.has(id)) groups.set(id,[]);
    groups.get(id).push(record);
  }
  return [...groups.values()].sort((a,b)=>a[0].university.name.localeCompare(b[0].university.name));
}

function acceptance(record){return record.admissions?.acceptance_rate==null?"—":`${record.admissions.acceptance_rate}%`;}

function renderUniversityGroup(records){
  const sorted=[...records].sort((a,b)=>a.major.name.localeCompare(b.major.name));
  const first=sorted[0];
  const university=first.university;
  const tuition=first.tuition?.tuition;
  const median1=median(sorted.map(r=>r.salary?.earnings_1yr));
  const rows=sorted.map(r=>`<tr><td>${r.major.name}</td><td class="metric">${currency(r.salary?.earnings_1yr)}</td><td class="metric">${currency(r.salary?.earnings_4yr)}</td></tr>`).join("");
  return `<details class="university-card"><summary><div class="university-main"><strong>${university.name}</strong><span>${university.city}, ${university.state}</span></div><div class="university-stats"><span><small>Bachelor's programs</small><b>${sorted.length}</b></span><span><small>Median across bachelor's programs</small><b>${currency(median1)}</b></span><span><small>In-state tuition</small><b>${currency(tuition)}</b></span><span><small>Acceptance rate</small><b>${acceptance(first)}</b></span></div><span class="expand-label">View majors</span></summary><div class="major-table-wrap"><table class="major-table"><thead><tr><th>Major</th><th>1-year median earnings</th><th>4-year median earnings</th></tr></thead><tbody>${rows}</tbody></table></div></details>`;
}

function render(records){
  const groups=groupByUniversity(records);
  el("resultCount").textContent=`${groups.length} universit${groups.length===1?"y":"ies"} · ${records.length} programs`;
  el("universityCount").textContent=groups.length;
  el("majorCount").textContent=unique(records.map(r=>r.major.major_id)).length;
  el("programCount").textContent=records.length;
  el("medianSalary").textContent=currency(median(records.map(r=>r.salary?.earnings_1yr)));
  el("emptyState").hidden=records.length>0;
  el("universityGroups").innerHTML=groups.map(renderUniversityGroup).join("");
}

function refresh(){render(applyFilters(state.records,currentFilters()));}

async function init(){
  try{
    const data=await loadData();
    state.meta=data.metadata;
    state.records=buildRecords(data);
    populateUniversities(state.records);
    populateMajors(state.records);
    ["searchInput","universityFilter","majorFilter","tuitionFilter"].forEach(id=>el(id).addEventListener(id==="searchInput"?"input":"change",refresh));
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
