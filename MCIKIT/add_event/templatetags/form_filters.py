from django import template
from django.template.defaultfilters import register

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
    if dictionary is None:
        return None
    return dictionary.get(str(key)) if isinstance(key, int) else dictionary.get(key)

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

@register.filter
def get_user_answers(extra_infos, user):
    """Получает все ответы пользователя на дополнительные вопросы"""
    from add_event.models import UserAnswer
    answers = UserAnswer.objects.filter(
        user=user,
        extra_info__in=extra_infos
    ).select_related('extra_info')
    return answers if answers.exists() else None
