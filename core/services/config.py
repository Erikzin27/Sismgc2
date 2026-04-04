from django.core.cache import cache

from core.models import ConfiguracaoSistema


CONFIG_CACHE_KEY = "core.configuracao_sistema.pk1"
CONFIG_CACHE_TIMEOUT = 300


def get_configuracao_sistema():
    config = cache.get(CONFIG_CACHE_KEY)
    if config is None:
        config, _ = ConfiguracaoSistema.objects.get_or_create(pk=1)
        cache.set(CONFIG_CACHE_KEY, config, CONFIG_CACHE_TIMEOUT)
    return config


def invalidate_configuracao_sistema_cache():
    cache.delete(CONFIG_CACHE_KEY)
