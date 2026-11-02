"use client";

import { useId, useState, type ReactNode } from "react";

interface ExpandableItemProps {
  summary: ReactNode;
  details: ReactNode;
}

/**
 * Một dòng dữ liệu. Trên điện thoại, phần chi tiết ẩn và mở bằng nút.
 * Từ lg trở lên, chi tiết luôn hiện như dòng mở rộng bên dưới.
 */
export function ExpandableItem({ summary, details }: ExpandableItemProps) {
  const [expanded, setExpanded] = useState(false);
  const detailsId = useId();
  return (
    <li className="flex flex-col gap-3 border-b border-border-subtle py-4 lg:gap-2">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="min-w-0 flex-1">{summary}</div>
        <button
          type="button"
          aria-expanded={expanded}
          aria-controls={detailsId}
          onClick={() => setExpanded((current) => !current)}
          className="min-h-11 self-start rounded-md border border-border-subtle px-3 text-sm font-medium text-primary lg:hidden"
        >
          {expanded ? "Thu gọn" : "Chi tiết"}
        </button>
      </div>
      <div id={detailsId} className={expanded ? "block" : "hidden lg:block"}>
        {details}
      </div>
    </li>
  );
}
