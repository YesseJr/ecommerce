def sidebar_context(request):
    """Inject nav items + low-stock alerts into every template."""
    from apps.inventory.models import Fragrance
    low_stock_items = []
    low_stock_count = 0
    if request.user.is_authenticated:
        all_items = [f for f in Fragrance.objects.filter(is_active=True) if f.is_low_stock]
        low_stock_items = all_items[:8]
        low_stock_count = len(all_items)
    return {
        'low_stock_count': low_stock_count,
        'low_stock_items': low_stock_items,
    }
