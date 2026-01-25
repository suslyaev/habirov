/**
 * IndexedDB для локального хранения транзакций и справочников
 */

const DB_NAME = 'HabirovDB';
const DB_VERSION = 1;

class LocalDB {
    constructor() {
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Транзакции (синхронизированные)
                if (!db.objectStoreNames.contains('transactions')) {
                    const txStore = db.createObjectStore('transactions', { keyPath: 'id' });
                    txStore.createIndex('date', 'date', { unique: false });
                    txStore.createIndex('sync_status', 'sync_status', { unique: false });
                }

                // Несинхронизированные транзакции (локальные)
                if (!db.objectStoreNames.contains('pending_transactions')) {
                    const pendingStore = db.createObjectStore('pending_transactions', { 
                        keyPath: 'local_id', 
                        autoIncrement: true 
                    });
                    pendingStore.createIndex('created_at', 'created_at', { unique: false });
                }

                // Справочники (кэш)
                ['categories', 'projects', 'stages', 'estimates', 'contractors'].forEach(storeName => {
                    if (!db.objectStoreNames.contains(storeName)) {
                        db.createObjectStore(storeName, { keyPath: 'id' });
                    }
                });
            };
        });
    }

    // === Транзакции ===
    async getTransactions() {
        const tx = this.db.transaction(['transactions', 'pending_transactions'], 'readonly');
        
        // Синхронизированные
        const syncedTx = await this._getAllFromStore(tx.objectStore('transactions'));
        
        // Несинхронизированные
        const pendingTx = await this._getAllFromStore(tx.objectStore('pending_transactions'));
        
        // Объединяем и сортируем
        const all = [
            ...syncedTx.map(t => ({ ...t, sync_status: 'synced' })),
            ...pendingTx.map(t => ({ ...t, sync_status: 'pending' }))
        ];
        
        return all.sort((a, b) => new Date(b.date) - new Date(a.date));
    }

    async addTransaction(transaction) {
        const tx = this.db.transaction('transactions', 'readwrite');
        const store = tx.objectStore('transactions');
        await this._promisifyRequest(store.put(transaction));
    }

    async addPendingTransaction(transaction) {
        // Убираем id если есть (он будет сгенерирован автоматически)
        const { id, ...dataToSave } = transaction;
        
        // Добавляем метаданные
        dataToSave.created_at = new Date().toISOString();
        dataToSave.sync_status = 'pending';
        
        const tx = this.db.transaction('pending_transactions', 'readwrite');
        const store = tx.objectStore('pending_transactions');
        const request = store.add(dataToSave);
        
        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result); // Возвращаем local_id
            request.onerror = () => {
                console.error('IndexedDB error:', request.error);
                reject(request.error);
            };
        });
    }

    async getPendingTransactions() {
        const tx = this.db.transaction('pending_transactions', 'readonly');
        return await this._getAllFromStore(tx.objectStore('pending_transactions'));
    }

    async deletePendingTransaction(localId) {
        const tx = this.db.transaction('pending_transactions', 'readwrite');
        await this._promisifyRequest(tx.objectStore('pending_transactions').delete(localId));
    }

    async clearPendingTransactions() {
        const tx = this.db.transaction('pending_transactions', 'readwrite');
        await this._promisifyRequest(tx.objectStore('pending_transactions').clear());
    }

    // === Справочники ===
    async saveReferenceData(storeName, data) {
        const tx = this.db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);
        await this._promisifyRequest(store.clear());
        
        for (const item of data) {
            await this._promisifyRequest(store.put(item));
        }
    }

    async getReferenceData(storeName) {
        const tx = this.db.transaction(storeName, 'readonly');
        return await this._getAllFromStore(tx.objectStore(storeName));
    }

    // === Утилиты ===
    _getAllFromStore(store) {
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    _promisifyRequest(request) {
        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
}

// Глобальный экземпляр
const localDB = new LocalDB();


