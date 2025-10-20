(function() {
    'use strict';
    
    // Функция для ожидания загрузки jQuery
    function initScript() {
        var $;
        
        // Пробуем разные способы получения jQuery
        if (typeof django !== 'undefined' && django.jQuery) {
            $ = django.jQuery;
        } else if (typeof jQuery !== 'undefined') {
            $ = jQuery;
        } else if (typeof $ !== 'undefined') {
            $ = $;
        } else {
            // Если jQuery еще не загружен, ждем
            setTimeout(initScript, 100);
            return;
        }
        
        // Запускаем основной код
        $(document).ready(function() {
    
    // Функция для получения данных прайсовой позиции
    function getPriceItemData(priceItemId, callback) {
        if (!priceItemId) {
            console.log('PriceItem ID не указан');
            callback(null);
            return;
        }
        
        console.log('Запрашиваем данные для PriceItem ID:', priceItemId);
        
        $.ajax({
            url: '/api/price-item-data/',
            data: { id: priceItemId },
            dataType: 'json',
            success: function(data) {
                console.log('Получены данные прайса:', data);
                callback(data);
            },
            error: function(xhr, status, error) {
                console.error('Ошибка получения данных прайса:', error, xhr.responseText);
                callback(null);
            }
        });
    }
    
    // Функция для автозаполнения полей
    function autoFillFields(row, priceData) {
        if (!priceData) {
            console.log('Нет данных для автозаполнения');
            return;
        }
        
        console.log('Автозаполнение полей для строки:', row);
        console.log('Данные прайса:', priceData);
        
        // Находим поле цены за единицу в текущей строке
        var unitPriceField = row.find('input[name$="-unit_price"]');
        console.log('Найдено полей цены:', unitPriceField.length);
        
        if (unitPriceField.length) {
            console.log('Текущее значение цены:', unitPriceField.val());
            
            // Заполняем цену только если поле пустое или равно 0
            if (!unitPriceField.val() || unitPriceField.val() == '0') {
                console.log('Заполняем цену:', priceData.price_per_unit);
                unitPriceField.val(priceData.price_per_unit);
                
                // Триггерим событие change для пересчета сумм
                unitPriceField.trigger('change');
                console.log('Цена заполнена и событие change вызвано');
            } else {
                console.log('Поле цены уже заполнено, пропускаем');
            }
        } else {
            console.log('Поле цены не найдено в строке');
        }
        
        // Опционально: заполняем описание, если оно пустое
        var descriptionField = row.find('input[name$="-description"]');
        if (descriptionField.length && !descriptionField.val()) {
            var description = priceData.material || priceData.work_type || '';
            if (description) {
                descriptionField.val(description);
                console.log('Описание заполнено:', description);
            }
        }
    }
    
    // Обработчик изменения поля прайсовой позиции
    function onPriceItemChange() {
        var $this = $(this);
        var row = $this.closest('tr');
        var priceItemId = $this.val();
        
        console.log('Изменение прайсовой позиции. ID:', priceItemId, 'Строка:', row);
        
        if (priceItemId) {
            getPriceItemData(priceItemId, function(priceData) {
                if (priceData) {
                    autoFillFields(row, priceData);
                }
            });
        }
    }
    
    // Инициализация при загрузке страницы
    $(document).ready(function() {
        console.log('Инициализация скрипта автозаполнения');
        
        // Функция для привязки обработчиков к полям прайса
        function bindPriceItemHandlers() {
            var priceItemSelects = $('select[name$="-price_item"]');
            console.log('Найдено полей прайса:', priceItemSelects.length);
            
            priceItemSelects.each(function() {
                var $select = $(this);
                if (!$select.data('price-handler-bound')) {
                    $select.on('change', onPriceItemChange);
                    $select.data('price-handler-bound', true);
                    console.log('Обработчик привязан к полю:', $select.attr('name'));
                }
            });
        }
        
        // Привязываем обработчики к существующим полям
        bindPriceItemHandlers();
        
        // Обработчик для динамически добавляемых строк
        $(document).on('click', '.add-row a', function() {
            console.log('Добавлена новая строка');
            setTimeout(function() {
                bindPriceItemHandlers();
            }, 200);
        });
        
        // Обработчик для автокомплита Django (select2)
        $(document).on('select2:select', 'select[name$="-price_item"]', function(e) {
            console.log('Select2 выбор:', e.params.data);
            var row = $(this).closest('tr');
            var priceItemId = e.params.data.id;
            
            if (priceItemId) {
                getPriceItemData(priceItemId, function(priceData) {
                    if (priceData) {
                        autoFillFields(row, priceData);
                    }
                });
            }
        });
        
        // Дополнительный обработчик для случаев, когда автокомплит не срабатывает
        $(document).on('change', 'select[name$="-price_item"]', function() {
            console.log('Обычный change event на select');
            onPriceItemChange.call(this);
        });
        
        // Обработчик для клика по опциям в автокомплите
        $(document).on('click', '.select2-results__option', function() {
            var $option = $(this);
            var $select = $option.closest('.select2-container').prev('select');
            if ($select.attr('name') && $select.attr('name').endsWith('-price_item')) {
                setTimeout(function() {
                    var priceItemId = $select.val();
                    if (priceItemId) {
                        var row = $select.closest('tr');
                        getPriceItemData(priceItemId, function(priceData) {
                            if (priceData) {
                                autoFillFields(row, priceData);
                            }
                        });
                    }
                }, 100);
            }
        });
        });
        
        }); // конец $(document).ready
    }
    
    // Запускаем инициализацию
    initScript();
    
})();
