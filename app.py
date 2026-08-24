from pathlib import Path
import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pydeck as pdk
import seaborn as sns
import streamlit as st

PASTA_DADOS = Path(__file__).parent / "extraidos"
st.set_page_config(page_title="Dashboard COVID-19", layout="wide")


def carregar(nome):
    dados = pd.read_csv(PASTA_DADOS / nome, sep=";", encoding="utf-8-sig")
    for coluna in ["data", "data_inicio"]:
        if coluna in dados.columns:
            dados[coluna] = pd.to_datetime(dados[coluna], format="mixed", errors="coerce")
    colunas_numericas = [
        "ano",
        "semanaEpi",
        "casosNovos",
        "obitosNovos",
        "casosAcumulado",
        "obitosAcumulado",
        "populacao",
        "populacaoTCU2019",
        "latitude",
        "longitude",
    ]
    for coluna in colunas_numericas:
        if coluna in dados.columns:
            dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
    return dados


brasil = carregar("dados_semanais_brasil.csv")
estados = carregar("dados_semanais_estado.csv")
regioes = carregar("dados_semanais_regiao.csv")
recentes = carregar("dados_recentes_municipio.csv")
centroides = carregar("centroides_municipios.csv")

st.title("Dashboard COVID-19")
aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9 = st.tabs(
    ["Barras e linha", "Área", "Mapas", "Matplotlib", "Seaborn", "Altair", "Pizza", "Subplots", "PyDeck"]
)


#Respostas dos exercícios:
#1. Importância da Visualização de Dados: 
#"""
#A visualização de dados é importante em uma pandemia para
#transformar uma grande quantidade de informações, como casos, óbitos,
#em representações que podem ser compreendidas
#rapidamente. Os recursos visuais ajudam os gestores de saúde a 
#identificar novas ondas de contágio, tomar decisões sobre a distribuição
#de leitos, vacinas e outros recursos, além de facilitar a comunicação com
# a população.
#Para a população, visualizações claras e acessíveis também ajudam na
#compreensão da situação e podem contribuir para a adoção de medidas de
#prevenção.
#"""

#2. Gráfico de Barras com Streamlit
with aba1:
    st.header("Evolução semanal dos casos em São Paulo")
    estado = "SP"
    dados_sao_paulo = estados[estados["estado"] == estado]
    dados_sao_paulo = dados_sao_paulo.sort_values("data_inicio")
    dados_sao_paulo["semana"] = dados_sao_paulo.apply(
        lambda linha: f"{int(linha['ano'])} - Semana {int(linha['semanaEpi']):02d}",
        axis=1,
    )
    casos_por_semana = dados_sao_paulo.set_index("semana")["casosNovos"]
    st.bar_chart(casos_por_semana)
    st.write("Escolhi São Paulo por ser o estado mais populoso do Brasil. O eixo mostra o ano e o número da semana epidemiológica.")

#3. Gráfico de Linha com Streamlit
    st.header("Óbitos acumulados no Brasil")
    brasil_ordenado = brasil.sort_values("data_inicio").copy()
    brasil_ordenado["semana"] = brasil_ordenado.apply(
        lambda linha: f"{int(linha['ano'])} - Semana {int(linha['semanaEpi']):02d}",
        axis=1,
    )
    obitos_por_semana = brasil_ordenado.set_index("semana")["obitosAcumulado"]
    st.line_chart(obitos_por_semana)
    st.write("A curva de óbitos acumulados mostra como o total aumentou ao longo das semanas epidemiológicas. Trechos mais inclinados indicam períodos de maior entrada de óbitos.")

#4. Gráfico de Área com Streamlit
with aba2:
    st.header("Evolução anual dos casos acumulados")
    escolhidos = ["SP", "RJ", "MG"]
    estados_escolhidos = estados[
        estados["estado"].isin(escolhidos)
    ]
    casos_por_ano = estados_escolhidos.groupby(
        ["ano", "estado"], as_index=False
    )["casosAcumulado"].max()
    grafico_area = px.area(
        casos_por_ano,
        x="ano",
        y="casosAcumulado",
        color="estado",
        color_discrete_map={
            "MG": "#2E86DE",
            "RJ": "#F39C12",
            "SP": "#E74C3C",
        },
        labels={
            "ano": "Ano",
            "casosAcumulado": "Casos acumulados",
            "estado": "Estado",
        },
        title="Evolução anual dos casos acumulados",
    )
    st.plotly_chart(grafico_area, use_container_width=True)
    st.write("O gráfico mostra a evolução anual dos casos acumulados em São Paulo, Rio de Janeiro e Minas Gerais. Escolhi esses estados por serem populosos e representarem uma comparação relevante do Sudeste.")

