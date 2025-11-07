from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
import uuid
from django.core.exceptions import ValidationError


PHONE_PATTERNS = {
    "ru": ("+7", 10),
    "uk": ("+44", 10),
}

STATUS_MODEL = (
    ('announced', 'Заявлен'),
    ('invited', 'Приглашён'),
    ('registered', 'Зарегистрирован'),
    ('cancelled', 'Отменён'),
    ('visited', 'Зачекинен')
)


class CustomUserManager(BaseUserManager):
    """
    Менеджер пользователей, использующий телефон как логин (USERNAME_FIELD).
    """
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Телефон обязателен для создания пользователя")
        phone = str(phone).strip()
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя с логином по телефону.
    """
    phone = models.CharField(max_length=20, unique=True, verbose_name='Телефон')
    first_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='Имя')
    last_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='Фамилия')

    ext_id = models.CharField(max_length=150, blank=True, null=True, verbose_name='Внешний ID')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    auth_token = models.UUIDField(blank=True, null=True, unique=True)

    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []  # Если хотите, можно добавить first_name/last_name

    def generate_auth_token(self):
        self.auth_token = uuid.uuid4()
        self.save(update_fields=['auth_token'])
        return self.auth_token
    
    def get_short_name(self):
        if self.first_name:
            return f"{self.first_name or ''}".strip()
        return self.phone
    
    def clean(self):
        """
        Проверяет корректность номера перед сохранением.
        """
        super().clean()  # Вызываем стандартную валидацию модели

        phone = self.phone.strip()
        for code, length in PHONE_PATTERNS.values():
            if phone.startswith(code) and len(phone) == len(code) + length:
                return  # Валидация прошла

        raise ValidationError(f"Некорректный номер телефона: {phone}. Доступные форматы: " +
                              ", ".join(f"{code}X...X ({length} цифр)" for code, length in PHONE_PATTERNS.values()))

    class Meta:
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        if self.last_name or self.first_name:
            return f"{self.last_name or ''} {self.first_name or ''}".strip()
        return self.phone


# Дополнительные модели для справочников
class WorkType(models.Model):
    """Виды работ"""
    name = models.CharField('Название', max_length=200, unique=True)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Вид работ'
        verbose_name_plural = 'Виды работ'
        ordering = ['name']

    def __str__(self):
        return self.name


class MaterialType(models.Model):
    """Виды материалов"""
    name = models.CharField('Название', max_length=200, unique=True)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Вид материала'
        verbose_name_plural = 'Виды материалов'
        ordering = ['name']

    def __str__(self):
        return self.name


class PriceItem(models.Model):
    """Прайсовая позиция: либо материал, либо вид работ (строго одно из двух)"""
    name = models.CharField('Название', max_length=255, blank=True)
    material = models.ForeignKey(
        MaterialType,
        on_delete=models.PROTECT,
        verbose_name='Материал',
        related_name='price_items',
        null=True,
        blank=True,
    )
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.PROTECT,
        verbose_name='Вид работ',
        related_name='price_items',
        null=True,
        blank=True,
    )
    unit = models.CharField('Единица измерения', max_length=50)
    price_per_unit = models.DecimalField('Цена за единицу', default=1,max_digits=12, decimal_places=2)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Позиция прайса'
        verbose_name_plural = 'Позиции прайса'
        ordering = ['-is_active', 'name']

    def clean(self):
        super().clean()
        # Ровно одно из полей material/work_type должно быть заполнено
        if bool(self.material) == bool(self.work_type):
            raise ValidationError('Заполните либо \'Материал\', либо \'Вид работ\', но не оба сразу.')

    def save(self, *args, **kwargs):
        # Автогенерация name при пустом значении
        if not self.name:
            base_name = self.material.name if self.material else (self.work_type.name if self.work_type else '')
            if base_name:
                self.name = f"{base_name} {self.unit} {self.price_per_unit}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or 'Позиция прайса'

# Модель Contractor удалена - теперь используем CustomUser для контрагентов


class Category(models.Model):
    """Категории транзакций"""
    name = models.CharField('Название', max_length=200, unique=True)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name





class Project(models.Model):
    """Проект для объединения объектов (например, яхт-клуб)"""
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    contractor = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name='Заказчик',
        related_name='projects'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.contractor})"


class Object(models.Model):
    """Объект строительства (например, баня, домик, веранда)"""
    name = models.CharField('Название', max_length=200)
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        verbose_name='Проект',
        related_name='objects'
    )
    address = models.TextField('Адрес', blank=True)
    planned_start_date = models.DateField('Плановая дата начала', null=True, blank=True)
    planned_end_date = models.DateField('Плановая дата окончания', null=True, blank=True)
    actual_end_date = models.DateField('Фактическая дата окончания', null=True, blank=True)
    estimated_budget = models.DecimalField(
        'Примерный бюджет', 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        ordering = ['project', 'name']

    def __str__(self):
        return f"{self.name} - {self.project.name}"


class Stage(models.Model):
    """Этап строительства (фундамент, крыша, отделка и т.д.)"""
    order = models.PositiveIntegerField('Порядок', default=0)
    object = models.ForeignKey(
        Object, 
        on_delete=models.CASCADE, 
        verbose_name='Объект',
        related_name='stages'
    )
    name = models.CharField('Название', max_length=200)
    planned_start_date = models.DateField('Плановая дата начала', null=True, blank=True)
    planned_end_date = models.DateField('Плановая дата окончания', null=True, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Этап'
        verbose_name_plural = 'Этапы'
        ordering = ['object', 'order']
        unique_together = ['object', 'order']

    def __str__(self):
        return f"{self.object.name} - {self.name} (этап {self.order})"


class Estimate(models.Model):
    """Смета по этапу"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('pending', 'На согласовании'),
        ('approved', 'Утвержден'),
        ('completed', 'Выполнен'),
    ]
    
    stage = models.ForeignKey(
        Stage, 
        on_delete=models.CASCADE, 
        verbose_name='Этап',
        related_name='estimates'
    )
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Смета'
        verbose_name_plural = 'Сметы'
        ordering = ['stage', '-created_at']

    def __str__(self):
        return f"Смета {self.stage.name} - {self.get_status_display()}"
    
    def get_client_total(self):
        """Сумма для заказчика (с наценками)"""
        return sum(item.client_price for item in self.items.all())
    
    def get_contractor_total(self):
        """Сумма для исполнителя (без наценок, с откатами)"""
        return sum(item.contractor_price for item in self.items.all())
    
    def get_income_total(self):
        """Общий доход по смете"""
        return sum(item.income_amount for item in self.items.all())
    
    def get_base_total(self):
        """Базовая сумма (без наценок и откатов)"""
        return sum(item.base_price for item in self.items.all())





