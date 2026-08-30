export const currency = value => Number.isFinite(value) ? new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}).format(value) : "—";
export const percent = value => Number.isFinite(value) ? `${value}%` : "—";
export const median = values => {const nums=values.filter(Number.isFinite).sort((a,b)=>a-b);if(!nums.length)return null;const mid=Math.floor(nums.length/2);return nums.length%2?nums[mid]:(nums[mid-1]+nums[mid])/2;};
export const average = values => {const nums=values.filter(Number.isFinite);return nums.length?nums.reduce((a,b)=>a+b,0)/nums.length:null;};
export const unique = values => [...new Set(values)];
