/**
 * Главное PWA приложение
 */

class App {
    constructor() {
        this.currentView = 'transactions';
        this.referenceData = {};
    }

    async init() {
        console.log('🚀 Инициализация приложения...');
        
        // Инициализируем IndexedDB
        await localDB.init();
        
        // Проверяем авторизацию
        const token = localStorage.getItem('access_token');
        if (!token) {
            this.showScreen('login');
            this.setupLoginForm();
        } else {
            // Пробуем восстановить сессию
            try {
                await api.getMe();
                this.showScreen('main');
                await this.loadApp();
            } catch (error) {
                console.error('Сессия истекла:', error);
                this.showScreen('login');
                this.setupLoginForm();
            }
        }
    }

    showScreen(screenName) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(`${screenName}-screen`).classList.add('active');
    }

    // === Авторизация ===
    setupLoginForm() {
        const form = document.getElementById('login-form');
        const errorEl = document.getElementById('login-error');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorEl.classList.add('hidden');
            
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            
            try {
                await api.login(phone, password);
                this.showScreen('main');
                await this.loadApp();
            } catch (error) {
                errorEl.textContent = error.message;
                errorEl.classList.remove('hidden');
            }
        });
    }

    // === Загрузка приложения ===
    async loadApp() {
        console.log('📱 Загрузка приложения...');
        
        // Запускаем синхронизацию
        syncManager.startAutoSync(30);
        
        // Загружаем справочники из локальной БД
        await this.loadReferenceData();
        
        // Загружаем транзакции
        await this.loadTransactions();
        
        // Настраиваем UI
        this.setupNavigation();
        this.setupTransactionForm();
        this.setupButtons();
    }

    async loadReferenceData() {
        try {
            this.referenceData.categories = await localDB.getReferenceData('categories');
            this.referenceData.projects = await localDB.getReferenceData('projects');
            this.referenceData.stages = await localDB.getReferenceData('stages');
            this.referenceData.estimates = await localDB.getReferenceData('estimates');
            this.referenceData.contractors = await localDB.getReferenceData('contractors');
            
            this.populateSelects();
        } catch (error) {
            console.error('Ошибка загрузки справочников:', error);
        }
    }

    populateSelects() {
        // Категории
        const categorySelect = document.getElementById('tr-category');
        categorySelect.innerHTML = '<option value="">Выберите категорию</option>';
        this.referenceData.categories.forEach(cat => {
            categorySelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
        });

        // Проекты
        const projectSelect = document.getElementById('tr-project');
        const filterProject = document.getElementById('filter-project');
        
        [projectSelect, filterProject].forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">Все проекты</option>';
                this.referenceData.projects.forEach(proj => {
                    select.innerHTML += `<option value="${proj.id}">${proj.name}</option>`;
                });
            }
        });

        // Этапы
        const stageSelect = document.getElementById('tr-stage');
        stageSelect.innerHTML = '<option value="">Не указан</option>';
        this.referenceData.stages.forEach(stage => {
            stageSelect.innerHTML += `<option value="${stage.id}">${stage.name}</option>`;
        });

        // Сметы
        const estimateSelect = document.getElementById('tr-estimate');
        estimateSelect.innerHTML = '<option value="">Не указана</option>';
        this.referenceData.estimates.forEach(est => {
            estimateSelect.innerHTML += `<option value="${est.id}">${est.stage_name}</option>`;
        });

        // Контрагенты
        const contractorSelect = document.getElementById('tr-contractor');
        contractorSelect.innerHTML = '<option value="">Не указан</option>';
        this.referenceData.contractors.forEach(contr => {
            const name = contr.first_name && contr.last_name 
                ? `${contr.first_name} ${contr.last_name}` 
                : contr.phone;
            contractorSelect.innerHTML += `<option value="${contr.id}">${name}</option>`;
        });
    }

    // === Транзакции ===
    async loadTransactions() {
        try {
            const transactions = await localDB.getTransactions();
            this.renderTransactions(transactions);
        } catch (error) {
            console.error('Ошибка загрузки транзакций:', error);
        }
    }

    renderTransactions(transactions) {
        const listEl = document.getElementById('transactions-list');
        const emptyEl = document.getElementById('no-transactions');
        
        if (transactions.length === 0) {
            listEl.innerHTML = '';
            emptyEl.classList.remove('hidden');
            return;
        }
        
        emptyEl.classList.add('hidden');
        
        listEl.innerHTML = transactions.map(tx => {
            const typeClass = tx.transaction_type === 'income' ? 'income' : 'expense';
            const typeText = tx.transaction_type_display || tx.transaction_type;
            const statusEmoji = tx.sync_status === 'pending' ? '🟡' : '🟢';
            const statusText = tx.sync_status === 'pending' ? 'Не синхр.' : 'Синхр.';
            const amount = tx.transaction_type === 'income' ? `+${tx.amount}` : `-${tx.amount}`;
            const txId = tx.id || tx.local_id;
            const isPending = tx.sync_status === 'pending';
            
            return `
                <div class="transaction-item ${tx.sync_status}" data-tx-id="${txId}" data-tx-pending="${isPending}">
                    <button class="transaction-delete" data-tx-id="${txId}" data-tx-pending="${isPending}" title="Удалить">🗑️</button>
                    <div class="transaction-status">${statusEmoji} ${statusText}</div>
                    <div class="transaction-header">
                        <span class="transaction-type ${typeClass}">${typeText}</span>
                        <span class="transaction-amount">${amount} ₽</span>
                    </div>
                    <div class="transaction-details">
                        <div><strong>Категория:</strong> ${tx.category_name || 'Не указана'}</div>
                        ${tx.contractor_name ? `<div><strong>Контрагент:</strong> ${tx.contractor_name}</div>` : ''}
                        ${tx.description ? `<div><strong>Описание:</strong> ${tx.description}</div>` : ''}
                        <div><strong>Дата:</strong> ${new Date(tx.date).toLocaleDateString('ru-RU')}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Добавляем обработчики удаления
        listEl.querySelectorAll('.transaction-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const txId = btn.dataset.txId;
                const isPending = btn.dataset.txPending === 'true';
                this.showDeleteConfirm(txId, isPending);
            });
        });
    }

    // === Создание транзакции ===
    setupTransactionForm() {
        const form = document.getElementById('transaction-form');
        const errorEl = document.getElementById('form-error');
        const successEl = document.getElementById('form-success');
        
        // Устанавливаем сегодняшнюю дату по умолчанию
        document.getElementById('tr-date').valueAsDate = new Date();
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorEl.classList.add('hidden');
            successEl.classList.add('hidden');
            
            const formData = new FormData(form);
            const data = {
                date: formData.get('date'),
                transaction_type: formData.get('transaction_type'),
                amount: parseFloat(formData.get('amount')),
                category: parseInt(formData.get('category')),
                contractor: formData.get('contractor') ? parseInt(formData.get('contractor')) : null,
                stage: formData.get('stage') ? parseInt(formData.get('stage')) : null,
                estimate: formData.get('estimate') ? parseInt(formData.get('estimate')) : null,
                description: formData.get('description') || '',
            };
            
            try {
                // Проверяем соединение
                const isOnline = await api.checkConnection();
                
                if (isOnline) {
                    // Отправляем сразу на сервер
                    const created = await api.createTransaction(data);
                    await localDB.addTransaction(created);
                    successEl.textContent = '✅ Транзакция создана и синхронизирована';
                    successEl.classList.remove('hidden');
                } else {
                    // Сохраняем локально
                    try {
                        const localId = await localDB.addPendingTransaction(data);
                        successEl.textContent = `🟡 Транзакция сохранена локально (будет синхронизирована при восстановлении связи)`;
                        successEl.classList.remove('hidden');
                    } catch (dbError) {
                        console.error('IndexedDB error:', dbError);
                        throw new Error('Не удалось сохранить транзакцию локально. Проверьте доступность хранилища.');
                    }
                }
                
                form.reset();
                document.getElementById('tr-date').valueAsDate = new Date();
                
                // Обновляем список транзакций
                await this.loadTransactions();
                
                // Автоматически переключаемся на список через 2 секунды
                setTimeout(() => {
                    this.switchView('transactions');
                }, 2000);
                
            } catch (error) {
                console.error('Ошибка создания транзакции:', error);
                // Показываем ошибку в попапе
                this.showError(`❌ Ошибка создания транзакции: ${error.message || 'Неизвестная ошибка'}`);
                // Также показываем внизу формы для совместимости
                errorEl.textContent = `❌ Ошибка: ${error.message || 'Неизвестная ошибка'}`;
                errorEl.classList.remove('hidden');
            }
        });
    }

    // === Навигация ===
    setupNavigation() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                this.switchView(view);
            });
        });
    }

    switchView(viewName) {
        // Обновляем кнопки
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === viewName);
        });
        
        // Обновляем виды
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');
        
        this.currentView = viewName;
    }

    // === Кнопки ===
    setupButtons() {
        // Кнопка синхронизации
        document.getElementById('sync-btn').addEventListener('click', async () => {
            await syncManager.syncAll();
        });

        // Кнопка выхода
        document.getElementById('logout-btn').addEventListener('click', async () => {
            if (confirm('Выйти из приложения?')) {
                await api.logout();
                syncManager.stopAutoSync();
                location.reload();
            }
        });

        // Фильтр по проектам
        document.getElementById('filter-project').addEventListener('change', async (e) => {
            await this.loadTransactions();
        });
        
        // Модальные окна
        this.setupModals();
    }
    
    // === Модальные окна ===
    setupModals() {
        // Окно ошибок
        const errorModal = document.getElementById('error-modal');
        const errorClose = document.getElementById('error-modal-close');
        const errorOk = document.getElementById('error-modal-ok');
        
        [errorClose, errorOk].forEach(btn => {
            btn.addEventListener('click', () => {
                errorModal.classList.add('hidden');
            });
        });
        
        // Окно удаления
        const deleteModal = document.getElementById('delete-modal');
        const deleteClose = document.getElementById('delete-modal-close');
        const deleteCancel = document.getElementById('delete-modal-cancel');
        const deleteConfirm = document.getElementById('delete-modal-confirm');
        
        [deleteClose, deleteCancel].forEach(btn => {
            btn.addEventListener('click', () => {
                deleteModal.classList.add('hidden');
            });
        });
        
        deleteConfirm.addEventListener('click', async () => {
            const txId = deleteConfirm.dataset.txId;
            const isPending = deleteConfirm.dataset.txPending === 'true';
            await this.deleteTransaction(txId, isPending);
            deleteModal.classList.add('hidden');
        });
    }
    
    showError(message) {
        const modal = document.getElementById('error-modal');
        const messageEl = document.getElementById('error-modal-message');
        messageEl.textContent = message;
        modal.classList.remove('hidden');
    }
    
    showDeleteConfirm(txId, isPending) {
        const modal = document.getElementById('delete-modal');
        const confirmBtn = document.getElementById('delete-modal-confirm');
        confirmBtn.dataset.txId = txId;
        confirmBtn.dataset.txPending = isPending;
        modal.classList.remove('hidden');
    }
    
    async deleteTransaction(txId, isPending) {
        try {
            if (isPending) {
                // Удаляем из локальной БД (pending_transactions)
                await localDB.deletePendingTransaction(parseInt(txId));
                console.log(`✅ Локальная транзакция ${txId} удалена`);
            } else {
                // Удаляем через API
                try {
                    await api.request(`/transactions/${txId}/`, { method: 'DELETE' });
                    console.log(`✅ Транзакция ${txId} удалена с сервера`);
                    
                    // Также удаляем из локальной БД
                    const tx = localDB.db.transaction('transactions', 'readwrite');
                    await localDB._promisifyRequest(tx.objectStore('transactions').delete(parseInt(txId)));
                } catch (error) {
                    // Если нет соединения, удаляем локально
                    if (!await api.checkConnection()) {
                        const tx = localDB.db.transaction('transactions', 'readwrite');
                        await localDB._promisifyRequest(tx.objectStore('transactions').delete(parseInt(txId)));
                        console.log(`✅ Транзакция ${txId} удалена локально (оффлайн)`);
                    } else {
                        throw error;
                    }
                }
            }
            
            // Обновляем список
            await this.loadTransactions();
            
            // Показываем успех
            this.showError('✅ Транзакция успешно удалена');
            setTimeout(() => {
                document.getElementById('error-modal').classList.add('hidden');
            }, 2000);
        } catch (error) {
            console.error('Ошибка удаления:', error);
            this.showError(`❌ Ошибка удаления: ${error.message || 'Неизвестная ошибка'}`);
        }
    }
}

// Инициализация при загрузке
window.app = new App();

document.addEventListener('DOMContentLoaded', () => {
    window.app.init();
});


