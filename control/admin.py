from django.contrib import admin
from django.db.models import Q
from admin_auto_filters.filters import AutocompleteFilter

class StageAutocompleteFilter(AutocompleteFilter):
    title = 'Этап'
    field_name = 'stage'

class EstimateAutocompleteFilter(AutocompleteFilter):
    title = 'Смета'
    field_name = 'estimate'

class EstimateItemAutocompleteFilter(AutocompleteFilter):
    title = 'Пункт сметы'
    field_name = 'estimate_item'

class CategoryAutocompleteFilter(AutocompleteFilter):
    title = 'Категория'
    field_name = 'category'

# ContractorAutocompleteFilter удален - теперь используем CustomUser
DropdownFilter = ChoiceDropdownFilter = RelatedDropdownFilter = None
from django.contrib.auth.admin import UserAdmin
from django import forms
from .models import (
    CustomUser, Project, Object, Stage, Estimate, EstimateItem,
    WorkType, MaterialType, PriceItem,
    Category, Transaction
)
from .utils import (
    get_transactions_for_estimate_item, get_transactions_for_estimate,
    get_transactions_for_stage, get_transactions_for_object, 
    get_transactions_for_project, render_transactions_table
)


# Кастомные формы для уменьшения размера многострочных полей
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }


class ObjectForm(forms.ModelForm):
    class Meta:
        model = Object
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }


# ContractorForm удален - больше не нужен


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'
        widgets = {
            'description': forms.TextInput(attrs={'size': 50}),
        }


class WorkTypeForm(forms.ModelForm):
    class Meta:
        model = WorkType
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }


class MaterialTypeForm(forms.ModelForm):
    class Meta:
        model = MaterialType
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }

class EstimateItemForm(forms.ModelForm):
    class Meta:
        model = EstimateItem
        fields = '__all__'
        widgets = {
            'description': forms.TextInput(attrs={'size': 50}),
        }


