const DATA_FILES = ["universities","majors","university-major","tuition","salaries","admissions","metadata"];

async function loadJson(name){
  const response = await fetch(`data/${name}.json`, {cache:"no-cache"});
  if(!response.ok) throw new Error(`Failed to load ${name}.json`);
  return response.json();
}

export async function loadData(){
  const entries = await Promise.all(DATA_FILES.map(async name => [name, await loadJson(name)]));
  return Object.fromEntries(entries);
}

export function buildRecords(data){
  const universities = new Map(data.universities.map(item => [item.university_id,item]));
  const majors = new Map(data.majors.map(item => [item.major_id,item]));
  const salaries = new Map(data.salaries.map(item => [`${item.university_id}|${item.major_id}`,item]));
  const tuition = new Map(data.tuition.map(item => [item.university_id,item]));
  const admissions = new Map(data.admissions.map(item => [item.university_id,item]));

  return data["university-major"].filter(rel => rel.available).map(rel => {
    const university = universities.get(rel.university_id);
    const major = majors.get(rel.major_id);
    const pairKey = `${rel.university_id}|${rel.major_id}`;
    return {university,major,relationship:rel,salary:salaries.get(pairKey),tuition:tuition.get(rel.university_id),admissions:admissions.get(rel.university_id)};
  }).filter(record => record.university && record.major);
}
