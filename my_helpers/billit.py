"""Billit integration utilities."""

def format_invoice_data(invoice_items):
    """Format invoice data for Billit."""
    total = 0
    formatted_items = []
    
    for item in invoice_items:
        item_total = item.get("quantity", 1) * item.get("unit_price", 0)
        formatted_items.append({
            "description": item.get("description", ""),
            "quantity": item.get("quantity", 1),
            "unit_price": item.get("unit_price", 0),
            "total": item_total
        })
        total += item_total
    
    return {
        "items": formatted_items,
        "total_amount": total,
        "currency": "EUR"
    }

