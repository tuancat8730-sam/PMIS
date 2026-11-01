import type { FieldAction, FieldQueueStore } from "./field-queue";

const DB_NAME = "pmis-field";
const DB_VERSION = 1;
const STORE_NAME = "actions";

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE_NAME, { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function runRequest<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Hàng đợi bền trong IndexedDB. Mọi truy cập đi qua hàm này nên lỗi được trả về
 * cho người gọi thay vì bị nuốt; trang sẽ báo người dùng khi không lưu được.
 */
export function createIndexedDbStore(): FieldQueueStore {
  async function withStore<T>(
    mode: IDBTransactionMode,
    run: (store: IDBObjectStore) => IDBRequest<T>,
  ): Promise<T> {
    const database = await openDatabase();
    try {
      const transaction = database.transaction(STORE_NAME, mode);
      return await runRequest(run(transaction.objectStore(STORE_NAME)));
    } finally {
      database.close();
    }
  }

  return {
    async list(): Promise<FieldAction[]> {
      const rows = await withStore<FieldAction[]>("readonly", (store) => store.getAll());
      return [...rows].sort((a, b) => a.createdAt.localeCompare(b.createdAt));
    },
    async put(action: FieldAction): Promise<void> {
      await withStore("readwrite", (store) => store.put(action));
    },
    async remove(id: string): Promise<void> {
      await withStore("readwrite", (store) => store.delete(id));
    },
  };
}
