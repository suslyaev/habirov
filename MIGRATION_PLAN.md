# План миграции: Объединение Contractor и CustomUser

## Шаг 1: Расширить модель CustomUser

Добавить поля:
```python
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Существующие поля
    phone = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    
    # НОВЫЕ ПОЛЯ (для контрагентов)
    company_name = models.CharField('Название компании', max_length=200, blank=True)
    contacts = models.TextField('Контакты', blank=True)
    address = models.TextField('Адрес', blank=True)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    bank_details = models.TextField('Банковские реквизиты', blank=True)
    
    # Флаг типа
    is_contractor = models.BooleanField('Является контрагентом', default=False)
    
    # Остальные поля...
```

## Шаг 2: Создать миграцию данных

1. Создать миграцию для добавления полей
2. Миграция данных: перенести всех Contractor в CustomUser
3. Обновить связи (Project.contractor → Project.contractor_user)
4. Удалить модель Contractor

## Шаг 3: Обновить админку

- CustomUserAdmin: показывать все поля
- Фильтры: is_staff, is_contractor
- Разные формсеты для сотрудников и контрагентов

## Восстановление из бекапа

Если что-то пойдет не так:
```bash
python manage.py loaddata backup_20251107_151319.json
```

## Альтернатива: OneToOneField

Если хотим сохранить разделение, но связать:
```python
class Contractor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    # остальные поля...
```

Это позволит:
- Контрагенту опционально иметь аккаунт
- Сохранить текущую структуру
- Постепенно мигрировать

