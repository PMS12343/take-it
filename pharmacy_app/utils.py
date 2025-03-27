from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages
from django.db import models
from functools import wraps
from datetime import timedelta
import xhtml2pdf.pisa as pisa
import io

def render_to_pdf(template_src, context_dict={}):
    """Generate PDF from HTML template with context data"""
    template = get_template(template_src)
    html = template.render(context_dict)
    
    # Fix CSS for xhtml2pdf
    # The main issue is with selectors using :not() pseudo-class
    # Replace problematic CSS with simpler alternatives
    html = html.replace(':not([controls])', '.with-controls')
    html = html.replace(':not(.btn-large)', '.btn-normal')
    html = html.replace(':not(.btn)', '.non-btn')
    
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def check_role_permission(user, allowed_roles):
    """Check if user has any of the allowed roles"""
    if user.is_superuser:
        return True
    
    try:
        user_role = user.profile.role
        return user_role in allowed_roles
    except:
        return False

def requires_role(allowed_roles):
    """Decorator to restrict view access based on user role"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if check_role_permission(request.user, allowed_roles):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
        return _wrapped_view
    return decorator

def get_low_stock_drugs():
    """Get all drugs with stock below reorder level"""
    from .models import Drug
    return Drug.objects.filter(
        is_active=True, 
        stock_quantity__lte=models.F('reorder_level')
    ).order_by('stock_quantity')

def get_expiring_drugs():
    """Get all drugs expiring within 2 months"""
    from .models import Drug
    today = timezone.now().date()
    two_months_later = today + timedelta(days=60)
    return Drug.objects.filter(
        is_active=True,
        expiry_date__gt=today,
        expiry_date__lte=two_months_later
    ).order_by('expiry_date')

def notifications_processor(request):
    """Context processor to add notifications to all templates"""
    if request.user.is_authenticated:
        low_stock_count = get_low_stock_drugs().count()
        expiring_count = get_expiring_drugs().count()
        total_notifications = low_stock_count + expiring_count
        
        return {
            'low_stock_count': low_stock_count,
            'expiring_count': expiring_count,
            'total_notifications': total_notifications,
        }
    return {}
