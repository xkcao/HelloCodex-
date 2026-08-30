import {loadData,buildRecords} from "./api.js";
import {applyFilters} from "./filters.js";
import {currency,median,unique} from "./utils.js";

const el=id=>document.getElementById(id);
const PAGE_SIZE=20;
const state={records:[],meta:null,page:1};

function populateUniversities(records){
  const universities=unique(records.map(r=>JSON.stringify({id:r.university.university_id,name:r.university.name}))).map(JSON.parse).sort((a,b)=>a.name.localeCompare(b.name));
  for(const university of universities){const option=document.createElement("option");option.value=university.id;option.textContent=university.name;el("universityFilter").append(option);}
}

function populateMajors(records){
  const majors=unique(records.map(r=>JSON.stringify({id:r.major.major_id,name:r.major.name}))).map(JSON.parse).sort((a,b)=>a.name.localeCompare(b.name));
  for(const major of majors){const option=document.createElement("option");option.value=major.id;option.textContent=major.name;el("majorFilter").append(option);}
}

function currentFilters(){return {query:el("searchInput").value,university:el("universityFilter").value,major:el("majorFilter").value,maxTuition:el("tuitionFilter").value};}

function render(records){
  const sorted=[...records].sort((a,b)=>a.university.name.localeCompare(b.university.name)||a.major.name.localeCompare(b.major.name));
  const totalPages=Math.max(1,Math.ceil(sorted.length/PAGE_SIZE));
  if(state.page>totalPages) state.page=totalPages;
  const start=(state.page-1)*PAGE_SIZE;
  const pageRows=sorted.slice(start,start+PAGE_SIZE);
  const first=sorted.length?start+1:0;
  const last=Math.min(start+PAGE_SIZE,sorted.length);

  el("resultCount").textContent=sorted.length?`Showing ${first}–${last} of ${sorted.length} programs`:`0 programs`;
  el("universityCount").textContent=unique(sorted.map(r=>r.university.university_id)).length;
  el("majorCount").textContent=unique(sorted.map(r=>r.major.major_id)).length;
  el("programCount").textContent=sorted.length;
  el("medianSalary").textContent=currency(median(sorted.map(r=>r.salary?.earnings_1yr)));
  el("emptyState").hidden=sorted.length>0;
  el("resultsBody").innerHTML=pageRows.map(r=>`<tr><td>${r.university.name}<br><small>${r.university.city}, ${r.university.state}</small></td><td>${r.major.name}</td><td class="metric">${currency(r.salary?.earnings_1yr)}</td><td class="metric">${currency(r.salary?.earnings_4yr)}</td><td class="metric">${currency(r.tuition?.tuition)}</td><td class="metric">${r.admissions?.acceptance_rate==null?"—":`${r.admissions.acceptance_rate}%`}</td></tr>`).join("");

  el("pageInfo").textContent=`Page ${state.page} of ${totalPages}`;
  el("prevPage").disabled=state.page<=1;
  el("nextPage").disabled=state.page>=totalPages;
  el("pagination").hidden=sorted.length===0;
}

function refresh(resetPage=true){
  if(resetPage) state.page=1;
  render(applyFilters(state.records,currentFilters()));
}

async function init(){
  try{
    const data=await loadData();
    state.meta=data.metadata;
    state.records=buildRecords(data);
    populateUniversities(state.records);
    populateMajors(state.records);
    ["searchInput","universityFilter","majorFilter","tuitionFilter"].forEach(id=>el(id).addEventListener(id==="searchInput"?"input":"change",()=>refresh(true)));
    el("prevPage").addEventListener("click",()=>{if(state.page>1){state.page--;refresh(false);}});
    el("nextPage").addEventListener("click",()=>{state.page++;refresh(false);});
    el("dataBadge").textContent=`${data.metadata.status} · ${data.metadata.current_year}`;
    refresh(true);
  }catch(error){
    console.error(error);
    el("dataBadge").textContent="Data load error";
    el("emptyState").hidden=false;
    el("emptyState").textContent="Unable to load project data.";
  }
}

init();
