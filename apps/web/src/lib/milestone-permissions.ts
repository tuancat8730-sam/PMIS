export type ProjectRole =
  | "ADMIN"
  | "PM"
  | "PM_CONSULTANT"
  | "SUPERVISION_CONSULTANT"
  | "INVESTOR"
  | "CONTRACTOR"
  | "FIELD_ENGINEER";

export interface TokenClaims {
  subject: string;
  role: string;
}

const JWT_SEGMENT_COUNT = 3;
const BASE64_BLOCK_SIZE = 4;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** JWT dùng base64url không padding; đổi sang base64 chuẩn để atob đọc được. */
function toStandardBase64(segment: string): string {
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const paddingLength = (BASE64_BLOCK_SIZE - (base64.length % BASE64_BLOCK_SIZE)) % BASE64_BLOCK_SIZE;
  return base64 + "=".repeat(paddingLength);
}

/**
 * Đọc `sub` và `role` từ phần payload của JWT để giao diện biết người dùng là ai.
 * Không xác minh chữ ký: chỉ dùng để ẩn/hiện nút, server vẫn kiểm quyền thật.
 */
export function readTokenClaims(token: string): TokenClaims | null {
  const segments = token.split(".");
  if (segments.length !== JWT_SEGMENT_COUNT) {
    return null;
  }
  try {
    const payload: unknown = JSON.parse(atob(toStandardBase64(segments[1])));
    if (
      isRecord(payload) &&
      typeof payload.sub === "string" &&
      typeof payload.role === "string"
    ) {
      return { subject: payload.sub, role: payload.role };
    }
    return null;
  } catch {
    return null;
  }
}

/** ADMIN toàn cục có quyền mọi dự án. Người khác lấy vai trò từ danh sách thành viên dự án. */
export function effectiveProjectRole(
  claims: TokenClaims,
  membershipRole: string | null,
): string | null {
  if (claims.role === "ADMIN") {
    return "ADMIN";
  }
  return membershipRole;
}

/** Khớp với server: PATCH mốc chỉ PM (và ADMIN) được sửa. */
export function canEditMilestoneFields(role: string | null): boolean {
  return role === "PM" || role === "ADMIN";
}

/** Khớp với server: ghi chú và task do PM hoặc TVGS (SUPERVISION_CONSULTANT) thực hiện. */
export function canWriteTasksAndNotes(role: string | null): boolean {
  return role === "PM" || role === "SUPERVISION_CONSULTANT" || role === "ADMIN";
}
