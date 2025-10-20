"""
Утилиты для системы учета строителя
"""
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Transaction


def get_transactions_for_estimate_item(estimate_item):
    """
    Получить все транзакции для пункта сметы
    """
    if not estimate_item or not estimate_item.pk:
        return Transaction.objects.none()
    
    return Transaction.objects.filter(
        estimate_item=estimate_item
    ).order_by('-date')


def get_transactions_for_estimate(estimate):
    """
    Получить все транзакции для сметы (включая транзакции пунктов сметы)
    """
    if not estimate or not estimate.pk:
        return Transaction.objects.none()
    
    # Транзакции, привязанные к смете напрямую
    estimate_transactions = Transaction.objects.filter(estimate=estimate)
    
    # Транзакции, привязанные к пунктам сметы
    item_transactions = Transaction.objects.filter(estimate_item__estimate=estimate)
    
    # Объединяем
    return (estimate_transactions | item_transactions).distinct().order_by('-date')


def get_transactions_for_stage(stage):
    """
    Получить все транзакции для этапа (включая транзакции смет и пунктов сметы)
    """
    if not stage or not stage.pk:
        return Transaction.objects.none()
    
    # Транзакции, привязанные к этапу напрямую
    stage_transactions = Transaction.objects.filter(stage=stage)
    
    # Транзакции через сметы
    estimate_transactions = Transaction.objects.filter(
        estimate__stage=stage
    )
    
    # Транзакции через пункты смет
    item_transactions = Transaction.objects.filter(
        estimate_item__estimate__stage=stage
    )
    
    # Объединяем
    return (stage_transactions | estimate_transactions | item_transactions).distinct().order_by('-date')


def get_transactions_for_object(object_obj):
    """
    Получить все транзакции для объекта (включая все дочерние этапы, сметы и пункты сметы)
    """
    if not object_obj or not object_obj.pk:
        return Transaction.objects.none()
    
    # Транзакции через этапы
    stage_transactions = Transaction.objects.filter(
        stage__object=object_obj
    )
    
    estimate_transactions = Transaction.objects.filter(
        estimate__stage__object=object_obj
    )
    
    item_transactions = Transaction.objects.filter(
        estimate_item__estimate__stage__object=object_obj
    )
    
    # Объединяем
    return (stage_transactions | estimate_transactions | item_transactions).distinct().order_by('-date')


def get_transactions_for_project(project):
    """
    Получить все транзакции для проекта (включая все дочерние объекты, этапы, сметы и пункты сметы)
    """
    if not project or not project.pk:
        return Transaction.objects.none()
    
    # Транзакции через объекты проекта
    stage_transactions = Transaction.objects.filter(
        stage__object__project=project
    )
    
    estimate_transactions = Transaction.objects.filter(
        estimate__stage__object__project=project
    )
    
    item_transactions = Transaction.objects.filter(
        estimate_item__estimate__stage__object__project=project
    )
    
    # Объединяем
    return (stage_transactions | estimate_transactions | item_transactions).distinct().order_by('-date')


