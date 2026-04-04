from django.contrib.auth.models import Group, Permission


ROLE_GROUP_NAMES = {
    "admin": "Administrador",
    "gerente": "Gerente",
    "funcionario": "Funcionario",
}

ROLE_ALLOWED_MODELS = [
    "linhagem",
    "ave",
    "lote",
    "incubacao",
    "nascimento",
    "itemestoque",
    "movimentoestoque",
    "vacina",
    "medicamento",
    "aplicacaovacina",
    "tratamento",
    "venda",
    "lancamentofinanceiro",
]


def sync_role_groups(force=False):
    admin_group, _ = Group.objects.get_or_create(name=ROLE_GROUP_NAMES["admin"])
    gerente_group, _ = Group.objects.get_or_create(name=ROLE_GROUP_NAMES["gerente"])
    func_group, _ = Group.objects.get_or_create(name=ROLE_GROUP_NAMES["funcionario"])

    all_perms = Permission.objects.all()
    funcionario_perms = Permission.objects.filter(content_type__model__in=ROLE_ALLOWED_MODELS)

    if force or admin_group.permissions.count() != all_perms.count():
        admin_group.permissions.set(all_perms)
    if force or gerente_group.permissions.count() != all_perms.count():
        gerente_group.permissions.set(all_perms)
    if force or func_group.permissions.count() != funcionario_perms.count():
        func_group.permissions.set(funcionario_perms)

    return {
        "admin": admin_group,
        "gerente": gerente_group,
        "funcionario": func_group,
    }


def assign_user_role_group(user):
    groups = sync_role_groups()
    if user.is_superuser or user.role == user.ADMIN:
        target_group = groups["admin"]
    elif user.role == user.GERENTE:
        target_group = groups["gerente"]
    else:
        target_group = groups["funcionario"]

    current_ids = set(user.groups.values_list("id", flat=True))
    if current_ids != {target_group.id}:
        user.groups.set([target_group])
        for cache_name in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
            if hasattr(user, cache_name):
                delattr(user, cache_name)