class CustomUserAdmin(UserAdmin):
    """Админка для кастомной модели пользователя"""
    model = CustomUser
    list_display = ['phone', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['phone', 'first_name', 'last_name']
    ordering = ['phone']
    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'ext_id')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
        ('Дополнительно', {'fields': ('auth_token',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


class EstimateItemInline(admin.TabularInline):
    """Инлайн для элементов сметы"""
    model = EstimateItem
    extra = 0
    fields = [
        'price_item', 'description',
        'quantity', 'unit_price', 'base_price', 'income_type', 
        'income_value', 'is_percentage', 'income_amount', 'client_price', 'contractor_price',
        'get_create_transaction_button'
    ]
    readonly_fields = [
        'base_price', 'income_amount', 'client_price', 'contractor_price',
        'get_create_transaction_button'
    ]
    autocomplete_fields = ['price_item']
    
    class Media:
        js = (
            'admin/js/jquery.init.js',
            'admin/js/estimate_item_inline.js',
        )
        css = {
            'all': (
                'admin/css/estimate_item_inline.css',
            )
        }
    
    def get_create_transaction_button(self, obj):
        """Кнопка для создания транзакции по отдельной позиции"""
        if not obj.pk:
            return 'Сохраните позицию для создания транзакции'
        
        from django.utils.html import format_html
        from django.urls import reverse
        
        url = reverse('admin:control_estimateitem_create_transaction', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" style="background-color: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px; display:inline-block; white-space: nowrap;">💰 Создать транзакцию</a>',
            url
        )
    
    get_create_transaction_button.short_description = 'Действия'


class TransactionInline(admin.TabularInline):
    """Инлайн для транзакций"""
    model = Transaction
    extra = 0
    fields = [
        'date', 'transaction_type', 'category', 'contractor', 
        'amount', 'description', 'get_estimate_info'
    ]
    readonly_fields = ['get_signed_amount', 'get_estimate_info']
    
    def get_signed_amount(self, obj):
        """Получить сумму со знаком"""
        if obj.pk:
            return f"{obj.get_signed_amount():,.2f} руб."
        return '-'
    get_signed_amount.short_description = 'Сумма со знаком'
    
    def get_estimate_info(self, obj):
        """Показать информацию о смете"""
        if obj.pk and obj.estimate:
            return f"Смета: {obj.estimate}"
        return 'Прямая транзакция'
    get_estimate_info.short_description = 'Привязка'


class EstimateAdmin(admin.ModelAdmin):
    """Админка для смет"""
    list_display = [
        'stage', 'status', 'get_client_total', 'get_contractor_total', 
        'get_income_total', 'created_at'
    ]
    list_filter = ('status', StageAutocompleteFilter, 'created_at')
    search_fields = ['stage__name', 'stage__object__name']
    readonly_fields = [
        'get_create_transactions_button', 'get_client_total', 'get_contractor_total', 'get_income_total', 
        'get_base_total', 'created_at', 'updated_at', 'get_all_transactions'
    ]
    inlines = [EstimateItemInline, TransactionInline]
    autocomplete_fields = ['stage']
    change_form_template = 'admin/control/estimate/change_form.html'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:estimate_id>/create-transactions/',
                self.admin_site.admin_view(self.create_transactions_view),
                name='control_estimate_create_transactions',
            ),
            path(
                '<int:estimate_id>/transactions-list/',
                self.admin_site.admin_view(self.transactions_list_view),
                name='control_estimate_transactions_list',
            ),
            path(
                '<int:estimate_id>/export/',
                self.admin_site.admin_view(self.export_view),
                name='control_estimate_export',
            ),
            path(
                '<int:estimate_id>/export/preview/',
                self.admin_site.admin_view(self.export_preview_view),
                name='control_estimate_export_preview',
            ),
            path(
                '<int:estimate_id>/export/xlsx/',
                self.admin_site.admin_view(self.export_xlsx_view),
                name='control_estimate_export_xlsx',
            ),
        ]
        return custom_urls + urls
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('stage', 'status')
        }),
        ('Суммы по смете', {
            'fields': ('get_client_total', 'get_contractor_total', 'get_income_total', 'get_base_total'),
            'classes': ('collapse',)
        }),
        ('История транзакций', {
            'fields': ('get_all_transactions',),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_client_total(self, obj):
        """Сумма для заказчика"""
        return f"{obj.get_client_total():,.2f} руб."
    get_client_total.short_description = 'Сумма для заказчика'
    
    def get_contractor_total(self, obj):
        """Сумма для исполнителя"""
        return f"{obj.get_contractor_total():,.2f} руб."
    get_contractor_total.short_description = 'Сумма для исполнителя'
    
    def get_income_total(self, obj):
        """Доход по смете"""
        return f"{obj.get_income_total():,.2f} руб."
    get_income_total.short_description = 'Доход по смете'
    
    def get_base_total(self, obj):
        """Базовая сумма"""
        return f"{obj.get_base_total():,.2f} руб."
    get_base_total.short_description = 'Базовая сумма'
    
    def get_all_transactions(self, obj):
        """Показать все транзакции сметы"""
        if not obj.pk:
            return 'Сохраните смету для просмотра транзакций'
        from django.utils.html import format_html
        from django.template.loader import render_to_string
        from .models import Transaction
        from django.core.paginator import Paginator
        
        qs = Transaction.objects.filter(estimate=obj).select_related('category', 'contractor')\
            .order_by('-date', '-id')
        paginator = Paginator(qs, 15)
        page_obj = paginator.get_page(1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        
        from django.urls import reverse
        base_url = reverse('admin:control_estimate_transactions_list', args=[obj.pk])
        per_page = 20
        html_inner = render_to_string(
            'admin/control/estimate/transactions_list.html',
            {
                'estimate': obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'per_page': per_page,
                'base_url': base_url,
                'all_total_income': all_total_income,
                'all_total_expense': all_total_expense,
                'all_total_net': all_total_net,
            }
        )
        # Оборачиваем в контейнер, чтобы будущие AJAX-страницы могли заменяться внутри
        return format_html('<div id="estimate-tx-list">{}</div>', html_inner)
    
    get_all_transactions.short_description = 'Все транзакции сметы'
    
    def get_create_transactions_button(self, obj):
        """Кнопка для создания транзакций по смете"""
        if not obj.pk:
            return 'Сохраните смету для создания транзакций'
        
        from django.utils.html import format_html
        from django.urls import reverse
        
        url = reverse('admin:control_estimate_create_transactions', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">💰 Создать транзакции по смете</a>',
            url
        )
    
    get_create_transactions_button.short_description = 'Создание транзакций'
    
    def create_transactions_view(self, request, estimate_id):
        """View для создания транзакций по смете"""
        from django.shortcuts import render, redirect, get_object_or_404
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        from .models import Estimate, Transaction, Category
        from django.urls import reverse
        
        estimate = get_object_or_404(Estimate, pk=estimate_id)
        
        if request.method == 'POST':
            # Обработка создания транзакций
            return self._process_transaction_creation(request, estimate)
        
        # GET запрос - показываем форму подтверждения
        return self._show_confirmation_form(request, estimate)
    
    def _show_confirmation_form(self, request, estimate):
        """Показать форму подтверждения с редактируемыми полями"""
        from django.shortcuts import render
        from .models import Category
        
        # Получаем все элементы сметы
        items = estimate.items.all()
        
        # Получаем категории и контрагентов для выбора
        categories = Category.objects.filter(is_active=True)
        contractors = CustomUser.objects.filter(is_active=True)
        
        # Подготавливаем данные для каждого элемента
        items_data = []
        for item in items:
            # Пересчитываем суммы, если они не актуальны
            item._calculate_amounts()
            

            item_data = {
                'item': item,
                'expense_amount': f"{float(item.contractor_price):.2f}",  # Сумма расхода (для исполнителя) с точкой
                'income_amount': f"{float(item.income_amount):.2f}" if item.income_type else "0.00",  # Сумма дохода с точкой
                'expense_category': None,  # Будет заполнено в форме
                'income_category': None,   # Будет заполнено в форме
            }
            items_data.append(item_data)
        
        context = {
            'estimate': estimate,
            'items_data': items_data,
            'categories': categories,
            'contractors': contractors,
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        
        return render(request, 'admin/control/estimate/create_transactions.html', context)

    def transactions_list_view(self, request, estimate_id):
        """Серверный список транзакций сметы с пагинацией (для AJAX-встраивания)."""
        from django.shortcuts import render, get_object_or_404
        from django.core.paginator import Paginator
        from .models import Estimate, Transaction
        
        estimate = get_object_or_404(Estimate, pk=estimate_id)
        qs = Transaction.objects.filter(estimate=estimate).select_related('category', 'contractor')\
            .order_by('-date', '-id')
        
        # размер страницы
        try:
            per_page = int(request.GET.get('per_page', 20))
        except Exception:
            per_page = 20
        # Ограничим разумными пределами
        if per_page < 5:
            per_page = 5
        if per_page > 500:
            per_page = 500
        page_number = request.GET.get('page') or 1
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page_number)
        
        # Итоги по всем результатам (по смете)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        
        from django.urls import reverse
        base_url = reverse('admin:control_estimate_transactions_list', args=[estimate.pk])
        context = {
            'estimate': estimate,
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': per_page,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        }
        return render(request, 'admin/control/estimate/transactions_list.html', context)

    def export_view(self, request, estimate_id):
        """Промежуточная страница выбора формата и аудитории, с редактируемым списком позиций."""
        from django.shortcuts import render, get_object_or_404
        from .models import Estimate
        estimate = get_object_or_404(Estimate, pk=estimate_id)
        audience = request.GET.get('audience', 'client')  # client|self|contractor
        return render(request, 'admin/control/estimate/export/select.html', {
            'estimate': estimate,
            'audience': audience,
        })

    def export_preview_view(self, request, estimate_id):
        """HTML предпросмотр для печати (PDF через печать браузера)."""
        from django.shortcuts import render, get_object_or_404
        from .models import Estimate
        estimate = get_object_or_404(Estimate, pk=estimate_id)
        audience = request.GET.get('audience', 'client')
        # Рассчитываем данные по каждой позиции под выбранную аудиторию
        materials_data, works_data = [], []
        total_materials, total_works = 0.0, 0.0
        for item in estimate.items.select_related('price_item').all():
            item._calculate_amounts()
            quantity = float(item.quantity)
            unit = item.get_unit()
            if audience == 'self' or audience == 'contractor':
                total = float(item.contractor_price)
            else:  # client
                total = float(item.client_price)
            unit_price = float(total / quantity) if quantity else float(item.unit_price)
            record = {
                'name': item.get_item_name(),
                'unit': unit,
                'quantity': quantity,
                'unit_price': unit_price,
                'unit_price_str': f"{unit_price:.2f}",
                'total': total,
                'total_str': f"{total:.2f}",
            }
            # Группируем по типу price_item (материал/работа)
            price_item = getattr(item, 'price_item', None)
            if price_item and getattr(price_item, 'material_id', None):
                materials_data.append(record)
                total_materials += total
            else:
                works_data.append(record)
                total_works += total
        overall_total = total_materials + total_works
        return render(request, 'admin/control/estimate/export/preview.html', {
            'estimate': estimate,
            'audience': audience,
            'materials_data': materials_data,
            'works_data': works_data,
            'total_materials': total_materials,
            'total_works': total_works,
            'overall_total': overall_total,
            'total_materials_str': f"{total_materials:.2f}",
            'total_works_str': f"{total_works:.2f}",
            'overall_total_str': f"{overall_total:.2f}",
        })

    def export_xlsx_view(self, request, estimate_id):
        """Выгрузка Excel с учетом выбора аудитории и корректировок."""
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponse
        from .models import Estimate
        import io
        try:
            import xlsxwriter
        except Exception:
            return HttpResponse('xlsxwriter не установлен', status=500)
        estimate = get_object_or_404(Estimate, pk=estimate_id)
        audience = request.GET.get('audience', 'client')
        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet('Смета')
        headers = ['Наименование', 'Ед.', 'Кол-во', 'Цена', 'Сумма']
        for c, h in enumerate(headers):
            ws.write(0, c, h)
        row = 1
        for item in estimate.items.all():
            name = item.get_item_name()
            unit = item.get_unit()
            qty = float(item.quantity)
            # цена по аудитории
            if audience == 'self':
                price = float(item.contractor_price / item.quantity) if item.quantity else float(item.unit_price)
            elif audience == 'contractor':
                price = float(item.contractor_price / item.quantity) if item.quantity else float(item.unit_price)
            else:
                price = float(item.client_price / item.quantity) if item.quantity else float(item.unit_price)
            total = qty * price
            ws.write(row, 0, name)
            ws.write(row, 1, unit or '')
            ws.write(row, 2, qty)
            ws.write(row, 3, price)
            ws.write(row, 4, total)
            row += 1
        wb.close()
        output.seek(0)
        resp = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = f'attachment; filename="estimate_{estimate_id}.xlsx"'
        return resp
    
    def _process_transaction_creation(self, request, estimate):
        """Обработать создание транзакций"""
        from django.shortcuts import redirect
        from django.contrib import messages
        from django.urls import reverse
        from .models import Transaction
        from django.db import transaction
        
        try:
            with transaction.atomic():
                created_count = 0
                
                # Проходим по всем элементам сметы
                for item in estimate.items.all():
                    # Проверяем, включена ли позиция
                    include_item = request.POST.get(f'include_item_{item.id}')
                    if not include_item:
                        continue
                    
                    # Получаем данные из формы
                    include_expense = request.POST.get(f'include_expense_{item.id}')
                    include_income = request.POST.get(f'include_income_{item.id}')
                    
                    if include_expense:
                        expense_amount = request.POST.get(f'expense_amount_{item.id}')
                        expense_category_id = request.POST.get(f'expense_category_{item.id}')
                        expense_contractor_id = request.POST.get(f'expense_contractor_{item.id}')
                        
                        if expense_amount and expense_category_id:
                            # Создаем транзакцию расхода
                            Transaction.objects.create(
                                amount=expense_amount,
                                transaction_type='expense',
                                category_id=expense_category_id,
                                contractor_id=expense_contractor_id if expense_contractor_id else None,
                                description=f'Расход по смете: {item.get_item_name()}',
                                estimate=estimate,
                                estimate_item=item,
                            )
                            created_count += 1
                    
                    if include_income:
                        income_amount = request.POST.get(f'income_amount_{item.id}')
                        income_category_id = request.POST.get(f'income_category_{item.id}')
                        income_contractor_id = request.POST.get(f'income_contractor_{item.id}')
                        
                        if income_amount and income_category_id:
                            # Формируем описание дохода
                            if item.income_type:
                                description = f'Расход по смете (наценка/откат): {item.get_item_name()} ({item.get_income_display()})'
                            else:
                                # Дополнительный расход (раньше доход)
                                income_description = request.POST.get(f'income_description_{item.id}', '').strip()
                                if income_description:
                                    description = f'Дополнительный расход по смете: {item.get_item_name()} - {income_description}'
                                else:
                                    description = f'Дополнительный расход по смете: {item.get_item_name()}'
                            
                            # Создаем как расход (наценки/откаты тоже расходы бюджета)
                            Transaction.objects.create(
                                amount=income_amount,
                                transaction_type='expense',
                                category_id=income_category_id,
                                contractor_id=income_contractor_id if income_contractor_id else None,
                                description=description,
                                estimate=estimate,
                                estimate_item=item,
                            )
                            created_count += 1
                
                messages.success(request, f'Успешно создано {created_count} транзакций по смете.')
                
        except Exception as e:
            messages.error(request, f'Ошибка при создании транзакций: {str(e)}')
        
        return redirect(reverse('admin:control_estimate_change', args=[estimate.pk]))


class EstimateItemAdmin(admin.ModelAdmin):
    """Админка для элементов сметы"""
    form = EstimateItemForm
    list_display = [
        'estimate', 'get_item_name', 'quantity', 
        'unit_price', 'base_price', 'income_type', 'income_value', 
        'is_percentage', 'income_amount', 'client_price', 'contractor_price'
    ]
    list_filter = ('income_type', 'is_percentage', EstimateAutocompleteFilter, 'created_at')
    search_fields = [
        'price_item__name', 'description',
        'estimate__stage__name'
    ]
    readonly_fields = [
        'base_price', 'income_amount', 'client_price', 'contractor_price', 
        'created_at', 'updated_at', 'get_transactions'
    ]
    autocomplete_fields = ['estimate', 'price_item']
    actions = ['create_transactions_for_selected']
    change_form_template = 'admin/control/estimateitem/change_form.html'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:item_id>/create-transaction/',
                self.admin_site.admin_view(self.create_transaction_view),
                name='control_estimateitem_create_transaction',
            ),
            path(
                'create-transactions-selected/',
                self.admin_site.admin_view(self.create_transactions_selected_view),
                name='control_estimateitem_create_transactions_selected',
            ),
            path(
                '<int:item_id>/transactions-list/',
                self.admin_site.admin_view(self.transactions_list_view),
                name='control_estimateitem_transactions_list',
            ),
        ]
        return custom_urls + urls
    
    def create_transaction_view(self, request, item_id):
        """View для создания транзакции по отдельной позиции"""
        from django.shortcuts import redirect
        from django.urls import reverse
        
        # Сохраняем ID позиции в сессии
        request.session['selected_estimate_items'] = [item_id]
        
        # Перенаправляем на общую страницу подтверждения
        return redirect(reverse('admin:control_estimateitem_create_transactions_selected'))
    
    def create_transactions_for_selected(self, request, queryset):
        """Действие для создания транзакций по выбранным позициям"""
        from django.shortcuts import redirect
        from django.urls import reverse
        from django.contrib import messages
        
        # Сохраняем выбранные ID в сессии
        selected_ids = list(queryset.values_list('id', flat=True))
        request.session['selected_estimate_items'] = selected_ids
        
        # Перенаправляем на страницу подтверждения
        return redirect(reverse('admin:control_estimateitem_create_transactions_selected'))
    
    create_transactions_for_selected.short_description = "Создать транзакции для выбранных позиций"
    
    def _process_selected_transactions(self, request, queryset):
        """Обработать создание транзакций для выбранных позиций"""
        from django.shortcuts import redirect
        from django.contrib import messages
        from django.urls import reverse
        from .models import Transaction
        from django.db import transaction
        
        try:
            with transaction.atomic():
                created_count = 0
                
                # Проходим по всем выбранным позициям
                for item in queryset:
                    # Проверяем, включена ли позиция
                    include_item = request.POST.get(f'include_item_{item.id}')
                    if not include_item:
                        continue
                    
                    # Получаем данные из формы
                    include_expense = request.POST.get(f'include_expense_{item.id}')
                    include_income = request.POST.get(f'include_income_{item.id}')
                    
                    if include_expense:
                        expense_amount = request.POST.get(f'expense_amount_{item.id}')
                        expense_category_id = request.POST.get(f'expense_category_{item.id}')
                        expense_contractor_id = request.POST.get(f'expense_contractor_{item.id}')
                        
                        if expense_amount and expense_category_id:
                            # Создаем транзакцию расхода
                            Transaction.objects.create(
                                amount=expense_amount,
                                transaction_type='expense',
                                category_id=expense_category_id,
                                contractor_id=expense_contractor_id if expense_contractor_id else None,
                                description=f'Расход по смете: {item.get_item_name()}',
                                estimate=item.estimate,
                                estimate_item=item,
                            )
                            created_count += 1
                    
                    if include_income:
                        income_amount = request.POST.get(f'income_amount_{item.id}')
                        income_category_id = request.POST.get(f'income_category_{item.id}')
                        income_contractor_id = request.POST.get(f'income_contractor_{item.id}')
                        
                        if income_amount and income_category_id:
                            # Формируем описание дохода
                            if item.income_type:
                                description = f'Расход по смете (наценка/откат): {item.get_item_name()} ({item.get_income_display()})'
                            else:
                                # Дополнительный расход (раньше доход)
                                income_description = request.POST.get(f'income_description_{item.id}', '').strip()
                                if income_description:
                                    description = f'Дополнительный расход по смете: {item.get_item_name()} - {income_description}'
                                else:
                                    description = f'Дополнительный расход по смете: {item.get_item_name()}'
                            
                            # Создаем как расход (наценки/откаты тоже расходы бюджета)
                            Transaction.objects.create(
                                amount=income_amount,
                                transaction_type='expense',
                                category_id=income_category_id,
                                contractor_id=income_contractor_id if income_contractor_id else None,
                                description=description,
                                estimate=item.estimate,
                                estimate_item=item,
                            )
                            created_count += 1
                
                messages.success(request, f'Успешно создано {created_count} транзакций по выбранным позициям.')
                
        except Exception as e:
            messages.error(request, f'Ошибка при создании транзакций: {str(e)}')
        
        # Очищаем сессию
        if 'selected_estimate_items' in request.session:
            del request.session['selected_estimate_items']
        
        return redirect(reverse('admin:control_estimateitem_changelist'))
    
    def create_transactions_selected_view(self, request):
        """View для создания транзакций по выбранным позициям"""
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from django.urls import reverse
        from .models import EstimateItem, Category
        
        # Получаем выбранные ID из сессии
        selected_ids = request.session.get('selected_estimate_items', [])
        if not selected_ids:
            messages.error(request, 'Нет выбранных позиций для создания транзакций.')
            return redirect(reverse('admin:control_estimateitem_changelist'))
        
        # Получаем объекты
        queryset = EstimateItem.objects.filter(id__in=selected_ids)
        
        if request.method == 'POST':
            # Обработка создания транзакций
            return self._process_selected_transactions(request, queryset)
        
        # GET запрос - показываем форму
        categories = Category.objects.filter(is_active=True)
        contractors = CustomUser.objects.filter(is_active=True)
        
        # Подготавливаем данные для каждой выбранной позиции
        items_data = []
        for item in queryset:
            # Пересчитываем суммы
            item._calculate_amounts()
            
            item_data = {
                'item': item,
                'expense_amount': f"{float(item.contractor_price):.2f}",  # Сумма расхода (для исполнителя) с точкой
                'income_amount': f"{float(item.income_amount):.2f}" if item.income_type else "0.00",  # Сумма дохода с точкой
                'expense_category': None,
                'income_category': None,
                'include_expense': True,  # По умолчанию включаем расход
                'include_income': bool(item.income_type),  # Доход только если есть наценка/откат
            }
            items_data.append(item_data)
        
        context = {
            'items_data': items_data,
            'categories': categories,
            'contractors': contractors,
            'opts': self.model._meta,
            'has_view_permission': True,
            'is_selected_action': True,
        }
        
        return render(request, 'admin/control/estimate/create_transactions.html', context)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('estimate', 'price_item', 'description')
        }),
        ('Количественные характеристики', {
            'fields': ('quantity', 'unit_price')
        }),
        ('Доход', {
            'fields': ('income_type', 'income_value', 'is_percentage')
        }),
        ('Расчетные поля', {
            'fields': ('base_price', 'income_amount', 'client_price', 'contractor_price'),
            'classes': ('collapse',)
        }),
        ('Транзакции по пункту', {
            'fields': ('get_transactions',),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_item_name(self, obj):
        """Получить название элемента"""
        return obj.get_item_name()
    get_item_name.short_description = 'Название'
    
    def get_transactions(self, obj):
        """Показать транзакции по пункту сметы (AJAX список с пагинацией)"""
        if not obj.pk:
            return 'Сохраните пункт сметы для просмотра транзакций'
        from django.utils.html import format_html
        from django.template.loader import render_to_string
        from django.core.paginator import Paginator
        from django.urls import reverse
        from .models import Transaction
        qs = Transaction.objects.filter(estimate_item=obj).select_related('category', 'contractor').order_by('-date', '-id')
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        base_url = reverse('admin:control_estimateitem_transactions_list', args=[obj.pk])
        html_inner = render_to_string(
            'admin/control/estimate/transactions_list.html',
            {
                'page_obj': page_obj,
                'paginator': paginator,
                'per_page': 20,
                'base_url': base_url,
                'all_total_income': all_total_income,
                'all_total_expense': all_total_expense,
                'all_total_net': all_total_net,
            }
        )
        return format_html('<div id="tx-list">{}</div>', html_inner)
    
    get_transactions.short_description = 'Транзакции по пункту'

    def transactions_list_view(self, request, item_id):
        """Список транзакций по EstimateItem (AJAX)."""
        from django.shortcuts import get_object_or_404, render
        from django.core.paginator import Paginator
        from .models import EstimateItem, Transaction
        item = get_object_or_404(EstimateItem, pk=item_id)
        qs = Transaction.objects.filter(estimate_item=item).select_related('category', 'contractor').order_by('-date', '-id')
        try:
            per_page = int(request.GET.get('per_page', 20))
        except Exception:
            per_page = 20
        if per_page < 5:
            per_page = 5
        if per_page > 500:
            per_page = 500
        page_number = request.GET.get('page') or 1
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page_number)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        from django.urls import reverse
        base_url = reverse('admin:control_estimateitem_transactions_list', args=[item.pk])
        return render(request, 'admin/control/estimate/transactions_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': per_page,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        })
    
    def income_info(self, obj):
        """Информация о доходе"""
        if obj.income_type and obj.income_value:
            if obj.is_percentage:
                return f"{obj.income_value}%"
            else:
                return f"{obj.income_value} руб."
        return '-'
    income_info.short_description = 'Доход'





