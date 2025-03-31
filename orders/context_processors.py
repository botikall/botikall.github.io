from .models import Type

def navbar_data(request):
    """Передає список категорій продукції у всі шаблони."""
    types = Type.objects.all()
    return {"product_types": types}