import {matchesSearch} from "./search.js";

export function applyFilters(records,{query,major,maxTuition}){
  return records.filter(record => {
    const tuition=record.tuition?.tuition;
    return matchesSearch(record,query) &&
      (major==="all" || record.major.major_id===major) &&
      (maxTuition==="all" || (Number.isFinite(tuition) && tuition<=Number(maxTuition)));
  });
}