#5. Mapa com Streamlit
with aba3:
    st.header("Mapa de casos acumulados por município")
    estado_mapa = "SP"
    municipios_estado = recentes[recentes["estado"] == estado_mapa]
    municipios_estado = municipios_estado.copy()
    municipios_estado["codmun"] = pd.to_numeric(municipios_estado["codmun"], errors="coerce").round().astype("Int64")
    centroides["codmun"] = pd.to_numeric(centroides["codmun"], errors="coerce").round().astype("Int64")
    mapa = municipios_estado.merge(centroides[["codmun", "latitude", "longitude"]], on="codmun", how="left")
    mapa = mapa.dropna(subset=["latitude", "longitude"])
    maior_numero_casos = mapa["casosAcumulado"].max()
    proporcao_casos = mapa["casosAcumulado"] / maior_numero_casos
    mapa["tamanho_ponto"] = 1000 + 3000 * (proporcao_casos ** 0.25)
    mapa = mapa.rename(columns={"latitude": "lat", "longitude": "lon"})
    st.map(mapa, latitude="lat", longitude="lon", size="tamanho_ponto")
    st.write("O mapa permite localizar concentrações e comparar municípios próximos dentro de São Paulo.")

#6. Visualização com Matplotlib
with aba4:
    st.header("Casos novos e óbitos novos por estado")
    semanas_com_dados = estados[
        (estados["casosNovos"] > 0) | (estados["obitosNovos"] > 0)
    ]
    semana = semanas_com_dados["data_inicio"].max()
    dados_ultima_semana = estados[estados["data_inicio"] == semana]
    numero_semana = dados_ultima_semana["semanaEpi"].iloc[0]
    comparacao = dados_ultima_semana.groupby("estado", as_index=False)[
        ["casosNovos", "obitosNovos"]
    ].sum()
    figura, eixo_casos = plt.subplots(figsize=(12, 5))
    posicoes = range(len(comparacao))
    largura = 0.4
    eixo_obitos = eixo_casos.twinx()

    eixo_casos.bar(
        [posicao - largura / 2 for posicao in posicoes],
        comparacao["casosNovos"],
        width=largura,
        color="steelblue",
        label="Casos novos",
    )
    eixo_obitos.plot(
        list(posicoes),
        comparacao["obitosNovos"],
        marker="o",
        linewidth=2,
        color="indianred",
        label="Óbitos novos",
    )
    eixo_casos.set_xticks(list(posicoes))
    eixo_casos.set_xticklabels(comparacao["estado"])
    eixo_casos.set_title(f"Semana epidemiológica {numero_semana} - {semana.date()}")
    eixo_casos.set_ylabel("Casos novos")
    eixo_obitos.set_ylabel("Óbitos novos")
    eixo_casos.tick_params(axis="x", rotation=45)
    eixo_casos.legend(loc="upper left")
    eixo_obitos.legend(loc="upper right")
    st.pyplot(figura)
    st.write("O gráfico combina barras de casos novos com uma linha de óbitos novos. Os dois eixos permitem visualizar as séries mesmo com escalas diferentes.")

#7. Boxplot com Seaborn
with aba5:
    st.header("Distribuição de casos novos por região")
    regioes_escolhidas = ["Norte", "Nordeste", "Sudeste"]
    caixa = regioes[regioes["regiao"].isin(regioes_escolhidas)]
    figura, eixo = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=caixa,
        x="regiao",
        y="casosNovos",
        order=regioes_escolhidas,
        palette=["#4C78A8", "#F58518", "#54A24B"],
        hue="regiao",
        legend=False,
        ax=eixo,
    )
    eixo.set_title("Casos novos semanais")
    eixo.set_xlabel("Região")
    eixo.set_ylabel("Casos novos")
    st.pyplot(figura)
    st.write("A linha dentro da caixa representa a mediana e a caixa mostra a maior parte das semanas. Os pontos mais distantes representam semanas com valores muito diferentes do padrão.")

