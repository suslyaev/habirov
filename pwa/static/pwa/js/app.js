/**
 * Главное PWA приложение
 */

class App {
    constructor() {
        this.currentView = 'transactions';
        this.referenceData = {};
        this.pagination = {
            currentPage: 1,
            pageSize: 20,
            totalItems: 0,
            filteredItems: []
        };
        this.currentFilter = {
            project: null
        };
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
        this.setupTransactionCardForm();
        this.setupButtons();
    }

    async loadReferenceData() {
        try {
            this.referenceData.categories = await localDB.getReferenceData('categories');
            this.referenceData.projects = await localDB.getReferenceData('projects');
            this.referenceData.objects = await localDB.getReferenceData('objects');
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
        const cardContractorSelect = document.getElementById('card-contractor');
        [contractorSelect, cardContractorSelect].forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">Не указан</option>';
                this.referenceData.contractors.forEach(contr => {
                    const name = contr.first_name && contr.last_name 
                        ? `${contr.first_name} ${contr.last_name}` 
                        : contr.phone;
                    select.innerHTML += `<option value="${contr.id}">${name}</option>`;
                });
            }
        });
        
        // Категории для карточки
        const cardCategorySelect = document.getElementById('card-category');
        if (cardCategorySelect) {
            cardCategorySelect.innerHTML = '<option value="">Выберите категорию</option>';
            this.referenceData.categories.forEach(cat => {
                cardCategorySelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
            });
        }
        
        // Проекты для карточки
        const cardProjectSelect = document.getElementById('card-project');
        if (cardProjectSelect) {
            cardProjectSelect.innerHTML = '<option value="">Не указан</option>';
            this.referenceData.projects.forEach(proj => {
                cardProjectSelect.innerHTML += `<option value="${proj.id}">${proj.name}</option>`;
            });
        }
        
        // Настраиваем зависимые списки
        this.setupDependentSelects();
    }
    
    setupDependentSelects() {
        // Для формы создания
        const createProject = document.getElementById('tr-project');
        const createStage = document.getElementById('tr-stage');
        const createEstimate = document.getElementById('tr-estimate');
        
        if (createProject) {
            createProject.addEventListener('change', () => {
                this.updateStagesSelect(createProject.value, createStage);
                createEstimate.innerHTML = '<option value="">Не указана</option>';
            });
        }
        
        if (createStage) {
            createStage.addEventListener('change', () => {
                this.updateEstimatesSelect(createStage.value, createEstimate);
            });
        }
        
        // Для карточки
        const cardProject = document.getElementById('card-project');
        const cardStage = document.getElementById('card-stage');
        const cardEstimate = document.getElementById('card-estimate');
        
        if (cardProject) {
            cardProject.addEventListener('change', () => {
                this.updateStagesSelect(cardProject.value, cardStage);
                cardEstimate.innerHTML = '<option value="">Не указана</option>';
            });
        }
        
        if (cardStage) {
            cardStage.addEventListener('change', () => {
                this.updateEstimatesSelect(cardStage.value, cardEstimate);
            });
        }
    }
    
    updateStagesSelect(projectId, stageSelect) {
        if (!stageSelect) return;
        
        stageSelect.innerHTML = '<option value="">Не указан</option>';
        
        if (!projectId) {
            return;
        }
        
        const projectIdNum = parseInt(projectId);
        const projectObjects = (this.referenceData.objects || []).filter(o => o.project === projectIdNum);
        const projectObjectIds = projectObjects.map(o => o.id);
        const projectStages = (this.referenceData.stages || []).filter(s => projectObjectIds.includes(s.object));
        
        projectStages.forEach(stage => {
            stageSelect.innerHTML += `<option value="${stage.id}">${stage.name}</option>`;
        });
    }
    
    updateEstimatesSelect(stageId, estimateSelect) {
        if (!estimateSelect) return;
        
        estimateSelect.innerHTML = '<option value="">Не указана</option>';
        
        if (!stageId) {
            return;
        }
        
        const stageIdNum = parseInt(stageId);
        const stageEstimates = (this.referenceData.estimates || []).filter(e => e.stage === stageIdNum);
        
        stageEstimates.forEach(est => {
            estimateSelect.innerHTML += `<option value="${est.id}">${est.stage_name || est.id}</option>`;
        });
    }

    // === Транзакции ===
    async loadTransactions() {
        try {
            const allTransactions = await localDB.getTransactions();
            
            // Сортируем по дате (последние сверху)
            allTransactions.sort((a, b) => {
                const dateA = new Date(a.date || a.created_at);
                const dateB = new Date(b.date || b.created_at);
                return dateB - dateA; // По убыванию (новые сверху)
            });
            
            // Применяем фильтры
            let filtered = this.applyFilters(allTransactions);
            
            // Сохраняем отфильтрованные транзакции
            this.pagination.filteredItems = filtered;
            this.pagination.totalItems = filtered.length;
            
            // Применяем пагинацию
            const paginated = this.applyPagination(filtered);
            
            // Обновляем UI пагинации
            this.updatePaginationUI();
            
            // Рендерим транзакции
            this.renderTransactions(paginated);
        } catch (error) {
            console.error('Ошибка загрузки транзакций:', error);
        }
    }
    
    applyFilters(transactions) {
        let filtered = [...transactions];
        
        // Фильтр по проекту
        if (this.currentFilter.project) {
            const projectId = parseInt(this.currentFilter.project);
            
            filtered = filtered.filter(tx => {
                // Если есть project_id в транзакции (из API)
                if (tx.project_id === projectId) {
                    return true;
                }
                
                // Если project_id нет, ищем через stage или estimate
                if (tx.stage) {
                    const stage = (this.referenceData.stages || []).find(s => s.id === tx.stage);
                    if (stage) {
                        const object = (this.referenceData.objects || []).find(o => o.id === stage.object);
                        if (object && object.project === projectId) {
                            return true;
                        }
                    }
                }
                if (tx.estimate) {
                    const estimate = (this.referenceData.estimates || []).find(e => e.id === tx.estimate);
                    if (estimate && estimate.stage) {
                        const stage = (this.referenceData.stages || []).find(s => s.id === estimate.stage);
                        if (stage) {
                            const object = (this.referenceData.objects || []).find(o => o.id === stage.object);
                            if (object && object.project === projectId) {
                                return true;
                            }
                        }
                    }
                }
                return false;
            });
        }
        
        return filtered;
    }
    
    applyPagination(transactions) {
        const start = (this.pagination.currentPage - 1) * this.pagination.pageSize;
        const end = start + this.pagination.pageSize;
        return transactions.slice(start, end);
    }
    
    updatePaginationUI() {
        const infoEl = document.getElementById('pagination-info');
        const prevBtn = document.getElementById('pagination-prev');
        const nextBtn = document.getElementById('pagination-next');
        const totalPages = Math.ceil(this.pagination.totalItems / this.pagination.pageSize);
        
        if (infoEl) {
            if (this.pagination.totalItems === 0) {
                infoEl.textContent = 'Нет транзакций';
            } else {
                const start = (this.pagination.currentPage - 1) * this.pagination.pageSize + 1;
                const end = Math.min(this.pagination.currentPage * this.pagination.pageSize, this.pagination.totalItems);
                infoEl.textContent = `Показано ${start}-${end} из ${this.pagination.totalItems}`;
            }
        }
        
        if (prevBtn) {
            prevBtn.disabled = this.pagination.currentPage <= 1;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.pagination.currentPage >= totalPages || totalPages === 0;
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
                <div class="transaction-item ${tx.sync_status}" data-tx-id="${txId}" data-tx-pending="${isPending}" data-tx-data='${JSON.stringify(tx).replace(/'/g, "&apos;")}'>
                    <button class="transaction-delete" data-tx-id="${txId}" data-tx-pending="${isPending}" title="Удалить">🗑️</button>
                    <div class="transaction-status">${statusEmoji} ${statusText}</div>
                    <div class="transaction-header">
                        <span class="transaction-type ${typeClass}">${typeText}</span>
                        <span class="transaction-amount">${amount} ₽</span>
                    </div>
                    <div class="transaction-details">
                        <div><strong>Категория:</strong> ${tx.category_name || 'Не указана'}</div>
                        ${tx.project_name ? `<div><strong>Проект:</strong> ${tx.project_name}</div>` : ''}
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
        
        // Добавляем обработчики клика на транзакцию
        listEl.querySelectorAll('.transaction-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // Игнорируем клик на кнопку удаления
                if (e.target.closest('.transaction-delete')) {
                    return;
                }
                const txData = JSON.parse(item.dataset.txData || '{}');
                this.openTransactionCard(txData);
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
            
            // Валидация обязательных полей
            const amount = parseFloat(formData.get('amount'));
            const category = formData.get('category');
            
            if (!amount || amount <= 0) {
                throw new Error('Сумма должна быть больше нуля');
            }
            
            if (!category) {
                throw new Error('Выберите категорию');
            }
            
            // Собираем данные с валидацией
            const data = {
                date: formData.get('date'),
                transaction_type: formData.get('transaction_type'),
                amount: amount,
                category: parseInt(category),
                description: (formData.get('description') || '').trim(),
            };
            
            // Добавляем опциональные поля только если они заполнены
            const contractor = formData.get('contractor');
            if (contractor && contractor !== '') {
                data.contractor = parseInt(contractor);
            }
            
            const stage = formData.get('stage');
            if (stage && stage !== '') {
                data.stage = parseInt(stage);
            }
            
            const estimate = formData.get('estimate');
            if (estimate && estimate !== '') {
                data.estimate = parseInt(estimate);
            }
            
            console.log('📝 Данные для сохранения:', data);
            
            try {
                // Проверяем соединение
                const isOnline = await api.checkConnection();
                
                if (isOnline) {
                    // Отправляем сразу на сервер
                    const created = await api.createTransaction(data);
                    console.log('📥 Получена транзакция с сервера:', created);
                    
                    if (!created || !created.id) {
                        console.error('❌ API вернул пустой ответ или транзакция без ID');
                        errorEl.textContent = '❌ Ошибка: сервер не вернул данные транзакции';
                        errorEl.classList.remove('hidden');
                        this.showError('Сервер не вернул данные созданной транзакции. Попробуйте обновить список.');
                        return;
                    }
                    
                    try {
                        await localDB.addTransaction(created);
                        console.log('✅ Транзакция сохранена в IndexedDB');
                    } catch (dbError) {
                        console.error('❌ Ошибка сохранения в IndexedDB:', dbError);
                        console.error('Данные транзакции:', created);
                        // Показываем ошибку, но не блокируем успех создания
                        this.showError(`Транзакция создана на сервере, но не сохранена локально: ${dbError.message}`);
                    }
                    successEl.textContent = '✅ Транзакция создана и синхронизирована';
                    successEl.classList.remove('hidden');
                } else {
                    // Сохраняем локально
                    let localId = null;
                    try {
                        localId = await localDB.addPendingTransaction(data);
                        console.log('✅ Транзакция успешно сохранена локально:', localId);
                    } catch (dbError) {
                        console.error('❌ IndexedDB error при сохранении:', dbError);
                        
                        // Проверяем, может транзакция все-таки сохранилась
                        try {
                            const pending = await localDB.getPendingTransactions();
                            const saved = pending.find(t => 
                                t.date === data.date && 
                                t.amount === data.amount && 
                                t.transaction_type === data.transaction_type
                            );
                            
                            if (saved) {
                                console.log('✅ Транзакция найдена в БД после ошибки, игнорируем ошибку');
                                localId = saved.local_id;
                            } else {
                                throw new Error(`Не удалось сохранить транзакцию: ${dbError.message || dbError.name || 'Неизвестная ошибка IndexedDB'}`);
                            }
                        } catch (checkError) {
                            throw new Error(`Не удалось сохранить транзакцию локально: ${dbError.message || dbError.name || 'Неизвестная ошибка'}`);
                        }
                    }
                    
                    if (localId) {
                        successEl.textContent = `🟡 Транзакция сохранена локально (будет синхронизирована при восстановлении связи)`;
                        successEl.classList.remove('hidden');
                    }
                }
                
                // Если дошли сюда, значит транзакция создана успешно
                form.reset();
                document.getElementById('tr-date').valueAsDate = new Date();
                
                // Обновляем список транзакций
                await this.loadTransactions();
                
                // Автоматически переключаемся на список через 2 секунды
                setTimeout(() => {
                    this.switchView('transactions');
                }, 2000);
                
            } catch (error) {
                console.error('❌ Ошибка создания транзакции:', error);
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
    
    // === Карточка транзакции ===
    openTransactionCard(txData) {
        // Заполняем форму данными транзакции
        document.getElementById('card-tx-id').value = txData.id || '';
        document.getElementById('card-tx-pending').value = txData.sync_status === 'pending' ? 'true' : 'false';
        document.getElementById('card-date').value = txData.date ? txData.date.split('T')[0] : '';
        document.getElementById('card-type').value = txData.transaction_type || 'expense';
        document.getElementById('card-amount').value = txData.amount || '';
        document.getElementById('card-category').value = txData.category || '';
        document.getElementById('card-contractor').value = txData.contractor || '';
        document.getElementById('card-description').value = txData.description || '';
        
        // Устанавливаем проект, этап и смету
        const cardProject = document.getElementById('card-project');
        const cardStage = document.getElementById('card-stage');
        const cardEstimate = document.getElementById('card-estimate');
        
        // Если есть project_id, устанавливаем проект
        if (txData.project_id) {
            cardProject.value = txData.project_id;
            // Обновляем этапы для этого проекта
            this.updateStagesSelect(txData.project_id, cardStage);
            
            // Если есть stage, устанавливаем его
            if (txData.stage) {
                setTimeout(() => {
                    cardStage.value = txData.stage;
                    // Обновляем сметы для этого этапа
                    this.updateEstimatesSelect(txData.stage, cardEstimate);
                    
                    // Если есть estimate, устанавливаем его
                    if (txData.estimate) {
                        setTimeout(() => {
                            cardEstimate.value = txData.estimate;
                        }, 100);
                    }
                }, 100);
            }
        } else {
            // Если нет project_id, но есть stage, пытаемся найти проект через stage
            if (txData.stage) {
                const stage = (this.referenceData.stages || []).find(s => s.id === txData.stage);
                if (stage) {
                    const object = (this.referenceData.objects || []).find(o => o.id === stage.object);
                    if (object) {
                        cardProject.value = object.project;
                        this.updateStagesSelect(object.project, cardStage);
                        setTimeout(() => {
                            cardStage.value = txData.stage;
                            this.updateEstimatesSelect(txData.stage, cardEstimate);
                            if (txData.estimate) {
                                setTimeout(() => {
                                    cardEstimate.value = txData.estimate;
                                }, 100);
                            }
                        }, 100);
                    }
                }
            }
        }
        
        // Переключаемся на вид карточки
        this.switchView('transaction-card');
    }
    
    setupTransactionCardForm() {
        const form = document.getElementById('transaction-card-form');
        const errorEl = document.getElementById('card-form-error');
        const successEl = document.getElementById('card-form-success');
        const backBtn = document.getElementById('card-back-btn');
        
        // Кнопка "Назад"
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.switchView('transactions');
                form.reset();
                errorEl.classList.add('hidden');
                successEl.classList.add('hidden');
            });
        }
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorEl.classList.add('hidden');
            successEl.classList.add('hidden');
            
            const txId = document.getElementById('card-tx-id').value;
            const isPending = document.getElementById('card-tx-pending').value === 'true';
            
            const data = {
                date: document.getElementById('card-date').value,
                transaction_type: document.getElementById('card-type').value,
                amount: parseFloat(document.getElementById('card-amount').value),
                category: parseInt(document.getElementById('card-category').value),
                description: document.getElementById('card-description').value || '',
            };
            
            const contractor = document.getElementById('card-contractor').value;
            if (contractor && contractor !== '') {
                data.contractor = parseInt(contractor);
            }
            
            const stage = document.getElementById('card-stage').value;
            if (stage && stage !== '') {
                data.stage = parseInt(stage);
            }
            
            const estimate = document.getElementById('card-estimate').value;
            if (estimate && estimate !== '') {
                data.estimate = parseInt(estimate);
            }
            
            try {
                const isOnline = await api.checkConnection();
                
                if (isOnline) {
                    // Обновляем на сервере
                    if (isPending) {
                        // Если это pending транзакция, создаем новую
                        const created = await api.createTransaction(data);
                        // Удаляем старую pending
                        await localDB.deletePendingTransaction(txId);
                        // Добавляем новую синхронизированную
                        await localDB.addTransaction(created);
                        successEl.textContent = '✅ Транзакция обновлена и синхронизирована';
                    } else {
                        // Обновляем существующую транзакцию
                        const updated = await api.updateTransaction(txId, data);
                        // Обновляем в локальной БД
                        await localDB.addTransaction(updated);
                        successEl.textContent = '✅ Изменения сохранены и синхронизированы';
                    }
                } else {
                    // Сохраняем локально
                    if (isPending) {
                        // Обновляем pending транзакцию
                        await localDB.deletePendingTransaction(txId);
                        const newLocalId = await localDB.addPendingTransaction(data);
                        successEl.textContent = '✅ Изменения сохранены локально';
                    } else {
                        // Для синхронизированных транзакций в оффлайне создаем новую pending
                        await localDB.addPendingTransaction(data);
                        successEl.textContent = '✅ Изменения сохранены локально (будут синхронизированы при подключении)';
                    }
                }
                
                successEl.classList.remove('hidden');
                
                // Обновляем список транзакций
                await this.loadTransactions();
                
                // Возвращаемся к списку через 1.5 секунды
                setTimeout(() => {
                    this.switchView('transactions');
                    form.reset();
                    successEl.classList.add('hidden');
                }, 1500);
                
            } catch (error) {
                console.error('❌ Ошибка сохранения транзакции:', error);
                errorEl.textContent = `❌ Ошибка: ${error.message || 'Неизвестная ошибка'}`;
                errorEl.classList.remove('hidden');
                this.showError(`❌ Ошибка сохранения транзакции: ${error.message || 'Неизвестная ошибка'}`);
            }
        });
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
            const projectId = e.target.value;
            this.currentFilter.project = projectId || null;
            this.pagination.currentPage = 1; // Сбрасываем на первую страницу при изменении фильтра
            await this.loadTransactions();
        });
        
        // Пагинация
        document.getElementById('pagination-prev').addEventListener('click', () => {
            if (this.pagination.currentPage > 1) {
                this.pagination.currentPage--;
                this.loadTransactions();
            }
        });
        
        document.getElementById('pagination-next').addEventListener('click', () => {
            const totalPages = Math.ceil(this.pagination.totalItems / this.pagination.pageSize);
            if (this.pagination.currentPage < totalPages) {
                this.pagination.currentPage++;
                this.loadTransactions();
            }
        });
        
        document.getElementById('pagination-page-size').addEventListener('change', (e) => {
            this.pagination.pageSize = parseInt(e.target.value);
            this.pagination.currentPage = 1; // Сбрасываем на первую страницу
            this.loadTransactions();
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
                // local_id может быть строкой для pending транзакций
                await localDB.deletePendingTransaction(txId);
                console.log(`✅ Локальная транзакция ${txId} удалена`);
            } else {
                // Удаляем через API
                try {
                    await api.deleteTransaction(parseInt(txId));
                    console.log(`✅ Транзакция ${txId} удалена с сервера`);
                    
                    // Также удаляем из локальной БД (используем числовой id)
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