class ProjectAdmin(admin.ModelAdmin):
    """Админка для проектов"""
    form = ProjectForm
    list_display = ['name', 'contractor', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'contractor', 'created_at']
    search_fields = ['name', 'description', 'contractor__name']
    readonly_fields = ['created_at', 'updated_at', 'get_all_transactions', 'get_all_stages']
    autocomplete_fields = ['contractor']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'contractor', 'is_active')
        }),
        ('Все этапы проекта', {
            'fields': ('get_all_stages',),
            'classes': ('collapse',)
        }),
        ('Все транзакции проекта', {
            'fields': ('get_all_transactions',),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:project_id>/transactions-list/',
                self.admin_site.admin_view(self.transactions_list_view),
                name='control_project_transactions_list',
            ),
        ]
        return custom_urls + urls
    
    def get_all_transactions(self, obj):
        """Показать все транзакции проекта (AJAX список)."""
        if not obj.pk:
            return 'Сохраните проект для просмотра транзакций'
        from django.utils.html import format_html
        from django.template.loader import render_to_string
        from django.core.paginator import Paginator
        from django.urls import reverse
        from .models import Transaction
        qs = get_transactions_for_project(obj)
        # qs может быть списком — приведем к QuerySet через фильтр
        if not hasattr(qs, 'filter'):
            qs_ids = [t.id for t in qs]
            qs = Transaction.objects.filter(id__in=qs_ids).order_by('-date', '-id')
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        base_url = reverse('admin:control_project_transactions_list', args=[obj.pk])
        html_inner = render_to_string('admin/control/estimate/transactions_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': 20,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        })
        return format_html('<div id="tx-list">{}</div>', html_inner)

    def transactions_list_view(self, request, project_id):
        from django.shortcuts import get_object_or_404, render
        from django.core.paginator import Paginator
        from .models import Project, Transaction
        project = get_object_or_404(Project, pk=project_id)
        qs = get_transactions_for_project(project)
        if not hasattr(qs, 'filter'):
            qs_ids = [t.id for t in qs]
            qs = Transaction.objects.filter(id__in=qs_ids).order_by('-date', '-id')
        try:
            per_page = int(request.GET.get('per_page', 20))
        except Exception:
            per_page = 20
        if per_page < 5: per_page = 5
        if per_page > 500: per_page = 500
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(request.GET.get('page') or 1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        from django.urls import reverse
        base_url = reverse('admin:control_project_transactions_list', args=[project.pk])
        return render(request, 'admin/control/estimate/transactions_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': per_page,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        })
    
    get_all_transactions.short_description = 'Все транзакции проекта'
    
    def get_all_stages(self, obj):
        """Показать все этапы проекта"""
        if not obj.pk:
            return 'Сохраните проект для просмотра этапов'
        
        from django.utils.html import format_html
        
        # Получаем все этапы проекта через объекты
        from .models import Stage
        stages = Stage.objects.filter(object__project=obj).order_by('object__name', 'order')
        
        if not stages.exists():
            return format_html('<p style="color: #666; font-style: italic;">Нет этапов</p>')
        
        # Кнопка добавления нового этапа
        html = '<div style="margin-bottom: 10px;">'
        html += '<a href="/admin/control/stage/add/" style="background-color: #007cba; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-size: 14px;">➕ Добавить этап</a>'
        html += '</div>'
        
        html += '<div style="overflow-x: auto;">'
        html += '<table style="width: 100%; border-collapse: collapse; border: 1px solid var(--border-color, #ddd);">'
        
        # Заголовок таблицы
        html += '<thead>'
        html += '<tr style="border-bottom: 2px solid var(--border-color, #dee2e6);">'
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Объект</th>'
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">Название</th>'
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: center; font-weight: 600;">Порядок</th>'
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">План. начало</th>'
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: left; font-weight: 600;">План. окончание</th>'
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: center; font-weight: 600;">Статус</th>'
        html += '<th style="border: 1px solid var(--border-color, #ddd); padding: 12px 8px; text-align: center; font-weight: 600;">Действия</th>'
        html += '</tr>'
        html += '</thead>'
        
        # Тело таблицы
        html += '<tbody>'
        
        for i, stage in enumerate(stages):
            # Статус этапа
            status_color = '#28a745' if stage.is_active else '#6c757d'
            status_text = 'Активен' if stage.is_active else 'Неактивен'
            
            html += '<tr>'
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{stage.object.name}</td>'
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px; font-weight: 500;">{stage.name}</td>'
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px; text-align: center;">{stage.order}</td>'
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{stage.planned_start_date or "-"}</td>'
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px;">{stage.planned_end_date or "-"}</td>'
            html += f'<td style="border: 1px solid var(--border-color, #ddd); padding: 8px; text-align: center; color: {status_color}; font-weight: 500;">{status_text}</td>'
            
            # Кнопки действий
            html += '<td style="border: 1px solid var(--border-color, #ddd); padding: 8px; text-align: center;">'
            html += f'<a href="/admin/control/stage/{stage.pk}/" style="color: #28a745; text-decoration: none; margin-right: 5px;" title="Просмотреть">👁️</a>'
            html += f'<a href="/admin/control/stage/{stage.pk}/change/" style="color: #007cba; text-decoration: none; margin-right: 5px;" title="Редактировать">✏️</a>'
            html += f'<a href="/admin/control/stage/{stage.pk}/delete/" style="color: #dc3545; text-decoration: none;" title="Удалить">🗑️</a>'
            html += '</td>'
            
            html += '</tr>'
        
        html += '</tbody>'
        html += '</table>'
        html += '</div>'
        
        # Итоговая информация
        html += '<div style="margin-top: 15px; padding: 10px; border-radius: 4px; border: 1px solid var(--border-color, #dee2e6);">'
        html += f'<strong>Всего этапов:</strong> {stages.count()} | '
        html += f'<span style="color: #28a745;">Активных: {stages.filter(is_active=True).count()}</span> | '
        html += f'<span style="color: #6c757d;">Неактивных: {stages.filter(is_active=False).count()}</span>'
        html += '</div>'
        
        return format_html(html)
    
    get_all_stages.short_description = 'Все этапы проекта'


