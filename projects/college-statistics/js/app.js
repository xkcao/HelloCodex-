const state={records:[]};
const $=id=>document.getElementById(id);
const money=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0});
const percent=value=>`${Number(value).toFixed(0)}%`;

async function loadData(){
  try{
    const response=await fetch('data/colleges.json');
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    state.records=await response.json();
    populateMajors();
    applyFilters();
  }catch(error){
    console.error('Unable to load college data:',error);
    $('resultsBody').innerHTML='<tr><td colspan="6">Unable to load placeholder data.</td></tr>';
  }
}

function populateMajors(){
  const majors=[...new Set(state.records.map(r=>r.major))].sort();
  majors.forEach(major=>{
    const option=document.createElement('option');
    option.value=major;
    option.textContent=major;
    $('majorFilter').appendChild(option);
  });
}

function applyFilters(){
  const query=$('searchInput').value.trim().toLowerCase();
  const major=$('majorFilter').value;
  const maxTuition=$('tuitionFilter').value;
  const minEmployment=Number($('employmentFilter').value);
  const filtered=state.records.filter(record=>{
    const matchesText=!query||`${record.university} ${record.major}`.toLowerCase().includes(query);
    const matchesMajor=major==='all'||record.major===major;
    const matchesTuition=maxTuition==='all'||record.tuition<=Number(maxTuition);
    const matchesEmployment=record.employmentRate>=minEmployment;
    return matchesText&&matchesMajor&&matchesTuition&&matchesEmployment;
  });
  renderRows(filtered);
  updateSummary(filtered);
}

function renderRows(records){
  const body=$('resultsBody');
  body.innerHTML=records.map(record=>`<tr>
    <td>${escapeHtml(record.university)}<br><small>${escapeHtml(record.location)}</small></td>
    <td>${escapeHtml(record.major)}</td>
    <td class="metric">${money.format(record.medianSalary)}</td>
    <td class="metric employment">${percent(record.employmentRate)}</td>
    <td class="metric">${money.format(record.tuition)}</td>
    <td class="metric">${percent(record.acceptanceRate)}</td>
  </tr>`).join('');
  $('emptyState').hidden=records.length!==0;
  $('resultCount').textContent=`${records.length} record${records.length===1?'':'s'}`;
}

function updateSummary(records){
  const universities=new Set(records.map(r=>r.university));
  const majors=new Set(records.map(r=>r.major));
  const salaries=records.map(r=>r.medianSalary).sort((a,b)=>a-b);
  const mid=Math.floor(salaries.length/2);
  const median=salaries.length?(salaries.length%2?salaries[mid]:(salaries[mid-1]+salaries[mid])/2):0;
  const employment=records.length?records.reduce((sum,r)=>sum+r.employmentRate,0)/records.length:0;
  $('universityCount').textContent=universities.size;
  $('majorCount').textContent=majors.size;
  $('medianSalary').textContent=records.length?money.format(median):'—';
  $('employmentRate').textContent=records.length?percent(employment):'—';
}

function escapeHtml(value){
  return String(value).replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

['searchInput','majorFilter','tuitionFilter','employmentFilter'].forEach(id=>{
  $(id).addEventListener(id==='searchInput'?'input':'change',applyFilters);
});
loadData();
