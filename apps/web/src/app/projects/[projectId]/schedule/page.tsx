"use client";

import { useParams } from "next/navigation";
import { useCallback, useState } from "react";

import { MatrixPage } from "../../../../components/tracking/matrix-page";
import { ScheduleTable } from "../../../../components/tracking/schedule-table";
import { fetchScheduleMatrix } from "../../../../lib/tracking";

export default function SchedulePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [reloadKey, setReloadKey] = useState(0);
  const handleChanged = useCallback(() => setReloadKey((key) => key + 1), []);
  return (
    <MatrixPage
      projectId={projectId}
      title="Kế hoạch và tiến độ"
      reloadKey={reloadKey}
      load={(token) => fetchScheduleMatrix(projectId, token)}
      render={(data) => (
        <ScheduleTable rows={data.rows} projectId={projectId} onChanged={handleChanged} />
      )}
    />
  );
}
