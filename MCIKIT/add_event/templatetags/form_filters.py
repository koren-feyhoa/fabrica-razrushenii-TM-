from django import template

register = template.Library()

@register.filter
def get_field(form, field_name):
    """Получает поле формы по имени"""
    try:
        return form[field_name]
    except KeyError:
        return None

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except (AttributeError, KeyError, TypeError):
        return None

@register.filter
def add(value, arg):
    """Складывает строки"""
    return str(value) + str(arg)

@register.filter
def get_errors(field):
    """Получает ошибки поля формы"""
    return field.errors if field else None

@register.filter
def startswith(text, starts):
    """Проверяет, начинается ли строка с указанного префикса"""
    if isinstance(text, str):
        return text.startswith(starts)
    return False
