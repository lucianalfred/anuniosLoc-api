from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import datetime, timedelta
import json
import math
from django.db.models import Q
import uuid

from .models import User, Session, Location, Announcement, UserProfile, SavedAnnouncement, ViewedAnnouncement
from .serializers import (
    UserSerializer, SessionSerializer, LocationSerializer, 
    AnnouncementSerializer, AnnouncementRequestSerializer,
    UserProfileSerializer, AuthSerializer, AuthResponseSerializer,
    LocationRequestSerializer
)
from .utils import validate_session, get_user_from_session

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = AuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(username=username, password=password)
        
        session = Session.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=7),
            token=str(uuid.uuid4())
        )
        
        response_serializer = AuthResponseSerializer({
            'sessionId': session.token, 
            'username': user.username
        })
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = AuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        session = Session.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=7),
            token=str(uuid.uuid4())
        )
        
        response_serializer = AuthResponseSerializer({
            'sessionId': session.token,  # Envia o token
            'username': user.username
        })
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    
    def get_queryset(self):
        session_id = self.request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Location.objects.none()
        
        # Retorna todos os locais (públicos)
        return Location.objects.all()
    
    def create(self, request, *args, **kwargs):
        print("=== CREATE CALLED ===")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
        print(f"URL kwargs: {kwargs}")
        print(f"Has 'pk' in kwargs: {'pk' in kwargs}")
        print(f"Has 'id' in kwargs: {'id' in kwargs}")
    
        # Se tiver pk/id nos kwargs, algo está errado
        if 'pk' in kwargs or 'id' in kwargs:
            print(f"⚠️ AVISO: CREATE recebeu ID: {kwargs.get('pk', kwargs.get('id'))}")
            print("Isso não deveria acontecer!")
    
        session_id = request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = LocationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        location = Location.objects.create(
            name=data['name'],
            type=data.get('type', 'GPS'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            radius_meters=data.get('radius_meters', 100.00),
            wifi_ids_csv=data.get('wifi_ids_csv'),
            owner=user
        )
        
        return Response(
            LocationSerializer(location).data, 
            status=status.HTTP_201_CREATED
        )
        
    def destroy(self, request, *args, **kwargs):
        print("=== DESTROY CALLED ===")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
        print(f"URL kwargs: {kwargs}")
    
        try:
            # Tente obter o objeto para ver qual ID está sendo usado
            location = self.get_object()
            print(f"Tentando deletar local ID: {location.id}")
        except Exception as e:
            print(f"Erro no get_object(): {e}")
            print(f"Lookup value: {kwargs.get(self.lookup_field)}")
            session_id = request.headers.get('Session-Id')
            user = get_user_from_session(session_id)
        
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    # AGORA pegue o objeto
        location = self.get_object()
    
    # Apenas o dono pode apagar
        if location.owner != user:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
        location.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.filter(is_active=True)
    serializer_class = AnnouncementSerializer
    
    def get_queryset(self):
        session_id = self.request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Announcement.objects.none()
        
        return Announcement.objects.filter(is_active=True)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        session_id = self.request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        context['request'] = self.request
        if user:
            context['request'].user = user
        return context
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my')
    def my_announcements(self, request):
        session_id = request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = Announcement.objects.filter(owner=user, is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        session_id = request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        lat = request.query_params.get('lat', None)
        lon = request.query_params.get('lon', None)
        radius_km = float(request.query_params.get('radiusKm', 10.0))
        
        if not lat or not lon:
            return Response(
                {"error": "Latitude and longitude required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lon = float(lon)
            radius_meters = radius_km * 1000
        except ValueError:
            return Response(
                {"error": "Invalid coordinates"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fórmula Haversine simplificada
        queryset = Announcement.objects.filter(is_active=True)
        nearby_announcements = []
        
        for announcement in queryset:
            if announcement.location and announcement.location.latitude and announcement.location.longitude:
                # Cálculo de distância
                R = 6371000  # Raio da Terra em metros
                lat1 = math.radians(lat)
                lat2 = math.radians(float(announcement.location.latitude))
                delta_lat = math.radians(float(announcement.location.latitude) - lat)
                delta_lon = math.radians(float(announcement.location.longitude) - lon)
                
                a = math.sin(delta_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance = R * c
                
                if distance <= radius_meters:
                    nearby_announcements.append(announcement)
        
        serializer = self.get_serializer(nearby_announcements, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        session_id = request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
        serializer = AnnouncementRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
        data = serializer.validated_data
    
        
        location = data.get('location')
    
        announcement = Announcement.objects.create(
            title=data['title'],
            content=data['content'],
            owner=user,
            location=location,
            policy_type=data.get('policy_type', 'WHITELIST'),
            profile_restrictions_json=data.get('profile_restrictions_json'),
            start_time=data.get('start_time') or timezone.now(),
            end_time=data.get('end_time'),
            delivery_mode=data.get('delivery_mode', 'CENTRALIZED')
        )
    
        response_serializer = AnnouncementSerializer(
            announcement, 
            context=self.get_serializer_context()
        )
    
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='markSeen')
    def mark_seen(self, request, pk=None):
        session_id = request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            announcement = Announcement.objects.get(id=pk, is_active=True)
        except Announcement.DoesNotExist:
            return Response(
                {"error": "Announcement not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Marcar como visto
        ViewedAnnouncement.objects.get_or_create(
            user=user,
            announcement=announcement
        )
        
        # Incrementar contador de visualizações
        announcement.view_count += 1
        announcement.save()
        
        return Response(status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='save')
    def save_announcement(self, request, pk=None):
        session_id = request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            announcement = Announcement.objects.get(id=pk, is_active=True)
        except Announcement.DoesNotExist:
            return Response(
                {"error": "Announcement not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Salvar anúncio
        SavedAnnouncement.objects.get_or_create(
            user=user,
            announcement=announcement
        )
        
        return Response(status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='saved')
    def saved_announcements(self, request):
        session_id = request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return Response(
                {"error": "Invalid session"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        saved_ids = SavedAnnouncement.objects.filter(user=user).values_list('announcement_id', flat=True)
        queryset = Announcement.objects.filter(id__in=saved_ids, is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        session_id = self.request.headers.get('Session-Id')
        user = get_user_from_session(session_id)
        if not user:
            return UserProfile.objects.none()
        
        return UserProfile.objects.filter(user=user)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "service": "AnunciosLoc API"})
