interface DriveSyncBarProps {
  lastSyncedAt: string | null;
  syncing: boolean;
  message: string | null;
  onSync: () => void;
}

const SYNC_TIME_FORMAT: Intl.DateTimeFormatOptions = {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "Asia/Ho_Chi_Minh",
};

function formatSyncTime(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", SYNC_TIME_FORMAT);
}

/** Thanh trạng thái đồng bộ: thời điểm cập nhật gần nhất và nút quét ngay. */
export function DriveSyncBar({ lastSyncedAt, syncing, message, onSync }: DriveSyncBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-md bg-neutral-50 p-3">
      <p className="text-sm text-neutral-700">
        {lastSyncedAt ? `Cập nhật lúc ${formatSyncTime(lastSyncedAt)}` : "Chưa đồng bộ lần nào"}
      </p>
      <button
        type="button"
        onClick={onSync}
        disabled={syncing}
        className={`min-h-11 rounded-md bg-neutral-900 px-4 font-semibold text-white${syncing ? " opacity-50" : ""}`}
      >
        {syncing ? "Đang quét…" : "Quét ngay"}
      </button>
      {message && (
        <p role="status" className="w-full text-sm text-neutral-700">
          {message}
        </p>
      )}
    </div>
  );
}