class ObjectAdmin(admin.ModelAdmin):
    """Админка для объектов"""
    form = ObjectForm
    list_display = [
        'name', 'project', 'address', 'planned_start_date', 
        'planned_end_date', 'estimated_budget', 'is_active'
    ]
    list_filter = ['is_active', 'project', 'planned_start_date', 'planned_end_date']
    search_fields = ['name', 'address', 'project__name']
    readonly_fields = ['created_at', 'updated_at', 'get_all_transactions']
    date_hierarchy = 'planned_start_date'
    autocomplete_fields = ['project']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'project', 'address', 'planned_start_date', 'planned_end_date', 'actual_end_date', 'estimated_budget', 'is_active')
        }),
        ('Все транзакции объекта', {
            'fields': ('get_all_transactions',),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/transactions-list/',
                self.admin_site.admin_view(self.transactions_list_view),
                name='control_object_transactions_list',
            ),
        ]
        return custom_urls + urls
    
    def get_all_transactions(self, obj):
        """Показать все транзакции объекта (AJAX список)."""
        if not obj.pk:
            return 'Сохраните объект для просмотра транзакций'
        from django.utils.html import format_html
        from django.template.loader import render_to_string
        from django.core.paginator import Paginator
        from django.urls import reverse
        from .models import Transaction
        qs = get_transactions_for_object(obj)
        if not hasattr(qs, 'filter'):
            qs_ids = [t.id for t in qs]
            qs = Transaction.objects.filter(id__in=qs_ids).order_by('-date', '-id')
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        base_url = reverse('admin:control_object_transactions_list', args=[obj.pk])
        html_inner = render_to_string('admin/control/estimate/transactions_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': 20,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        })
        return format_html('<div id="tx-list">{}</div>', html_inner)

    def transactions_list_view(self, request, object_id):
        from django.shortcuts import get_object_or_404, render
        from django.core.paginator import Paginator
        from .models import Object as BuildObject, Transaction
        build_object = get_object_or_404(BuildObject, pk=object_id)
        qs = get_transactions_for_object(build_object)
        if not hasattr(qs, 'filter'):
            qs_ids = [t.id for t in qs]
            qs = Transaction.objects.filter(id__in=qs_ids).order_by('-date', '-id')
        try:
            per_page = int(request.GET.get('per_page', 20))
        except Exception:
            per_page = 20
        if per_page < 5: per_page = 5
        if per_page > 500: per_page = 500
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(request.GET.get('page') or 1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        from django.urls import reverse
        base_url = reverse('admin:control_object_transactions_list', args=[build_object.pk])
        return render(request, 'admin/control/estimate/transactions_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': per_page,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        })
    
    get_all_transactions.short_description = 'Все транзакции объекта'


