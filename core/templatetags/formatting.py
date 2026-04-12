from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _to_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _format_decimal(value, decimals=2, strip_trailing=False):
    dec = _to_decimal(value)
    if dec is None:
        return "-"
    q = Decimal("1." + ("0" * decimals))
    dec = dec.quantize(q)
    s = f"{dec:.{decimals}f}"
    if strip_trailing:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


@register.filter
def int_if_whole(value):
    dec = _to_decimal(value)
    if dec is None:
        return "-"
    if dec == dec.to_integral():
        return str(int(dec))
    return _format_decimal(dec, 2, strip_trailing=True)


@register.filter
def brl(value):
    return f"R$ {_format_decimal(value, 2, strip_trailing=False)}"


@register.filter
def qty(value, unidade=""):
    unidade = (unidade or "").lower().strip()
    if unidade in {"un", "und", "unidade", "aves", "ovos"}:
        return int_if_whole(value)
    return _format_decimal(value, 2, strip_trailing=True)


@register.filter
def num(value):
    return _format_decimal(value, 2, strip_trailing=True)


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except Exception:
        return None
