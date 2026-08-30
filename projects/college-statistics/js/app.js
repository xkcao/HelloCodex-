import {loadData,buildRecords} from "./api.js";
import {applyFilters} from "./filters.js";
import {currency,median,unique} from "./utils.js";

const el=id=>document.getElementById(id);
const state={records:[],meta:null};

function populateMajors(records){
  const majors=unique(records.map(r=>JSON.stringify({id:r.major.major_id,name:r.major.name}))).map(JSON.parse).sort((a,b)=>a.name.localeCompare(b.name));
  for(const major of majors){const option=document.createElement("option");option.value=major.id;option.textContent=major.name;el("majorFilter").append(option);}
}

function currentFilters(){return {query:el("searchInput").value,major:el("majorFilter").value,maxTuition:el("tuitionFilter").value};}

function render(records){
  el("resultCount").textContent=`${records.length} program${records.length===1?"":"s"}`;
  el("universityCount").textContent=unique(records.map(r=>r.university.university_id)).length;
  el("majorCount").textContent=unique(records.map(r=>r.major.major_id)).length;
  el("programCount").textContent=records.length;
  el("medianSalary").textContent=currency(median(records.map(r=>r.salary?.earnings_1yr)));
  el("emptyState").hidden=records.length>0;
  el("resultsBody").innerHTML=records.map(r=>`<tr><td>${r.university.name}<br><small>${r.university.city}, ${r.university.state}</small></td><td>${r.major.name}</td><td class="metric">${currency(r.salary?.earnings_1yr)}</td><td class="metric">${currency(r.salary?.earnings_4yr)}</td><td class="metric">${currency(r.tuition?.tuition)}</td><td class="metric">${r.admissions?.acceptance_rate==null?"—":`${r.admissions.acceptance_rate}%`}</td></tr>`).join("");
}

function refresh(){render(applyFilters(state.records,currentFilters()));}

async function init(){
  try{
    const data=await loadData();
    state.meta=data.metadata;
    state.records=buildRecords(data);
    populateMajors(state.records);
    ["searchInput","majorFilter","tuitionFilter"].forEach(id=>el(id).addEventListener(id==="searchInput"?"input":"change",refresh));
    el("dataBadge").textContent=`${data.metadata.status} · ${data.metadata.current_year}`;
    render(state.records);
  }catch(error){
    console.error(error);
    el("dataBadge").textContent="Data load error";
    el("emptyState").hidden=false;
    el("emptyState").textContent="Unable to load project data.";
  }
}

init();
