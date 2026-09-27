export const CATEGORY_COLORS = {
  Bug: "border-brick text-brick",
  Documentation: "border-moss text-moss",
  Enhancement: "border-amber text-amber",
  Question: "border-slate text-slate",
  "Good First Issue": "border-moss text-moss",
};

export function categoryClass(category) {
  return CATEGORY_COLORS[category] || "border-slate text-slate";
}
