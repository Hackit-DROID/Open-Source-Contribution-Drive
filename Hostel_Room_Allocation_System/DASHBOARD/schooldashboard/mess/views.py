from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Mess
from .forms import MessForm
from .reorder_engine import (
    MessInventoryDepletionEngine,
    MessSupplyItem,
    ReorderAlert,
    REORDER_THRESHOLD_DAYS,
)

class MessListView(ListView):
    model = Mess
    template_name = 'mess/dashboard.html'
    context_object_name = 'meals'

class MessCreateView(CreateView):
    model = Mess
    form_class = MessForm
    template_name = 'mess/form.html'
    success_url = reverse_lazy('mess_display')

class MessUpdateView(UpdateView):
    model = Mess
    form_class = MessForm
    template_name = 'mess/form.html'
    success_url = reverse_lazy('mess_display')

class MessDeleteView(DeleteView):
    model = Mess
    template_name = 'mess/confirm_delete.html'
    success_url = reverse_lazy('mess_display')


def mess_reorder_alerts_view(request):
    """API endpoint evaluating mess supply inventory and returning depletion predictions."""
    try:
        student_count = int(request.GET.get('student_count', Mess.objects.count() or 100))
    except (ValueError, TypeError):
        student_count = 100

    engine = MessInventoryDepletionEngine()
    # Default sample inventory items if not configured
    default_items = [
        MessSupplyItem("RICE-01", "Rice", "kg", current_stock=50.0, daily_per_student=0.25),
        MessSupplyItem("DAL-01", "Lentils/Dal", "kg", current_stock=20.0, daily_per_student=0.10),
        MessSupplyItem("OIL-01", "Cooking Oil", "liters", current_stock=8.0, daily_per_student=0.04),
    ]
    predictions = engine.evaluate_inventory(default_items, student_count)
    alerts = engine.get_reorder_alerts(default_items, student_count)

    return JsonResponse({
        "student_count": student_count,
        "reorder_threshold_days": REORDER_THRESHOLD_DAYS,
        "active_alerts_count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
        "inventory_status": [
            {
                "item_id": p.item_id,
                "item_name": p.item_name,
                "current_stock": p.current_stock,
                "daily_consumption": p.daily_consumption,
                "days_left": p.days_left,
                "needs_reorder": p.needs_reorder,
            }
            for p in predictions
        ],
    })
