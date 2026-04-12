from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def total_by_type(items, tipo_value):
    """
    Calcula o total de valores de itens filtrados por tipo.
    Uso: {{ lancamentos|total_by_type:1 }}
    Retorna a soma de valores onde item.tipo == tipo_value
    """
    if not items:
        return Decimal("0")
    
    total = Decimal("0")
    for item in items:
        if hasattr(item, 'tipo') and item.tipo == int(tipo_value):
            valor = getattr(item, 'valor', 0)
            if valor is None:
                valor = 0
            try:
                total += Decimal(str(valor))
            except (ValueError, TypeError):
                pass
    return total


@register.filter
def calculate_saldo(items):
    """
    Calcula o saldo (entradas - saídas) para lançamentos financeiros.
    Pressupõe que items sejam LancamentoFinanceiro com tipo (1=entrada, 2=saída)
    Uso: {{ lancamentos|calculate_saldo }}
    """
    if not items:
        return Decimal("0")
    
    entradas = Decimal("0")
    saidas = Decimal("0")
    
    for item in items:
        if hasattr(item, 'valor') and hasattr(item, 'tipo'):
            valor = item.valor
            if valor is None:
                valor = 0
                
            try:
                valor = Decimal(str(valor))
            except (ValueError, TypeError):
                valor = Decimal("0")
            
            if item.tipo == 1:  # Entrada
                entradas += valor
            elif item.tipo == 2:  # Saída
                saidas += valor
    
    return entradas - saidas


@register.filter
def sum_values(items, attr='valor'):
    """
    Soma valores de um atributo específico de items.
    Uso: {{ items|sum_values:'valor' }} ou {{ items|sum_values }}
    """
    if not items:
        return Decimal("0")
    
    total = Decimal("0")
    for item in items:
        try:
            value = getattr(item, attr, 0)
            if value is None:
                value = 0
            total += Decimal(str(value))
        except (ValueError, TypeError, AttributeError):
            pass
    
    return total


@register.filter
def count_by_type(items, tipo_value):
    """
    Conta quantos items correspondem a um tipo específico.
    Uso: {{ lancamentos|count_by_type:1 }}
    """
    if not items:
        return 0
    
    count = 0
    for item in items:
        if hasattr(item, 'tipo') and item.tipo == int(tipo_value):
            count += 1
    return count


@register.filter
def safe_decimal(value, default="0"):
    """
    Converte valor para Decimal com segurança.
    Uso: {{ value|safe_decimal:"0" }}
    """
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return Decimal(default)


@register.filter
def format_currency(value):
    """
    Formata valor como moeda brasileira sem símbolo.
    Uso: {{ value|format_currency }}
    Retorna: 1.234,56 (sem R$)
    """
    try:
        decimal_value = Decimal(str(value))
    except (ValueError, TypeError):
        decimal_value = Decimal("0")
    
    # Formata com 2 casas decimais
    formatted = f"{decimal_value:,.2f}"
    # Substitui , por . e . por , (formato brasileiro)
    formatted = formatted.replace('.', '|').replace(',', '.').replace('|', ',')
    return formatted


@register.filter
def get_display(obj, field_name):
    """
    Obtém o display de um field (ex: get_tipo_display).
    Uso: {{ item|get_display:'tipo' }}
    """
    try:
        method = getattr(obj, f'get_{field_name}_display', None)
        if method and callable(method):
            return method()
        return getattr(obj, field_name, '')
    except Exception:
        return ''


@register.filter
def group_by_type(items):
    """
    Agrupa items por tipo (para lançamentos financeiros).
    Uso: {% for tipo, items_list in lancamentos|group_by_type.items %}
    """
    if not items:
        return {}
    
    grouped = {}
    for item in items:
        if hasattr(item, 'tipo'):
            tipo = item.tipo
            if tipo not in grouped:
                grouped[tipo] = []
            grouped[tipo].append(item)
    return grouped


@register.filter
def percentage(value, total):
    """
    Calcula percentual de um valor em relação ao total.
    Uso: {{ valor|percentage:total }}
    Retorna: 45.67 (sem %)
    """
    try:
        value_dec = Decimal(str(value))
        total_dec = Decimal(str(total))
        if total_dec == 0:
            return Decimal("0")
        percentual = (value_dec / total_dec) * 100
        return percentual.quantize(Decimal('0.01'))
    except (ValueError, TypeError):
        return Decimal("0")


@register.filter
def default_if_zero(value, default_text="—"):
    """
    Retorna texto padrão se valor for 0 ou None.
    Uso: {{ value|default_if_zero:"N/A" }}
    """
    try:
        decimal_value = Decimal(str(value))
        if decimal_value == 0:
            return default_text
        return value
    except (ValueError, TypeError):
        if value is None or value == 0:
            return default_text
        return value
