from django.urls import path
from .views import (
    RelatoriosHomeView,
    RelatorioLoteView,
    RelatorioAveView,
    RelatorioVacinaView,
    RelatorioFinanceiroView,
    RelatorioIncubacaoView,
    RelatorioEstoqueBaixoView,
    RelatorioReproducaoView,
    RelatorioConsumoCustoLoteView,
    RelatorioPrevisaoEstoqueView,
    RelatorioComparacaoLotesView,
    RelatorioLucroLoteView,
    RelatorioRankingLotesView,
    RelatorioRankingReprodutoresView,
    ExportRelatorioPDFView,
    ExportRelatorioExcelView,
)

app_name = "relatorios"

urlpatterns = [
    path("", RelatoriosHomeView.as_view(), name="index"),
    path("lotes/", RelatorioLoteView.as_view(), name="lotes"),
    path("aves/", RelatorioAveView.as_view(), name="aves"),
    path("vacinas/", RelatorioVacinaView.as_view(), name="vacinas"),
    path("financeiro/", RelatorioFinanceiroView.as_view(), name="financeiro"),
    path("incubacao/", RelatorioIncubacaoView.as_view(), name="incubacao"),
    path("estoque-baixo/", RelatorioEstoqueBaixoView.as_view(), name="estoque_baixo"),
    path("reproducao/", RelatorioReproducaoView.as_view(), name="reproducao"),
    path("consumo-custo-lote/", RelatorioConsumoCustoLoteView.as_view(), name="consumo_custo_lote"),
    path("previsao-estoque/", RelatorioPrevisaoEstoqueView.as_view(), name="previsao_estoque"),
    path("comparacao-lotes/", RelatorioComparacaoLotesView.as_view(), name="comparacao_lotes"),
    path("lucro-lote/", RelatorioLucroLoteView.as_view(), name="lucro_lote"),
    path("ranking-lotes/", RelatorioRankingLotesView.as_view(), name="ranking_lotes"),
    path("ranking-reprodutores/", RelatorioRankingReprodutoresView.as_view(), name="ranking_reprodutores"),
    path("export/pdf/", ExportRelatorioPDFView.as_view(), name="export_pdf"),
    path("export/excel/", ExportRelatorioExcelView.as_view(), name="export_excel"),
]
