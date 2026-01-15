from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from control.models import (
    CustomUser, Transaction, Category, Project,
    Stage, Estimate, EstimateItem, Object
)
from .serializers import (
    UserSerializer, TransactionSerializer, TransactionCreateSerializer,
    CategorySerializer, ProjectSerializer, StageSerializer,
    EstimateSerializer, EstimateItemSerializer, ObjectSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    API для авторизации по телефону и паролю
    Возвращает JWT токены
    """
    phone = request.data.get('phone')
    password = request.data.get('password')
    
    if not phone or not password:
        return Response(
            {'error': 'Укажите телефон и пароль'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=phone, password=password)
    
    if user is None:
        return Response(
            {'error': 'Неверный телефон или пароль'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Генерируем JWT токены
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """API для выхода"""
    return Response({'message': 'Успешный выход'}, status=status.HTTP_200_OK)


@api_view(['GET', 'HEAD'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Получить информацию о текущем пользователе"""
    if request.method == 'HEAD':
        return Response(status=status.HTTP_200_OK)
    return Response(UserSerializer(request.user).data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для категорий (только чтение)"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('name')


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для проектов (только чтение)"""
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.filter(is_active=True).select_related('contractor').order_by('name')


class ObjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для объектов (только чтение)"""
    serializer_class = ObjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Object.objects.filter(is_active=True).select_related('project').order_by('name')


class StageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для этапов (только чтение)"""
    serializer_class = StageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Stage.objects.filter(is_active=True).select_related('object').order_by('object', 'order')


class EstimateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для смет (только чтение)"""
    serializer_class = EstimateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Estimate.objects.all().select_related('stage').order_by('-created_at')


class EstimateItemViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для элементов сметы (только чтение)"""
    serializer_class = EstimateItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return EstimateItem.objects.all().select_related('estimate', 'price_item').order_by('estimate', 'id')


class ContractorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для контрагентов (пользователей) (только чтение)"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для транзакций
    Поддерживает создание, чтение, обновление
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer
    
    def get_queryset(self):
        """Фильтрация по параметрам"""
        queryset = Transaction.objects.all().select_related(
            'category', 'contractor', 'stage', 'estimate'
        ).order_by('-date', '-created_at')
        
        # Фильтр по проекту
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(
                stage__object__project_id=project_id
            ) | queryset.filter(
                estimate__stage__object__project_id=project_id
            )
        
        # Фильтр по дате
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.distinct()
