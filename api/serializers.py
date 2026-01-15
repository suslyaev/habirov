from rest_framework import serializers
from control.models import (
    CustomUser, Transaction, Category, Project, 
    Stage, Estimate, EstimateItem, Object
)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""
    class Meta:
        model = CustomUser
        fields = ['id', 'phone', 'first_name', 'last_name']


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active']


class ProjectSerializer(serializers.ModelSerializer):
    """Сериализатор проекта"""
    contractor_name = serializers.CharField(source='contractor.__str__', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'contractor', 'contractor_name', 'is_active']


class ObjectSerializer(serializers.ModelSerializer):
    """Сериализатор объекта"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Object
        fields = ['id', 'name', 'project', 'project_name', 'address', 'is_active']


class StageSerializer(serializers.ModelSerializer):
    """Сериализатор этапа"""
    object_name = serializers.CharField(source='object.name', read_only=True)
    
    class Meta:
        model = Stage
        fields = ['id', 'name', 'object', 'object_name', 'order', 'is_active']


class EstimateSerializer(serializers.ModelSerializer):
    """Сериализатор сметы"""
    stage_name = serializers.CharField(source='stage.__str__', read_only=True)
    
    class Meta:
        model = Estimate
        fields = ['id', 'stage', 'stage_name', 'status']


class EstimateItemSerializer(serializers.ModelSerializer):
    """Сериализатор элемента сметы"""
    estimate_name = serializers.CharField(source='estimate.__str__', read_only=True)
    item_name = serializers.CharField(source='get_item_name', read_only=True)
    
    class Meta:
        model = EstimateItem
        fields = ['id', 'estimate', 'estimate_name', 'item_name', 'quantity', 'unit_price']


class TransactionSerializer(serializers.ModelSerializer):
    """Сериализатор транзакции"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    contractor_name = serializers.CharField(source='contractor.__str__', read_only=True, allow_null=True)
    project_name = serializers.SerializerMethodField()
    stage_name = serializers.CharField(source='get_stage', read_only=True, allow_null=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'transaction_type', 'transaction_type_display',
            'category', 'category_name', 'contractor', 'contractor_name',
            'description', 'date', 'stage', 'stage_name', 'estimate', 'estimate_item',
            'project_name', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_project_name(self, obj):
        project = obj.get_project()
        return project.name if project else None


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания транзакции"""
    
    class Meta:
        model = Transaction
        fields = [
            'amount', 'transaction_type', 'category', 'contractor',
            'description', 'date', 'stage', 'estimate', 'estimate_item'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть больше нуля")
        return value