class EstimateInline(admin.TabularInline):
    """Инлайн для смет"""
    model = Estimate
    extra = 0
    fields = ['status', 'get_client_total', 'get_contractor_total', 'get_income_total', 'created_at']
    readonly_fields = ['get_client_total', 'get_contractor_total', 'get_income_total', 'created_at', 'updated_at']
    
    def get_client_total(self, obj):
        """Сумма для заказчика"""
        if obj.pk:
            return f"{obj.get_client_total():,.2f} руб."
        return '-'
    get_client_total.short_description = 'Для заказчика'
    
    def get_contractor_total(self, obj):
        """Сумма для исполнителя"""
        if obj.pk:
            return f"{obj.get_contractor_total():,.2f} руб."
        return '-'
    get_contractor_total.short_description = 'Для исполнителя'
    
    def get_income_total(self, obj):
        """Доход по смете"""
        if obj.pk:
            return f"{obj.get_income_total():,.2f} руб."
        return '-'
    get_income_total.short_description = 'Доход'


class StageAdmin(admin.ModelAdmin):
    """Админка для этапов"""
    list_display = ['name', 'object', 'order', 'planned_start_date', 'planned_end_date', 'is_active']
    list_filter = ['is_active', 'object__project', 'planned_start_date']
    search_fields = ['name', 'object__name']
    readonly_fields = ['created_at', 'updated_at', 'get_all_transactions']
    ordering = ['object', 'order']
    inlines = [EstimateInline]
    autocomplete_fields = ['object']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'object', 'order', 'planned_start_date', 'planned_end_date', 'is_active')
        }),
        ('Все транзакции этапа', {
            'fields': ('get_all_transactions',),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:stage_id>/transactions-list/',
                self.admin_site.admin_view(self.transactions_list_view),
                name='control_stage_transactions_list',
            ),
        ]
        return custom_urls + urls
    
    def get_all_transactions(self, obj):
        """Показать все транзакции этапа (AJAX список)."""
        if not obj.pk:
            return 'Сохраните этап для просмотра транзакций'
        from django.utils.html import format_html
        from django.template.loader import render_to_string
        from django.core.paginator import Paginator
        from django.urls import reverse
        from .models import Transaction
        qs = get_transactions_for_stage(obj)
        if not hasattr(qs, 'filter'):
            qs_ids = [t.id for t in qs]
            qs = Transaction.objects.filter(id__in=qs_ids).order_by('-date', '-id')
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        base_url = reverse('admin:control_stage_transactions_list', args=[obj.pk])
        html_inner = render_to_string('admin/control/estimate/transactions_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': 20,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        })
        return format_html('<div id="tx-list">{}</div>', html_inner)

    def transactions_list_view(self, request, stage_id):
        from django.shortcuts import get_object_or_404, render
        from django.core.paginator import Paginator
        from .models import Stage, Transaction
        stage = get_object_or_404(Stage, pk=stage_id)
        qs = get_transactions_for_stage(stage)
        if not hasattr(qs, 'filter'):
            qs_ids = [t.id for t in qs]
            qs = Transaction.objects.filter(id__in=qs_ids).order_by('-date', '-id')
        try:
            per_page = int(request.GET.get('per_page', 20))
        except Exception:
            per_page = 20
        if per_page < 5: per_page = 5
        if per_page > 500: per_page = 500
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(request.GET.get('page') or 1)
        all_total_income = sum(t.amount for t in qs.filter(transaction_type='income'))
        all_total_expense = sum(t.amount for t in qs.filter(transaction_type='expense'))
        all_total_net = all_total_income - all_total_expense
        from django.urls import reverse
        base_url = reverse('admin:control_stage_transactions_list', args=[stage.pk])
        return render(request, 'admin/control/estimate/transactions_list.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'per_page': per_page,
            'base_url': base_url,
            'all_total_income': all_total_income,
            'all_total_expense': all_total_expense,
            'all_total_net': all_total_net,
        })
    
    get_all_transactions.short_description = 'Все транзакции этапа'



