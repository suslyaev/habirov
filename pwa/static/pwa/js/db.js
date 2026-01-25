/**
 * IndexedDB для локального хранения транзакций и справочников
 */

const DB_NAME = 'HabirovDB';
const DB_VERSION = 4; // Увеличена версия для добавления objects в справочники

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
                const oldVersion = event.oldVersion;

                // Транзакции (синхронизированные)
                if (!db.objectStoreNames.contains('transactions')) {
                    const txStore = db.createObjectStore('transactions', { keyPath: 'id' });
                    txStore.createIndex('date', 'date', { unique: false });
                    txStore.createIndex('sync_status', 'sync_status', { unique: false });
                }

                // Несинхронизированные транзакции (локальные)
                // Если обновляем с версии 2 или меньше, пересоздаем структуру
                if (oldVersion < 3 && db.objectStoreNames.contains('pending_transactions')) {
                    db.deleteObjectStore('pending_transactions');
                    console.log('🔄 Пересоздание pending_transactions для версии 3');
                }
                
                if (!db.objectStoreNames.contains('pending_transactions')) {
                    const pendingStore = db.createObjectStore('pending_transactions', { 
                        keyPath: 'local_id'
                    });
                    pendingStore.createIndex('created_at', 'created_at', { unique: false });
                    console.log('✅ Создан pending_transactions с keyPath: local_id');
                }

                // Справочники (кэш)
                ['categories', 'projects', 'objects', 'stages', 'estimates', 'contractors'].forEach(storeName => {
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
        // Генерируем уникальный local_id (timestamp + случайное число)
        const localId = `pending_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        // Создаем чистый объект только с нужными полями
        // IndexedDB не может сохранить undefined, поэтому используем только определенные значения
        const dataToSave = {
            local_id: localId,
            date: String(transaction.date || ''),
            transaction_type: String(transaction.transaction_type || ''),
            amount: parseFloat(transaction.amount) || 0,
            category: parseInt(transaction.category) || 0,
            description: String(transaction.description || ''),
            created_at: new Date().toISOString(),
            sync_status: 'pending'
        };
        
        // Добавляем опциональные поля только если они есть и не пустые
        if (transaction.contractor && transaction.contractor !== '' && transaction.contractor !== null) {
            dataToSave.contractor = parseInt(transaction.contractor);
        }
        if (transaction.stage && transaction.stage !== '' && transaction.stage !== null) {
            dataToSave.stage = parseInt(transaction.stage);
        }
        if (transaction.estimate && transaction.estimate !== '' && transaction.estimate !== null) {
            dataToSave.estimate = parseInt(transaction.estimate);
        }
        
        console.log('💾 Сохранение в IndexedDB:', dataToSave);
        
        // Проверяем что local_id установлен
        if (!dataToSave.local_id) {
            throw new Error('local_id не установлен перед сохранением');
        }
        
        const dbTx = this.db.transaction('pending_transactions', 'readwrite');
        const store = dbTx.objectStore('pending_transactions');
        const request = store.add(dataToSave);
        
        return new Promise((resolve, reject) => {
            request.onsuccess = () => {
                console.log('✅ Транзакция сохранена в IndexedDB:', localId);
                resolve(localId);
            };
            request.onerror = (event) => {
                const error = event.target.error;
                console.error('❌ IndexedDB error:', error);
                console.error('Данные которые пытались сохранить:', dataToSave);
                console.error('local_id:', dataToSave.local_id);
                reject(new Error(`Ошибка сохранения в IndexedDB: ${error.message || error.name || 'Неизвестная ошибка'}`));
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


