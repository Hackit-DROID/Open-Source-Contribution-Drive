from django.shortcuts import render
from django.http import JsonResponse
from .models import Payment
from .currency_converter import MultiCurrencyBillingEngine

def payment_list(request):
    payments = Payment.objects.all()
    return render(request, "payment_list.html", {"payments": payments})


def multi_currency_billing_view(request):
    """API endpoint to calculate multi-currency booking quote and receipt."""
    try:
        subtotal = float(request.GET.get('subtotal', 100.0))
        tax_rate = float(request.GET.get('tax_rate', 0.10))
        target_currency = request.GET.get('currency', 'EUR').strip().upper()
        booking_id = request.GET.get('booking_id', 'QUOTE-001')
        guest_name = request.GET.get('guest_name', 'Guest')
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid billing parameters provided."}, status=400)

    engine = MultiCurrencyBillingEngine()
    try:
        receipt = engine.generate_guest_receipt(
            booking_id=booking_id,
            guest_name=guest_name,
            subtotal=subtotal,
            tax_rate=tax_rate,
            target_currency=target_currency,
        )
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({
        "status": "success",
        "receipt": receipt,
    })
