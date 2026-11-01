export type FieldActionMethod = "PATCH" | "POST";
export type FieldActionStatus = "PENDING" | "CONFLICT" | "REJECTED";

/**
 * Một thao tác hiện trường chờ gửi. `id` cũng là Idempotency-Key, nên gửi lại
 * luôn dùng cùng khóa và máy chủ trả đúng kết quả cũ thay vì ghi thêm bản mới.
 */
export interface FieldAction {
  readonly id: string;
  readonly deviceId: string;
  readonly method: FieldActionMethod;
  readonly path: string;
  readonly body: unknown;
  readonly status: FieldActionStatus;
  readonly createdAt: string;
  readonly conflictCurrent?: unknown;
}

export type SendResult =
  | { readonly kind: "ok" }
  | { readonly kind: "retry" }
  | { readonly kind: "conflict"; readonly current: unknown }
  | { readonly kind: "rejected"; readonly httpStatus: number };

export interface FieldQueueStore {
  list(): Promise<FieldAction[]>;
  put(action: FieldAction): Promise<void>;
  remove(id: string): Promise<void>;
}

export interface FlushResult {
  readonly sent: number;
  readonly conflicted: number;
  readonly rejected: number;
  readonly deferred: number;
}

export interface EnqueueInput {
  readonly deviceId: string;
  readonly method: FieldActionMethod;
  readonly path: string;
  readonly body: unknown;
}

export interface FieldQueueOptions {
  readonly store: FieldQueueStore;
  readonly send: (action: FieldAction) => Promise<SendResult>;
  readonly newId?: () => string;
}

export interface FieldQueue {
  enqueue(input: EnqueueInput): Promise<FieldAction>;
  flush(): Promise<FlushResult>;
  listPending(): Promise<FieldAction[]>;
}

type OutcomeKey = keyof FlushResult;
interface StepOutcome {
  readonly counts: FlushResult;
  readonly stop: boolean;
}

const EMPTY_FLUSH: FlushResult = { sent: 0, conflicted: 0, rejected: 0, deferred: 0 };

function isPending(action: FieldAction): boolean {
  return action.status === "PENDING";
}

function countOutcome(counts: FlushResult, outcome: OutcomeKey): FlushResult {
  return { ...counts, [outcome]: counts[outcome] + 1 };
}

function withStatus(
  action: FieldAction,
  status: FieldActionStatus,
  conflictCurrent?: unknown,
): FieldAction {
  return { ...action, status, conflictCurrent };
}

export function createFieldQueue(options: FieldQueueOptions): FieldQueue {
  const { store, send } = options;
  const newId = options.newId ?? (() => crypto.randomUUID());

  async function applyResult(
    action: FieldAction,
    result: SendResult,
    counts: FlushResult,
  ): Promise<StepOutcome> {
    switch (result.kind) {
      case "ok":
        await store.remove(action.id);
        return { counts: countOutcome(counts, "sent"), stop: false };
      case "conflict":
        // Không tự gửi lại: người dùng quyết định trên màn hình xung đột.
        await store.put(withStatus(action, "CONFLICT", result.current));
        return { counts: countOutcome(counts, "conflicted"), stop: false };
      case "rejected":
        await store.put(withStatus(action, "REJECTED"));
        return { counts: countOutcome(counts, "rejected"), stop: false };
      case "retry":
        return { counts: countOutcome(counts, "deferred"), stop: true };
    }
  }

  async function sendOne(action: FieldAction, counts: FlushResult): Promise<StepOutcome> {
    try {
      return await applyResult(action, await send(action), counts);
    } catch {
      // Mất mạng hoặc máy chủ không phản hồi: giữ thao tác để gửi lại sau.
      return { counts: countOutcome(counts, "deferred"), stop: true };
    }
  }

  return {
    async enqueue(input: EnqueueInput): Promise<FieldAction> {
      const action: FieldAction = {
        id: newId(),
        deviceId: input.deviceId,
        method: input.method,
        path: input.path,
        body: input.body,
        status: "PENDING",
        createdAt: new Date().toISOString(),
      };
      await store.put(action);
      return action;
    },

    async flush(): Promise<FlushResult> {
      const pending = (await store.list()).filter(isPending);
      let counts = EMPTY_FLUSH;
      for (const action of pending) {
        const step = await sendOne(action, counts);
        counts = step.counts;
        if (step.stop) {
          break;
        }
      }
      return counts;
    },

    async listPending(): Promise<FieldAction[]> {
      return (await store.list()).filter(isPending);
    },
  };
}