class EstimateItem(models.Model):
    """Элемент сметы (материал, доставка, зарплата и т.д.)"""
    
    INCOME_TYPE_CHOICES = [
        ('', 'Без дохода'),
        ('markup', 'Наценка'),
        ('kickback', 'Откат'),
    ]
    
    estimate = models.ForeignKey(
        Estimate, 
        on_delete=models.CASCADE, 
        verbose_name='Смета',
        related_name='items'
    )
    
    # Связь с прайсовой позицией
    price_item = models.ForeignKey(
        PriceItem,
        on_delete=models.SET_NULL,
        verbose_name='Позиция прайса',
        related_name='estimate_items',
        null=True,
        blank=True,
    )
    
    # Основные поля
    description = models.CharField('Описание', max_length=200, null=True, blank=True)
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2)
    
    # Расчетные поля (автоматически заполняются)
    base_price = models.DecimalField('Базовая цена', max_digits=15, decimal_places=2, default=0)
    income_amount = models.DecimalField('Сумма дохода', max_digits=10, decimal_places=2, default=0)
    client_price = models.DecimalField('Сумма для клиента', max_digits=15, decimal_places=2, default=0)
    contractor_price = models.DecimalField('Сумма для исполнителя', max_digits=15, decimal_places=2, default=0)
    
    # Наценка/откат
    income_type = models.CharField('Вид дохода', max_length=20, choices=INCOME_TYPE_CHOICES, blank=True)
    income_value = models.DecimalField('Значение дохода', max_digits=10, decimal_places=2, default=0)
    is_percentage = models.BooleanField('Процент', default=False)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Элемент сметы'
        verbose_name_plural = 'Элементы сметы'
        ordering = ['estimate', 'id']

    def __str__(self):
        if self.price_item:
            return f"{self.price_item.name} - {self.estimate}"
        return f"Пункт сметы - {self.estimate}"

    def save(self, *args, **kwargs):
        # Если выбрана прайсовая позиция и цена не задана вручную, подставим из прайса
        if self.price_item and (self.unit_price is None or self.unit_price == 0):
            self.unit_price = self.price_item.price_per_unit
        # Автоматический расчет всех сумм
        self._calculate_amounts()
        super().save(*args, **kwargs)
    
    def _calculate_amounts(self):
        """Расчет всех сумм"""
        # Базовая цена = количество * цена за единицу
        if self.quantity and self.unit_price:
            self.base_price = self.quantity * self.unit_price
        else:
            self.base_price = 0
        
        # Расчет дохода
        if self.income_type and self.income_value:
            if self.is_percentage:
                # Процент от базовой цены
                self.income_amount = (self.base_price * self.income_value) / 100
            else:
                # Фиксированная сумма
                self.income_amount = self.income_value
        else:
            self.income_amount = 0
        
        # Расчет сумм для клиента и исполнителя
        if self.income_type == 'markup':
            # Наценка: клиент платит больше, исполнитель получает базовую сумму
            self.client_price = self.base_price + self.income_amount
            self.contractor_price = self.base_price
        elif self.income_type == 'kickback':
            # Откат: клиент платит базовую сумму, исполнитель получает меньше
            self.client_price = self.base_price
            self.contractor_price = self.base_price - self.income_amount
        else:
            # Без дохода: обе суммы равны базовой цене
            self.client_price = self.base_price
            self.contractor_price = self.base_price
    
    def get_item_name(self):
        """Получить название элемента в зависимости от типа"""
        if self.price_item:
            return self.price_item.name
        return "Позиция"
    
    def get_unit(self):
        """Получить единицу измерения из справочника"""
        if self.price_item:
            return self.price_item.unit
        return ""
    
    def get_income_display(self):
        """Получить отображение дохода"""
        if not self.income_type or not self.income_value:
            return '-'
        
        if self.is_percentage:
            return f"{self.income_value}%"
        else:
            return f"{self.income_value} руб."


