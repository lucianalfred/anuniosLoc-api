from django.utils import timezone
from .models import Session, User
import logging
import uuid


logger = logging.getLogger(__name__)

def validate_session(session_id):
    """Valida se uma sessão é válida"""
    if not session_id:
        return False
    
    try:
        session = Session.objects.get(id=session_id, is_valid=True)
        if session.expires_at < timezone.now():
            session.is_valid = False
            session.save()
            return False
        return True
    except Session.DoesNotExist:
        return False



def get_user_from_session(session_id):
    """
    Obtém o usuário a partir do ID da sessão.
    Agora session_id pode ser string (para UUID) ou inteiro.
    """
    if not session_id:
        return None
    
    try:
        # Primeiro tenta como inteiro (AutoField)
        try:
            session_id_int = int(session_id)
            session = Session.objects.get(id=session_id_int, is_valid=True)
        except (ValueError, Session.DoesNotExist):
            # Se não for número, tenta como string (token)
            session = Session.objects.get(token=session_id, is_valid=True)
        
        # Verifica se expirou
        if session.expires_at < timezone.now():
            session.is_valid = False
            session.save()
            return None
            
        return session.user
        
    except Session.DoesNotExist:
        return None
    except Exception as e:
        print(f"Erro ao buscar sessão: {e}")
        return None
    
def create_session(user, duration_days=7):
    """Cria uma nova sessão para o usuário"""
    from datetime import timedelta
    session = Session.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(days=duration_days)
    )
    return session