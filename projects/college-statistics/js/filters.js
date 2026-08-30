import {matchesSearch} from "./search.js";

export function applyFilters(records,{query,major,maxTuition,minEmployment}){
  return records.filter(record => {
    const tuition=record.tuition?.tuition;
    const employment=record.employment?.employment_rate;
    return matchesSearch(record,query) &&
      (major==="all" || record.major.major_id===major) &&
      (maxTuition==="all" || (Number.isFinite(tuition) && tuition<=Number(maxTuition))) &&
      (!Number(minEmployment) || (Number.isFinite(employment) && employment>=Number(minEmployment)));
  });
}