class Transaction(models.Model):
    """Универсальная модель для всех движений средств"""
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
        ('transfer', 'Перевод'),
        ('debt_give', 'Дать в долг'),
        ('debt_receive', 'Получить в долг'),
        ('debt_repay', 'Вернуть долг'),
        ('debt_received', 'Получить возврат долга'),
    ]
    
    amount = models.DecimalField('Сумма', max_digits=15, decimal_places=2)
    transaction_type = models.CharField('Тип операции', max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория')
    contractor = models.ForeignKey(CustomUser, on_delete=models.PROTECT, verbose_name='Контрагент', null=True, blank=True)
    
    description = models.CharField('Описание', max_length=200, null=True, blank=True)
    date = models.DateField('Дата', default=timezone.now)
    
    # Связи с проектами/этапами/сметами
    stage = models.ForeignKey(
        Stage, 
        on_delete=models.CASCADE, 
        verbose_name='Этап',
        related_name='transactions',
        null=True, 
        blank=True
    )
    estimate = models.ForeignKey(
        Estimate, 
        on_delete=models.CASCADE, 
        verbose_name='Смета',
        related_name='transactions',
        null=True, 
        blank=True
    )
    estimate_item = models.ForeignKey(
        EstimateItem, 
        on_delete=models.SET_NULL, 
        verbose_name='Пункт сметы',
        related_name='transactions',
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} руб. ({self.date})"
    
    def get_signed_amount(self):
        """Возвращает сумму со знаком в зависимости от типа операции"""
        expense_types = ['expense', 'transfer', 'debt_give', 'debt_repay']
        return -self.amount if self.transaction_type in expense_types else self.amount
    
    def get_project(self):
        """Получить проект через этап или смету"""
        if self.stage:
            return self.stage.object.project
        elif self.estimate:
            return self.estimate.stage.object.project
        return None
    
    def get_object(self):
        """Получить объект через этап или смету"""
        if self.stage:
            return self.stage.object
        elif self.estimate:
            return self.estimate.stage.object
        return None
    
    def get_stage(self):
        """Получить этап напрямую или через смету"""
        if self.stage:
            return self.stage
        elif self.estimate:
            return self.estimate.stage
        return None

