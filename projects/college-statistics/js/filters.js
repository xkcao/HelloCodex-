import {matchesSearch} from "./search.js";

export function applyFilters(records,filters){
  const {query,university,major,state,institutionType,maxTuition}=filters;
  return records.filter(record => {
    const tuition=record.tuition?.tuition;
    return matchesSearch(record,query) &&
      (university==="all" || record.university.university_id===university) &&
      (major==="all" || record.major.major_id===major) &&
      (state==="all" || record.university.state===state) &&
      (institutionType==="all" || record.university.type===institutionType) &&
      (maxTuition==="all" || (Number.isFinite(tuition) && tuition<=Number(maxTuition)));
  });
}
