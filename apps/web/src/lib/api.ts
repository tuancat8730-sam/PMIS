export const DEFAULT_API_URL = "http://localhost:8000";
export const HEALTH_PATH = "/api/v1/health";

export type ApiHealthStatus = "ok" | "unreachable";

interface HealthBody {
  status: string;
}

function isHealthBody(value: unknown): value is HealthBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    typeof value.status === "string"
  );
}

export function resolveApiUrl(
  path: string,
  baseUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): string {
  const base = (baseUrl ?? DEFAULT_API_URL).replace(/\/+$/, "");
  return `${base}/${path.replace(/^\/+/, "")}`;
}

export async function fetchApiHealth(
  fetchImpl: typeof fetch = fetch,
): Promise<ApiHealthStatus> {
  try {
    const response = await fetchImpl(resolveApiUrl(HEALTH_PATH), { cache: "no-store" });
    if (!response.ok) {
      return "unreachable";
    }
    const body: unknown = await response.json();
    return isHealthBody(body) && body.status === "ok" ? "ok" : "unreachable";
  } catch {
    return "unreachable";
  }
}
