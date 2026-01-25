/**
 * Модуль синхронизации локальных данных с сервером
 */

class SyncManager {
    constructor() {
        this.isSyncing = false;
        this.syncInterval = null;
    }

    /**
     * Запустить автоматическую синхронизацию
     */
    startAutoSync(intervalSeconds = 30) {
        this.stopAutoSync();
        this.syncInterval = setInterval(() => {
            this.syncAll();
        }, intervalSeconds * 1000);
        
        // Первая синхронизация сразу
        this.syncAll();
    }

    stopAutoSync() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }

    /**
     * Полная синхронизация всех данных
     */
    async syncAll() {
        if (this.isSyncing) return;
        
        this.isSyncing = true;
        this.updateSyncStatus('syncing', '🔄 Синхронизация...');

        try {
            // Проверяем соединение
            const isOnline = await api.checkConnection();
            
            if (!isOnline) {
                this.updateSyncStatus('offline', '📵 Оффлайн');
                this.isSyncing = false;
                return;
            }

            // 1. Загружаем справочники с сервера
            await this.syncReferenceData();

            // 2. Отправляем несинхронизированные транзакции
            await this.syncPendingTransactions();

            // 3. Загружаем транзакции с сервера
            await this.syncTransactions();

            this.updateSyncStatus('synced', '✅ Синхронизировано');
            
            // Обновляем UI
            if (window.app) {
                await window.app.loadReferenceData(); // Обновляем справочники
                await window.app.loadTransactions(); // Обновляем транзакции
            }
        } catch (error) {
            console.error('Sync error:', error);
            this.updateSyncStatus('error', '⚠️ Ошибка синхронизации');
        } finally {
            this.isSyncing = false;
        }
    }

    /**
     * Синхронизация справочников
     */
    async syncReferenceData() {
        try {
            const [categories, projects, objects, stages, estimates, contractors] = await Promise.all([
                api.getCategories(),
                api.getProjects(),
                api.getObjects(),
                api.getStages(),
                api.getEstimates(),
                api.getContractors(),
            ]);

            await Promise.all([
                localDB.saveReferenceData('categories', categories.results || categories),
                localDB.saveReferenceData('projects', projects.results || projects),
                localDB.saveReferenceData('objects', objects.results || objects),
                localDB.saveReferenceData('stages', stages.results || stages),
                localDB.saveReferenceData('estimates', estimates.results || estimates),
                localDB.saveReferenceData('contractors', contractors.results || contractors),
            ]);

            console.log('✅ Справочники синхронизированы');
        } catch (error) {
            console.error('Ошибка синхронизации справочников:', error);
            throw error;
        }
    }

    /**
     * Отправка несинхронизированных транзакций на сервер
     */
    async syncPendingTransactions() {
        const pending = await localDB.getPendingTransactions();
        
        if (pending.length === 0) {
            console.log('Нет несинхронизированных транзакций');
            return;
        }

        console.log(`📤 Отправка ${pending.length} транзакций...`);

        for (const transaction of pending) {
            try {
                // Убираем локальные поля
                const { local_id, created_at, sync_status, ...dataToSend } = transaction;
                
                // Отправляем на сервер
                const created = await api.createTransaction(dataToSend);
                
                // Сохраняем синхронизированную транзакцию
                await localDB.addTransaction(created);
                
                // Удаляем из pending
                await localDB.deletePendingTransaction(local_id);
                
                console.log(`✅ Транзакция ${local_id} синхронизирована (ID: ${created.id})`);
            } catch (error) {
                console.error(`❌ Ошибка синхронизации транзакции ${transaction.local_id}:`, error);
            }
        }
    }

    /**
     * Загрузка транзакций с сервера
     */
    async syncTransactions() {
        try {
            // Загружаем все транзакции (может быть несколько страниц)
            let allTransactions = [];
            let nextUrl = null;
            let page = 1;
            
            do {
                const params = { page_size: 100, page: page };
                const response = await api.getTransactions(params);
                
                const transactions = response.results || response;
                allTransactions = allTransactions.concat(transactions);
                
                nextUrl = response.next;
                page++;
                
                // Ограничим максимум 10 страниц (1000 транзакций)
                if (page > 10) break;
            } while (nextUrl);
            
            // Очищаем старые синхронизированные транзакции
            const tx = localDB.db.transaction('transactions', 'readwrite');
            await localDB._promisifyRequest(tx.objectStore('transactions').clear());
            
            // Сохраняем новые (используем addTransaction для нормализации данных)
            for (const transaction of allTransactions) {
                await localDB.addTransaction(transaction);
            }
            
            console.log(`✅ Загружено ${allTransactions.length} транзакций с сервера`);
        } catch (error) {
            console.error('Ошибка загрузки транзакций:', error);
            throw error;
        }
    }

    /**
     * Обновление статуса синхронизации в UI
     */
    updateSyncStatus(statusClass, text) {
        const statusEl = document.getElementById('sync-status');
        if (statusEl) {
            statusEl.className = `sync-status ${statusClass}`;
            statusEl.textContent = text;
        }

        // Показать/скрыть оффлайн баннер
        const offlineBanner = document.getElementById('offline-banner');
        if (offlineBanner) {
            if (statusClass === 'offline') {
                offlineBanner.classList.remove('hidden');
            } else {
                offlineBanner.classList.add('hidden');
            }
        }
    }
}

// Глобальный экземпляр
const syncManager = new SyncManager();

// Отслеживание онлайн/оффлайн статуса
window.addEventListener('online', () => {
    console.log('📶 Соединение восстановлено');
    syncManager.syncAll();
});

window.addEventListener('offline', () => {
    console.log('📵 Соединение потеряно');
    syncManager.updateSyncStatus('offline', '📵 Оффлайн');
});