def render_transactions_table(transactions, title="Транзакции", show_links=True, page_size=10, page=1):
    """
    Рендерит HTML-таблицу транзакций в стиле Django Admin с пагинацией
    
    Args:
        transactions: QuerySet транзакций
        title: Заголовок таблицы
        show_links: Показывать ли ссылки на редактирование
        page_size: Количество записей на странице
        page: Номер страницы (начиная с 1)
    """
    if not transactions.exists():
        return format_html('<p style="color: #666; font-style: italic;">Нет транзакций</p>')
    
    # Пагинация
    total_count = transactions.count()
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_transactions = transactions[start_index:end_index]
    total_pages = (total_count + page_size - 1) // page_size
    
    html = f'<h3 style="margin-top: 20px; margin-bottom: 10px; color: #333;">{title}</h3>'
    
    # Информация о пагинации
    html += f'<p style="color: #666; font-size: 14px; margin-bottom: 10px;">'
    html += f'Показано {start_index + 1}-{min(end_index, total_count)} из {total_count} записей'
    html += '</p>'
    
    # Кнопка добавления новой транзакции
    if show_links:
        html += '<div style="margin-bottom: 10px;">'
        html += '<a href="/admin/control/transaction/add/" style="background-color: #007cba; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-size: 14px;">➕ Добавить транзакцию</a>'
        html += '</div>'
    
    html += '<div style="overflow-x: auto;">'
    html += '<table style="width: 100%; border-collapse: collapse; border: 1px solid var(--border-color, #ddd);">'
    
    # Заголовок таблицы
    html += '<thead>'
    html += '<tr style="border-bottom: 2px solid var(--border-color, #dee2e6);">'
    html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Дата</th>'
    html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Тип</th>'
    html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Категория</th>'
    html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Контрагент</th>'
    html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: right; font-weight: 600;">Сумма</th>'
    html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Описание</th>'
    html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Привязка</th>'
    if show_links:
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: center; font-weight: 600;">Действия</th>'
    html += '</tr>'
    html += '</thead>'
    
    # Тело таблицы
    html += '<tbody>'
    
    total_income = 0
    total_expense = 0
    
    for i, transaction in enumerate(paginated_transactions):
        # Определяем цвет суммы
        signed_amount = transaction.get_signed_amount()
        amount_color = '#28a745' if signed_amount > 0 else '#dc3545' if signed_amount < 0 else '#6c757d'
        
        # Подсчитываем общие суммы
        if signed_amount > 0:
            total_income += signed_amount
        else:
            total_expense += abs(signed_amount)
        
        html += '<tr>'
        html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{transaction.date}</td>'
        html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{transaction.get_transaction_type_display()}</td>'
        html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{transaction.category.name}</td>'
        html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{transaction.contractor.name if transaction.contractor else "-"}</td>'
        html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px; text-align: right; color: {amount_color}; font-weight: 500;">{signed_amount:,.2f} руб.</td>'
        html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{transaction.description}</td>'
        
        # Привязка
        if transaction.estimate_item:
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">Пункт: {transaction.estimate_item.get_item_name()}</td>'
        elif transaction.estimate:
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">Смета: {transaction.estimate}</td>'
        elif transaction.stage:
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">Этап: {transaction.stage.name}</td>'
        else:
            html += '<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">Прямая транзакция</td>'
        
        # Ссылки на редактирование и просмотр
        if show_links:
            html += '<td style="border: 1px solid var(--border-color, #ddd); padding: 8px; text-align: center;">'
            html += f'<a href="/admin/control/transaction/{transaction.pk}/change/" style="color: #007cba; text-decoration: none; margin-right: 5px;" title="Редактировать">✏️</a>'
            html += f'<a href="/admin/control/transaction/{transaction.pk}/" style="color: #28a745; text-decoration: none;" title="Просмотреть">👁️</a>'
            html += '</td>'
        
        html += '</tr>'
    
    html += '</tbody>'
    html += '</table>'
    html += '</div>'
    
    # Навигация по страницам
    if total_pages > 1:
        html += '<div style="margin-top: 15px; text-align: center;">'
        html += '<div style="display: inline-block;">'
        
        # Предыдущая страница
        if page > 1:
            html += f'<a href="?page={page-1}" style="padding: 8px 12px; margin: 0 2px; background-color: #007cba; color: white; text-decoration: none; border-radius: 4px;">‹ Предыдущая</a>'
        
        # Номера страниц
        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)
        
        for p in range(start_page, end_page + 1):
            if p == page:
                html += f'<span style="padding: 8px 12px; margin: 0 2px; background-color: #6c757d; color: white; border-radius: 4px;">{p}</span>'
            else:
                html += f'<a href="?page={p}" style="padding: 8px 12px; margin: 0 2px; background-color: #f8f9fa; color: #007cba; text-decoration: none; border-radius: 4px;">{p}</a>'
        
        # Следующая страница
        if page < total_pages:
            html += f'<a href="?page={page+1}" style="padding: 8px 12px; margin: 0 2px; background-color: #007cba; color: white; text-decoration: none; border-radius: 4px;">Следующая ›</a>'
        
        html += '</div>'
        html += '</div>'
    
    # Итоговая строка
    if paginated_transactions.exists():
        html += '<div style="margin-top: 15px; padding: 10px; border-radius: 4px; border: 1px solid var(--border-color, #dee2e6);">'
        html += '<strong>Итого по странице:</strong> '
        html += f'<span style="color: #28a745;">Доходы: {total_income:,.2f} руб.</span> | '
        html += f'<span style="color: #dc3545;">Расходы: {total_expense:,.2f} руб.</span> | '
        html += f'<span style="color: #007cba; font-weight: bold;">Баланс: {total_income - total_expense:,.2f} руб.</span>'
        html += '</div>'
    
    return format_html(html)


def get_transactions_summary(transactions):
    """
    Получить сводку по транзакциям
    """
    if not transactions.exists():
        return {
            'total_income': 0,
            'total_expense': 0,
            'balance': 0,
            'count': 0
        }
    
    total_income = 0
    total_expense = 0
    
    for transaction in transactions:
        signed_amount = transaction.get_signed_amount()
        if signed_amount > 0:
            total_income += signed_amount
        else:
            total_expense += abs(signed_amount)
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'count': transactions.count()
    }