#8. Gráfico de Área com Altair 
with aba6:
    st.header("Área em Altair por região - Sudeste")
    dados_altair = regioes[regioes["regiao"] == "Sudeste"].copy()
    dados_altair = dados_altair.sort_values(["ano", "semanaEpi"])
    dados_altair["semana"] = (
        dados_altair["ano"].astype(str)
        + " - Semana "
        + dados_altair["semanaEpi"].astype(str)
    )
    grafico = alt.Chart(dados_altair).mark_area().encode(
        x=alt.X("semana:N", title="Semana epidemiológica"),
        y=alt.Y("casosNovos:Q", title="Casos novos"),
        tooltip=["semana:N", "casosNovos:Q"],
    ).properties(height=350)
    st.altair_chart(grafico, use_container_width=True)
    st.write("Escolhi a região Sudeste por concentrar grande população e permitir observar claramente a evolução das notificações semanais.")

#9. Heatmap com Altair
    st.header("Heatmap de correlações")
    estado_heatmap = "SP"
    dados_heatmap = estados[estados["estado"] == estado_heatmap]
    colunas = ["casosNovos", "obitosNovos"]
    if "leitosOcupados" in dados_heatmap.columns:
        colunas.append("leitosOcupados")
    correlacao = dados_heatmap[colunas].corr().reset_index().melt("index")
    heatmap = alt.Chart(correlacao).mark_rect().encode(
        x=alt.X("index:N", title="Variável"),
        y=alt.Y("variable:N", title="Variável"),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(domain=[-1, 1], scheme="redblue"),
        ),
        tooltip=["index", "variable", "value"],
    ).properties(height=300)
    st.altair_chart(heatmap, use_container_width=True)
    st.write("O heatmap mostra a força da relação entre as variáveis em São Paulo. Valores próximos de 1 indicam relação positiva forte.")


#10. Gráfico de Pizza com Plotly
with aba7:
    st.header("Pizza: casos acumulados por região")
    ultimos_por_regiao = regioes.sort_values("data_inicio").groupby("regiao").tail(1)
    pizza = ultimos_por_regiao.groupby("regiao", as_index=False)["casosAcumulado"].sum()
    figura_pizza = px.pie(
        pizza,
        names="regiao",
        values="casosAcumulado",
        title="Distribuição percentual",
    )
    st.plotly_chart(figura_pizza, use_container_width=True)
    st.write("Regiões populosas tendem a concentrar mais casos absolutos; uma taxa por população seria melhor para comparar risco.")


#11. Subplots com Plotly
with aba8:
    st.header("Subplots: Sudeste e Nordeste")
    regioes_duas = ["Sudeste", "Nordeste"]
    figura = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=regioes_duas,
    )
    for numero, regiao_atual in enumerate(regioes_duas, start=1):
        parte = regioes[regioes["regiao"] == regiao_atual].sort_values("data_inicio")
        figura.add_trace(
            go.Bar(x=parte["data_inicio"], y=parte["casosNovos"], name="Casos"),
            row=1,
            col=numero,
        )
        figura.add_trace(
            go.Bar(x=parte["data_inicio"], y=parte["obitosNovos"], name="Óbitos"),
            row=1,
            col=numero,
        )
    figura.update_layout(barmode="group", title="Casos e óbitos por semana")
    st.plotly_chart(figura, use_container_width=True)
    st.write("Sudeste e Nordeste foram escolhidos para comparar duas regiões populosas, com diferentes padrões de notificações e picos de casos e óbitos ao longo das semanas.")

#12. Mapa Interativo com PyDeck
with aba9:
    st.header("PyDeck: Nordeste")
    st.write("Este mapa compara municípios do Nordeste usando casos acumulados ajustados pela população.")
    coordenadas = centroides.dropna(subset=["latitude", "longitude"])
    municipios_nordeste = recentes[recentes["regiao"] == "Nordeste"]
    pontos = municipios_nordeste.merge(
        coordenadas[["codmun", "latitude", "longitude"]],
        on="codmun",
    )
    pontos["casos_por_habitante"] = pontos["casosAcumulado"] / pontos["populacaoTCU2019"].replace(0, pd.NA)
    pontos["tamanho_ponto"] = 1000 + 4000 * pontos["casos_por_habitante"].fillna(0)
    camada = pdk.Layer(
        "ScatterplotLayer",
        data=pontos,
        get_position="[longitude, latitude]",
        get_radius="tamanho_ponto",
        get_fill_color="[200, 30, 0, 140]",
        pickable=True,
    )
    visao_inicial = pdk.ViewState(latitude=-9, longitude=-39, zoom=4)
    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            layers=[camada],
            initial_view_state=visao_inicial,
            tooltip={"text": "{municipio}\nCasos por habitante: {casos_por_habitante}"},
        )
    )