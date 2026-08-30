export function matchesSearch(record, query){
  if(!query) return true;
  const haystack=[record.university.name,record.university.short_name,record.university.city,record.university.state,record.university.country,record.major.name,record.major.category].join(" ").toLowerCase();
  return haystack.includes(query.trim().toLowerCase());
}
