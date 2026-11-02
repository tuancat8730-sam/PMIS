"use client";

import { useEffect, useState } from "react";

import { fetchMyProjectRole } from "../../lib/milestone-api";
import { effectiveProjectRole, readTokenClaims } from "../../lib/milestone-permissions";
import { readStoredToken } from "./matrix-page";

export interface ProjectAccess {
  token: string | null;
  role: string | null;
}

const NO_ACCESS: ProjectAccess = { token: null, role: null };

/**
 * Token và vai trò của người dùng trong dự án. Vai trò là null cho đến khi tải xong
 * hoặc khi không có phiên. Dùng để ẩn/hiện form; server vẫn kiểm quyền khi ghi.
 */
export function useProjectAccess(projectId: string): ProjectAccess {
  const [access, setAccess] = useState<ProjectAccess>(NO_ACCESS);

  useEffect(() => {
    let cancelled = false;
    const token = readStoredToken();
    const claims = token === null ? null : readTokenClaims(token);
    if (token === null || claims === null) {
      setAccess(NO_ACCESS);
      return;
    }
    fetchMyProjectRole(projectId, claims.subject, token)
      .then((membership) => {
        if (!cancelled) {
          setAccess({ token, role: effectiveProjectRole(claims, membership) });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAccess({ token, role: effectiveProjectRole(claims, null) });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return access;
}
