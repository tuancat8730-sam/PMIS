"use client";

import { useParams } from "next/navigation";

import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { ScheduleTable } from "../../../../components/tracking/schedule-table";
import { fetchScheduleMatrix } from "../../../../lib/tracking";

export default function SchedulePage() {
  const { projectId } = useParams<{ projectId: string }>();
  return (
    <MatrixPage
      projectId={projectId}
      title="Kế hoạch và tiến độ"
      load={(token) => fetchScheduleMatrix(projectId, token)}
      render={(data) => <ScheduleTable rows={data.rows} />}
    />
  );
}