class WorkTypeAdmin(admin.ModelAdmin):
    """Админка для видов работ"""
    form = WorkTypeForm
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


class MaterialTypeAdmin(admin.ModelAdmin):
    """Админка для видов материалов"""
    form = MaterialTypeForm
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


class PriceItemAdmin(admin.ModelAdmin):
    """Админка для прайсовых позиций"""
    list_display = ['name', 'material', 'work_type', 'unit', 'price_per_unit', 'is_active', 'created_at']
    list_filter = ['is_active', 'unit', 'created_at']
    search_fields = ['name', 'material__name', 'work_type__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['material', 'work_type']


# ContractorAdmin удален - теперь контрагенты = пользователи


class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий транзакций"""
    form = CategoryForm
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


class TransactionAdmin(admin.ModelAdmin):
    """Админка для транзакций"""
    form = TransactionForm
    list_display = [
        'date', 'transaction_type', 'category', 'contractor', 'amount', 
        'get_signed_amount', 'description', 'get_project', 'get_object_name', 'get_stage'
    ]
    list_filter = (
        'transaction_type',
        CategoryAutocompleteFilter,
        EstimateAutocompleteFilter,
        EstimateItemAutocompleteFilter,
        'date', 'created_at'
    )
    search_fields = [
        'description', 'contractor__first_name', 'contractor__last_name', 
        'contractor__phone', 'category__name',
        'estimate__stage__name', 'estimate__stage__object__name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    list_per_page = 25  # Пагинация - 25 записей на странице
    list_max_show_all = 100  # Максимум записей для показа всех
    autocomplete_fields = ['category', 'contractor', 'stage', 'estimate', 'estimate_item']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('date', 'transaction_type', 'category', 'contractor', 'amount', 'description')
        }),
        ('Привязка к проекту', {
            'fields': ('stage', 'estimate', 'estimate_item'),
            'classes': ('collapse',)
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_project(self, obj):
        """Получить проект"""
        project = obj.get_project()
        return project.name if project else '-'
    get_project.short_description = 'Проект'
    
    def get_object_name(self, obj):
        """Получить объект"""
        object_obj = obj.get_object()
        return object_obj.name if object_obj else '-'
    get_object_name.short_description = 'Объект'
    
    def get_stage(self, obj):
        """Получить этап"""
        stage = obj.get_stage()
        return stage.name if stage else '-'
    get_stage.short_description = 'Этап'
    
    def get_signed_amount(self, obj):
        """Получить сумму со знаком"""
        return f"{obj.get_signed_amount():,.2f} руб."
    get_signed_amount.short_description = 'Сумма со знаком'


# Регистрация моделей в админке
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Object, ObjectAdmin)
admin.site.register(Stage, StageAdmin)
admin.site.register(Estimate, EstimateAdmin)
admin.site.register(EstimateItem, EstimateItemAdmin)
admin.site.register(PriceItem, PriceItemAdmin)
admin.site.register(WorkType, WorkTypeAdmin)
admin.site.register(MaterialType, MaterialTypeAdmin)
# Contractor удален - используем CustomUser
admin.site.register(Category, CategoryAdmin)
admin.site.register(Transaction, TransactionAdmin)
