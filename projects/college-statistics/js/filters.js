import {matchesSearch} from "./search.js";

export function applyFilters(records,{query,university,major,maxTuition}){
  return records.filter(record => {
    const tuition=record.tuition?.tuition;
    return matchesSearch(record,query) &&
      (university==="all" || record.university.university_id===university) &&
      (major==="all" || record.major.major_id===major) &&
      (maxTuition==="all" || (Number.isFinite(tuition) && tuition<=Number(maxTuition)));
  });
}
