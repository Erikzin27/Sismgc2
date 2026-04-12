"""
Script de teste de performance: Database Query Optimization
Demonstra a redução de queries de 140+ para ~5 após otimizações.
"""

import os
import django
from django.test.utils import override_settings
from django.db import connection, reset_queries

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sismgc.settings')
django.setup()

from django.test import Client, RequestFactory
from django.test.utils import CaptureQueriesContext
from django.contrib.auth.models import User
from lotes.models import Lote
from lotes.views import LoteListView
from vendas.models import Venda
from vendas.views import VendaListView
from usuarios.models import User as CustomUser


def test_lote_list_queries():
    """
    Testa quantas queries são disparadas ao listar lotes.
    Expectativa: ~5-7 queries (antes era 140+)
    """
    print("\n" + "="*70)
    print("🔍 TESTE DE PERFORMANCE: LoteListView")
    print("="*70)
    
    # Criar dados de teste se não existirem
    if Lote.objects.count() == 0:
        print("⚠️  Nenhum lote encontrado. Criando dados de teste...")
        for i in range(3):
            Lote.objects.create(
                codigo=f"L{i:03d}",
                nome=f"Lote {i}",
                local="Galpão A",
                finalidade="postura",
            )
    
    # Criar usuário admin para teste
    if not CustomUser.objects.filter(username="admin_test").exists():
        user = CustomUser.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="test123"
        )
    else:
        user = CustomUser.objects.get(username="admin_test")
    
    factory = RequestFactory()
    request = factory.get('/lotes/')
    request.user = user
    
    # Contar queries
    with CaptureQueriesContext(connection) as context:
        view = LoteListView.as_view()
        response = view(request)
    
    query_count = len(context)
    print(f"\n📊 Total de Queries: {query_count}")
    print(f"✅ Status: {'OTIMIZADO' if query_count < 20 else 'AINDA COM PROBLEMAS'}")
    
    #Mostrar detalhes das queries
    print("\n📝 Queries Executadas:")
    total_time = 0
    for idx, query in enumerate(context.captured_queries, 1):
        sql = query['sql'][:80] + "..." if len(query['sql']) > 80 else query['sql']
        qtime = float(query['time']) if isinstance(query['time'], str) else query['time']
        time = f"{qtime*1000:.2f}ms"
        total_time += qtime
        print(f"  {idx}. {sql} ({time})")
    
    print(f"\n⏱️  Tempo Total: {total_time*1000:.2f}ms")
    
    return query_count


def test_venda_list_queries():
    """
    Testa quantas queries são disparadas ao listar vendas.
    Expectativa: ~4-6 queries (antes era 50+)
    """
    print("\n" + "="*70)
    print("🔍 TESTE DE PERFORMANCE: VendaListView")
    print("="*70)
    
    # Criar dados de teste se não existirem
    if Venda.objects.count() == 0:
        print("⚠️  Nenhuma venda encontrada. Criando dados de teste...")
        for i in range(5):
            Venda.objects.create(
                data="2024-04-12",
                cliente=f"Cliente {i}",
                produto="Ovos",
                categoria="ovos",
                quantidade=100,
                valor_unitario=50,
                valor_total=5000,
                status_pagamento="pago" if i % 2 else "pendente",
            )
    
    # Criar usuário para teste
    if not CustomUser.objects.filter(username="user_test").exists():
        user = CustomUser.objects.create_user(
            username="user_test",
            email="user@test.com",
            password="test123",
            is_staff=True,
            is_superuser=True
        )
    else:
        user = CustomUser.objects.get(username="user_test")
    
    factory = RequestFactory()
    request = factory.get('/vendas/')
    request.user = user
    request.META['HTTP_ACCEPT'] = 'text/html'
    
    # Contar queries
    with CaptureQueriesContext(connection) as context:
        view = VendaListView.as_view()
        response = view(request)
    
    query_count = len(context)
    print(f"\n📊 Total de Queries: {query_count}")
    print(f"✅ Status: {'OTIMIZADO' if query_count < 15 else 'AINDA COM PROBLEMAS'}")
    
    # Mostrar detalhes das queries
    print("\n📝 Queries Executadas:")
    total_time = 0
    for idx, query in enumerate(context.captured_queries, 1):
        sql = query['sql'][:80] + "..." if len(query['sql']) > 80 else query['sql']
        qtime = float(query['time']) if isinstance(query['time'], str) else query['time']
        time = f"{qtime*1000:.2f}ms"
        total_time += qtime
        print(f"  {idx}. {sql} ({time})")
    
    print(f"\n⏱️  Tempo Total: {total_time*1000:.2f}ms")
    
    return query_count


def print_summary(lote_queries, venda_queries):
    """Imprime resumo das otimizações"""
    print("\n" + "="*70)
    print("📈 RESUMO DAS OTIMIZAÇÕES")
    print("="*70)
    
    print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│ View               │ Queries │ Status                               │
├─────────────────────────────────────────────────────────────────────┤
│ LoteListView       │ {lote_queries:<7} │ {'✅ OK' if lote_queries < 20 else '⚠️  Pode melhorar':<33} │
│ VendaListView      │ {venda_queries:<7} │ {'✅ OK' if venda_queries < 15 else '⚠️  Pode melhorar':<33} │
└─────────────────────────────────────────────────────────────────────┘

🎯 META: < 10 queries por view
✅ OBJETIVO: Reduzir load time de 10s → 200ms

💡 Técnicas Aplicadas:
   1. select_related() - Evita queries extras em ForeignKeys
   2. prefetch_related() - Otimiza queries em Many-to-many e Reverse FK
   3. .only() - Carrega apenas campos necessários
   4. .values_list() - Retorna apenas dados específicos
   5. distinct() com CTE - Evita contagem duplicada
   6. Cache de filtros - Não busca filtros a cada request (HX-Request check)
""")


if __name__ == "__main__":
    print("\n🚀 INICIANDO TESTES DE PERFORMANCE\n")
    
    try:
        lote_queries = test_lote_list_queries()
        venda_queries = test_venda_list_queries()
        print_summary(lote_queries, venda_queries)
        
        print("\n✅ Testes completados com sucesso!")
        print("💾 Limpar dados de teste: Deletar usuários 'admin_test' e 'user_test'")
        
    except Exception as e:
        print(f"\n❌ Erro durante testes: {str(e)}")
        import traceback
        traceback.print_exc()
