from pathlib import Path
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import csv
from plotly.graph_objs import *
import plotly.express as px
from datetime import datetime, timedelta
from datetime import date as dt
import base64
import plotly.graph_objects as go
from shiny import *
from pprint import pformat
import pyodide.http
import matplotlib.dates as mdates
import copy
import math
from shiny import ui, render, App, Inputs, Outputs, Session
from shinywidgets import output_widget, register_widget

# -*- coding: utf-8 -*-
app_ui = ui.page_fluid(
    {"class": "p-4"},
    ui.tags.style(
        """
        body {
            background-color: #f0f0f0;
        }
        .app-col {
            border: 1px solid #ccc;
            border-radius: 10px;
            background-color: #fff;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .app-header {
            text-align: center;
            background-color: #007bff;
            color: #fff;
            padding: 20px;
            border-radius: 5px 5px 0 0;
            font-size: 24px;
        }
        .app-description {
            font-size: 16px;
        }
        .app-controls {
            background-color: #f9f9f9;
            border-radius: 0 0 5px 5px;
            padding: 20px;
            margin: 20px 0;
        }
        .app-controls-label {
            font-weight: bold;
        }
        .app-action-button {
            background-color: #28a745;
            color: #fff;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            cursor: pointer;
        }
        .app-action-button:hover {
            background-color: #218838;
        }
        """
    ),
    ui.h2(
        {"class": "app-header"},
        "Otimizacao aplicada a Teoria Moderna do Portfolio",
    ),
    ui.row(
        ui.column(
            12,
            ui.div(
                {"class": "app-col app-description"},
                ui.p(
                    """
                    Nosso objetivo principal com este dashboard e tornar a teoria moderna do 
                    portfolio acessivel aos alunos dos primeiros anos de graduacao. Neste sentido, 
                    utilizando os resultados obtidos durante nossa pesquisa, elaboramos este dashboard 
                    que pode ser utilizado como meio para realizar backtest simples utilizando duas 
                    estrategias principais (Markowitz e Ingenua).
                    """
                ),
            ),
        )
    ),
    ui.row(
        ui.column(
            4,
            ui.navset_card_tab(
                ui.nav_panel(
                    "Controles",
                    ui.div(
                        {"class": "app-controls"},
                        ui.input_select(
                            "grafico",
                            "Selecione o grafico",
                            {
                                "linhas": "Grafico de Linhas",
                                "barras": "Grafico de Barras",
                            },
                        ),
                        ui.input_date_range(
                            "x",
                            "Periodo de investimento",
                            language="pt-BR",
                            format="dd-mm-yyyy",
                            min="2017-12-29",
                            max="2023-07-28",
                            start="2017-12-29",
                            end="2023-07-28",
                        ),
                        ui.input_numeric("y", "Investimento Inicial", value=1000),
                        ui.input_numeric("z", "Aporte Mensal", value=400),
                        ui.input_action_button(
                            "run",
                            "Executar Simulacao",
                            class_="btn btn-primary app-action-button",
                        ),
                    ),
                ),
                ui.nav_panel(
                    "Markowitz",
                    ui.p(
                        """
                        Nesta estrategia, os aportes seriam feitos em um unico ativo de
                        modo que ao final do aporte a proporcao de cada ativo na carteira seja a mais proxima
                        possivel do vetor de alocacao de capital. O vetor de alocacao de capital e obtido
                        com o objetivo de encontrar o portfolio com menor volatilidade.
                        """
                    ),
                ),
                ui.nav_panel(
                    "Ingenua",
                    ui.p(
                        """
                        A estrategia ingenua realiza a simulacao de um investidor iniciante que 
                        busca sempre manter a sua carteira de ativos balanceada em 50/50, ou seja,
                        realiza os aportes mensais tentando balancear o dinheiro nos ativos (BOVA11 e IVVB11),
                        sempre realizando aporte no ativo com menor valor no primeiro dia do mes.
                        """
                    ),
                ),
            ),
        ),
        ui.column(
            8,
            ui.navset_card_tab(
                ui.nav_panel(
                    "Graficos",
                    ui.row(
                        ui.column(12, output_widget("plot"),),
                        ui.column(12, ui.output_plot("plot2")),
                        ui.column(12, ui.output_table("plot3")),
                    ),
                )
            ),
        ),
    ),
)

dados_valores = {}


def server(input, output, session):
    @reactive.Calc
    def url():
        return f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.4391/dados?formato=json"

    @reactive.Calc
    def urlDiariocdi():
        return f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json"

    @reactive.Calc
    def url2():
        return f"https://storage.googleapis.com/dadosic-teste4/DadosIc-teste4.json?cacheControl=no-cache"

    @reactive.Calc
    def url2ativos():
        return f"https://storage.googleapis.com/dadosic-teste4/Dados2ativos.json?cacheControl=no-cache"

    @reactive.Calc
    async def cdi_data():
        response = await pyodide.http.pyfetch(url())
        if response.status != 200:
            raise Exception(f"Error fetching {url()}: {response.status}")
        data = await response.json()
        return data

    @reactive.Calc
    async def cdiDia_data():
        response = await pyodide.http.pyfetch(urlDiariocdi())
        if response.status != 200:
            raise Exception(f"Error fetching {urlDiariocdi()}: {response.status}")
        data = await response.json()
        return data

    @reactive.Calc
    async def geral_data():
        response = await pyodide.http.pyfetch(url2())
        if response.status != 200:
            raise Exception(f"Error fetching {url2()}: {response.status}")
        data = await response.json()
        return data

    @reactive.Calc
    async def doisativos_data():
        response = await pyodide.http.pyfetch(url2ativos())
        if response.status != 200:
            raise Exception(f"Error fetching {url2ativos()}: {response.status}")
        data = await response.json()
        return data

    @output
    @render.plot
    @reactive.effect()
    async def plot():
        selected=["Markowitz","Ingenua","IVVB11","BOVA11","SMALL11","CDI","Estrategia2","Estrategia3"]
        # Atualiza os valores iniciais e finais.
        datacdiDiario = await cdiDia_data()
        data1 = await cdi_data()
        dataTeste = await geral_data()
        data2ativos = await doisativos_data()
        readerT2ativos = pd.DataFrame(data2ativos)
        readerT = pd.DataFrame(dataTeste)

        dadoscdi = pd.DataFrame(datacdiDiario)
        dadoscdi["data"] = pd.to_datetime(dadoscdi["data"], dayfirst=True)
        dadoscdi.set_index("data", inplace=True)

        cdidiario = dadoscdi

        df = pd.DataFrame(data1)
        df["data"] = pd.to_datetime(df["data"], dayfirst=True)
        df.set_index("data", inplace=True)
        cdi = df
        data = list(input.x())

        data_inicio = data[0] - timedelta(365)
        data_final = data[1]
        print(data_inicio)
        print(data_final)

        # ObtÃÂÃÂ©m os nomes das colunas ÃÂÃÂ­mpares
        nomes_dados = readerT.columns[1::2].tolist()
        # Armazena a quantidade de linhas da planilha.
        tamanhoDF = readerT.shape[0]
        num_colunas = readerT.shape[1]

        readerT = readerT.to_numpy()  # Transforma os dados em tipo numpy.
        # Essa variavel ÃÂ¯ÃÂ¿ÃÂ½ responsavel por dizer quando o programa ira iniciar.
        diaInicio = 1

        # Lista para armazenar as datas da planilha .
        readerTDATASacao1 = []
        for i in range(tamanhoDF):
            readerTDATASacao1.append("")
        readerTDATASacaoauxiliar1 = list(
            range(tamanhoDF)
        )  # contem tudo ate a hora, feito para remover a parte da hora
        # Lista para armazenar as datas da planilha .
        readerTDATASacao2 = list(range(tamanhoDF))
        readerTDATASacaoauxiliar2 = list(
            range(tamanhoDF)
        )  # contem tudo ate a hora, feito para remover a parte da hora
        # Lista para armazenar os valores da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o (NÃÂ¯ÃÂ¿ÃÂ½o necessariamente BOVA11).
        readerTBOVA = list(range(tamanhoDF))
        # Lista para armazenar os valores da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o (NÃÂ¯ÃÂ¿ÃÂ½o necessariamente IVVB11).
        readerTIVVB = list(range(tamanhoDF))
        stringaux = ""
        stringaux2 = ""
        lixo = ""
        ContadorErros = 0

        readerTDATAS = [["" for _ in range(num_colunas)] for _ in range(tamanhoDF)]
        readerTVALORES = np.zeros((tamanhoDF, num_colunas))
        # Para facilitar o acesso aos dados do reader, eles sÃÂ¯ÃÂ¿ÃÂ½o separados nas listas.
        for i in range(0, tamanhoDF):
            for j in range(0, num_colunas):
                # Passa a string de data contida na planilha.
                if j % 2 == 0:
                    readerTDATAS[i][j] = readerT[i][j]
                    stringaux = readerTDATAS[i][j]
                    readerTDATASacao1[i], lixo = stringaux.split(" ")
                    readerTDATAS[i][j] = readerTDATASacao1[i]
                else:
                    # readerBOVA recebe os valores da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                    readerTVALORES[i][j] = readerT[i][j]
                    # readerTBOVA[i] = readerT[i][1]
                    # readerIVVB recebe os valores da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                    # readerTIVVB[i] = readerT[i][3]
        # tamanhoListas = len(readerTDATASacao1)
        # if tamanhoListas > len(readerTDATASacao2):
        #    tamanhoListas = len(readerTDATASacao2)
        i = 1

        tamanhoDATA = 0
        tamanhoInicio = 0
        # Para facilitar o acesso aos dados do reader, eles sÃÂ¯ÃÂ¿ÃÂ½o separados nas listas.

        for i in range(0, tamanhoDF):
            if (
                data_inicio
                <= datetime.strptime(readerTDATASacao1[i], "%m/%d/%Y").date()
                and (data_final + timedelta(days=1))
                >= datetime.strptime(readerTDATASacao1[i], "%m/%d/%Y").date()
            ):
                if tamanhoDATA == 0:
                    tamanhoInicio = i
                tamanhoDATA = tamanhoDATA + 1

        readerDATAS = list(range(tamanhoDATA))

        # Para facilitar o acesso aos dados do reader, eles sÃÂ¯ÃÂ¿ÃÂ½o separados nas listas.
        for i in range(0, tamanhoDF):
            # Transforma a string em um tipo datetime.
            if i >= tamanhoInicio and i <= (tamanhoInicio + tamanhoDATA):
                readerTDATASacao1[i] = datetime.strptime(
                    readerTDATASacao1[i], "%m/%d/%Y"
                )
        for i in range(0, tamanhoDATA):
            readerDATAS[i] = readerTDATASacao1[i + tamanhoInicio]
        # Como os dados consultados tem todos os dados desde 1986,
        cdi = cdi[cdi.index >= readerDATAS[0]]
        # faz 'cdi' receber apenas o periodo desejado pelo usuario.
        cdi = cdi[cdi.index <= readerDATAS[i]]

        cdidiario = cdidiario[cdidiario.index >= readerDATAS[0]]
        cdidiario = cdidiario[cdidiario.index <= readerDATAS[i]]

        readerDATAScdi = list(range(cdidiario.shape[0]))

        for i in range(0, cdidiario.shape[0]):
            readerDATAScdi[i] = cdidiario.index[i]

        cdi = cdi.to_numpy()
        cdidiario = cdidiario.to_numpy()

        # Armazena a quantidade de linhas presentes no 'cdi'.
        tamanhoCDI = cdi.shape[0]

        lst = cdi.ravel().tolist()
        cdidiario = cdidiario.ravel().tolist()

        linhas = []
        cdi = lst

        # ---

        infile = Path(__file__).parent / "./DadosIC2.csv"
        with open(infile, "w") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(["Date", "IVVB11", "Date", "BOVA11", "Date", "SMAL11"])
            for i in range(1, tamanhoDATA + 1):
                for j in range(0, num_colunas):
                    if j % 2 == 0:
                        linhas.append(readerTDATAS[i + tamanhoInicio - 1][j])
                    else:
                        linhas.append(readerTVALORES[i + tamanhoInicio - 1][j])

                writer.writerow(linhas)
                linhas.clear()

        infile = Path(__file__).parent / "DadosIC2.csv"
        reader = pd.read_csv(infile)
        reader = reader.dropna()

        tamanhoDF = reader.shape[0]  # Armazena a quantidade de linhas da planilha.

        reader = reader.to_numpy()  # Transforma os dados em tipo numpy.

        # Essa variavel ÃÂ¯ÃÂ¿ÃÂ½ responsavel por dizer quando o programa ira iniciar.
        diaInicio = 1

        # Lista para armazenar as datas da planilha .
        readerDATASacao1 = list(range(tamanhoDF))
        # Lista para armazenar as datas da planilha .
        readerDATASacao2 = list(range(tamanhoDF))
        # Lista para armazenar os valores da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o (NÃÂ¯ÃÂ¿ÃÂ½o necessariamente BOVA11).
        readerBOVA = list(range(tamanhoDF))
        # Lista para armazenar os valores da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o (NÃÂ¯ÃÂ¿ÃÂ½o necessariamente IVVB11).
        readerIVVB = list(range(tamanhoDF))
        ContadorErros = 0

        # Para facilitar o acesso aos dados do reader, eles sÃÂ¯ÃÂ¿ÃÂ½o separados nas listas.
        for i in range(0, tamanhoDF):
            # Passa a string de data contida na planilha.
            readerDATASacao1[i] = reader[i][0]
            readerDATASacao2[i] = reader[i][2]
            # readerBOVA recebe os valores da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
            readerBOVA[i] = reader[i][1]
            # readerIVVB recebe os valores da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
            readerIVVB[i] = reader[i][3]

        readerDATAScdi = pd.to_datetime(readerDATAScdi)
        readerDATASacaoAux1 = pd.to_datetime(readerDATASacao1)

        # Obter as datas em comum e as datas que nÃÂÃÂ£o estÃÂÃÂ£o em comum
        datas_em_comum = set(readerDATAScdi).intersection(readerDATASacaoAux1)
        datas_nao_em_comum_lista1 = set(readerDATAScdi).difference(datas_em_comum)
        datas_nao_em_comum_lista2 = set(readerDATASacaoAux1).difference(datas_em_comum)

        # Obter as posiÃÂÃÂ§ÃÂÃÂµes originais das datas em comum em cada lista
        posicoes_em_comum_lista1 = [
            i for i, data in enumerate(readerDATAScdi) if data in datas_em_comum
        ]
        posicoes_em_comum_lista2 = [
            i for i, data in enumerate(readerDATASacaoAux1) if data in datas_em_comum
        ]

        # Obter as posiÃÂÃÂ§ÃÂÃÂµes originais das datas que nÃÂÃÂ£o estÃÂÃÂ£o em comum em cada lista
        posicoes_nao_em_comum_lista1 = [
            i
            for i, data in enumerate(readerDATAScdi)
            if data in datas_nao_em_comum_lista1
        ]
        posicoes_nao_em_comum_lista2 = [
            i
            for i, data in enumerate(readerDATASacaoAux1)
            if data in datas_nao_em_comum_lista2
        ]

        # print("PosiÃÂÃÂ§ÃÂÃÂµes originais das datas que nÃÂÃÂ£o estÃÂÃÂ£o em ambas as listas:")
        # print(posicoes_nao_em_comum_lista1)  # Lista de posiÃÂÃÂ§ÃÂÃÂµes das datas que nÃÂÃÂ£o estÃÂÃÂ£o em comum na lista1

        posicoes_nao_em_comum_lista1.sort(reverse=True)
        for indice in posicoes_nao_em_comum_lista1:
            cdidiario.pop(indice)

        i = 1

        tamanhoDF = tamanhoDF

        # Altera os tipos de dados dentro das listas

        readerBOVA = list(np.float_(readerBOVA))
        readerIVVB = list(np.float_(readerIVVB))

        # Remove o ultimo dado de cada lista, pois foram criados com o tamanho da planilha(linhas)
        # e o ultimo elemento nessa lista possui valores que nÃÂ¯ÃÂ¿ÃÂ½o sÃÂ¯ÃÂ¿ÃÂ½o da planilha

        readerBOVAdesvio = list(range(tamanhoDF))
        readerIVVBdesvio = list(range(tamanhoDF))

        # taxas de retorno
        for i in range(1, tamanhoDF - ContadorErros - 1):
            readerBOVAdesvio[i - 1] = readerBOVA[i] / readerBOVA[i - 1] - 1
            readerIVVBdesvio[i - 1] = readerIVVB[i] / readerIVVB[i - 1] - 1

        readerBOVAdesvio[tamanhoDF - 2] = 0
        readerIVVBdesvio[tamanhoDF - 2] = 0

        #################################################################################################
        # Estrategia 2 - corolÃÂÃÂ¡rio 3

        # Recebe o valor inicial investido.
        valorInvestidoX = input.y()
        # Recebe o aporte mensal.
        aporteMensal = input.z()
        # -------Variaveis para o corolario----------
        valorInvestidoEstrategia2 = list(range(tamanhoDF))
        valorInvestidoEstrategia3 = list(range(tamanhoDF))
        CotasEstrategia2 = list(range(tamanhoDF))
        ValorIvvb11 = list(range(tamanhoDF))
        ValorBova11 = list(range(tamanhoDF))
        ValorIvvb_3 = list(range(tamanhoDF))
        ValorBova_3 = list(range(tamanhoDF))
        ValorCDI_3 = list(range(tamanhoDF))
        ValorCDI_2 = list(range(tamanhoDF))

        # Zerar as listas
        for i in range(tamanhoDF):
            valorInvestidoEstrategia2[i] = 0
            valorInvestidoEstrategia3[i] = 0
            CotasEstrategia2[i] = 0
            ValorIvvb11[i] = 0
            ValorBova11[i] = 0
            ValorIvvb_3[i] = 0
            ValorBova_3[i] = 0
            ValorCDI_3[i] = 0
            ValorCDI_2[i] = 0
        QntdIvvb_3 = 0.0
        QntdBova_3 = 0.0
        QntdCdi_3 = 0.0
        QntdIvvb11 = 0.0
        QntdBova11 = 0.0
        diferenca = 0.0
        diferenca2 = 0.0
        diferenca3 = 0.0
        porcentagemBOVA = 0.0
        porcentagemIVVB = 0.0
        diferencaAcao1 = 0.0
        diferencaCDI = 0.0
        diferencaAcao2 = 0.0
        diferencaMaior = 0.0
        # -------------------------------------------------

        # Para criar um grafico ÃÂ¯ÃÂ¿ÃÂ½ necessario possuir uma lista que represente o X do grafico com o mesmo tamanho dos valores.
        Xmax = list(range(len(readerDATASacao1)))
        # Transforma as strings no tipo pandas dataframe
        df = pd.DataFrame({"Teste": (readerDATASacao1)}, index=Xmax)
        df["Teste"] = pd.to_datetime(df["Teste"], format="%m/%d/%Y")
        df = df["Teste"].dt.strftime("%m")  # Obter apenas os meses

        MatrizV = list(range(4))
        ComecoMes = 0.0
        PrimeiroComeco = 0
        FimMes = 0
        aux = 0
        auxAporte = 0
        readerCovarianciaBova = list(range(tamanhoDF))
        readerCovarianciaIvvb = list(range(tamanhoDF))
        readerRETORNOcdi = list(range(tamanhoDF))
        # Lista criada para definir o comeÃÂ¯ÃÂ¿ÃÂ½o e fim dos meses que representam um ano de dados do markowitz.
        ComecoEFim = list(range(26))
        for i in range(26):
            ComecoEFim[i] = 0
        j = p = r = w = z = 0
        comI = 0
        comF = 1
        ContadorMark = 1
        ContaAporte = 0
        CotasEstrategia2[0] = 1
        for i in range(diaInicio, tamanhoDF):
            # Verifica se mudou de mes.
            if (int(df[i]) - 1) > (int(df[i - 1]) - 1) or (
                int(df[i]) - 1 == 0 and int(df[i - 1]) == 12
            ):
                if (
                    j == 0
                ):  # No primeiro mÃÂ¯ÃÂ¿ÃÂ½s armazena apenas o 'i' em que ele comeÃÂ¯ÃÂ¿ÃÂ½ou.
                    ComecoMes = i
                    PrimeiroComeco = i
                    j = j + 1
                    for z in range(1, tamanhoDF):
                        readerCovarianciaBova[z] = 0
                        readerCovarianciaIvvb[z] = 0
                        readerRETORNOcdi[z] = 0
                else:
                    if (
                        j <= 12
                    ):  # Agora comeÃÂ¯ÃÂ¿ÃÂ½a armazenar os dados de 1 ano para os testes do markowitz.
                        j = j + 1
                        # Pega o dia anterior do mes atual, ou seja, o ultimo dia do mes anterior.
                        FimMes = i - 1
                        # Armazeno o comeÃÂ¯ÃÂ¿ÃÂ½o do mes anterior em uma variavel auxiliar.
                        aux = ComecoMes
                        ComecoMes = i  # Armazeno o dia que comeÃÂ¯ÃÂ¿ÃÂ½ou o proximo mes.

                        # Vai armazenando as datas de inicio e fim de cada mes.
                        ComecoEFim[comI] = aux
                        ComecoEFim[comF] = FimMes

                        # Acrescenta 2 para que no proximo mes seja armazenado sem sobrescrever as datas do mes anterior.
                        comI = comI + 2
                        comF = comF + 2

                        # Armazena os valores de cada mes.
                        # readerCovarianciaBOVA armazena as taxas de retorno da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o e a outra lista da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                        for k in range(aux, FimMes + 1):
                            readerCovarianciaBova[w] = readerBOVAdesvio[k - 1]
                            readerCovarianciaIvvb[w] = readerIVVBdesvio[k - 1]
                            readerRETORNOcdi[w] = cdidiario[k - 1]
                            w = w + 1

                        # Vai armazenar todos os retornos diarios em 1 ano
                        readerCovarianciaBova2 = list(
                            range(FimMes - PrimeiroComeco + 1)
                        )
                        readerCovarianciaIvvb2 = list(
                            range(FimMes - PrimeiroComeco + 1)
                        )
                        readerRETORNOcdi2 = list(range(FimMes - PrimeiroComeco + 1))

                        for h in range(0, (FimMes - PrimeiroComeco + 1)):
                            # Como o 'for' anterior comeÃÂ¯ÃÂ¿ÃÂ½a no primeiro dia de cada mes, eu faÃÂ¯ÃÂ¿ÃÂ½o outro 'for' para padronizar os dados
                            # comeÃÂ¯ÃÂ¿ÃÂ½ando por 0, e sendo armazenado os dados de um ano dentro de outra lista.
                            readerCovarianciaBova2[h] = readerCovarianciaBova[h]
                            readerCovarianciaIvvb2[h] = readerCovarianciaIvvb[h]
                            readerRETORNOcdi2[h] = readerRETORNOcdi[h]

                        readerCovarianciaBova2 = np.array(
                            readerCovarianciaBova2
                        )  # Transformo em array
                        readerCovarianciaIvvb2 = np.array(readerCovarianciaIvvb2)
                        readerRETORNOcdi2 = np.array(
                            readerRETORNOcdi2
                        )  # Transformo em array
                        # ComecoTotal representa quando as outras estrategias podem comeÃÂ¯ÃÂ¿ÃÂ½ar(para todas comeÃÂ¯ÃÂ¿ÃÂ½arem apos um ano)
                        ComecoTotal = i

                    if j >= 13:
                        # Apos 12 meses a estrategia comeÃÂ¯ÃÂ¿ÃÂ½a a funcionar.
                        if (
                            r == 0
                        ):  # O primeiro mes apos a coleta de dados ÃÂ¯ÃÂ¿ÃÂ½ aplicado a estrategia separadamente pois ÃÂ¯ÃÂ¿ÃÂ½ feito com o valor aportado incialmente.
                            # MatrizV a matriz de covariancia dos dados armazenados por um ano
                            print(PrimeiroComeco)
                            print(ComecoEFim[23])
                            # print(readerCovarianciaBova2)

                            MatrizV[0] = np.cov(
                                readerCovarianciaBova2,
                                y=readerCovarianciaBova2,
                                bias=True,
                            )[0][1]
                            MatrizV[1] = np.cov(
                                readerCovarianciaBova2,
                                y=readerCovarianciaIvvb2,
                                bias=True,
                            )[0][1]
                            MatrizV[2] = MatrizV[1]
                            MatrizV[3] = np.cov(
                                readerCovarianciaIvvb2,
                                y=readerCovarianciaIvvb2,
                                bias=True,
                            )[0][1]

                            # Armazeno os dados da MatrizV.
                            MatrizVinv = [
                                [MatrizV[0], MatrizV[1]],
                                [MatrizV[2], MatrizV[3]],
                            ]

                            M1 = np.mean(readerCovarianciaBova2)
                            M2 = np.mean(readerCovarianciaIvvb2)
                            M = [[float(M1)], [float(M2)]]

                            CDIaux = [float(elemento) for elemento in readerRETORNOcdi2]
                            CDIRet = np.mean(CDIaux)

                            e = [[1.0], [1.0]]  # vetor elementar
                            eTransposto = [[1.0, 1.0]]
                            # Apos ter armazenado faÃÂ¯ÃÂ¿ÃÂ½o a inversa.
                            MatrizVinv = np.linalg.inv(MatrizVinv)

                            Rf_e = [
                                [1.0 * float(CDIRet) / 100],
                                [1.0 * float(CDIRet) / 100],
                            ]
                            # print(Rf_e)
                            # Recebe o valor de V^(-1)*e tem que receber V^(-1)
                            M_Rfe = np.subtract(M, Rf_e)

                            V_M_Rfe = np.matmul(MatrizVinv, M_Rfe)

                            V_eT = np.matmul(eTransposto, MatrizVinv)

                            Div = np.matmul(V_eT, M_Rfe)

                            #######################################################################
                            # EstratÃÂÃÂ©gia 3
                            V_e = np.matmul(MatrizVinv, e)
                            c = np.matmul(eTransposto, V_e)  # Recebe o valor de c
                            M_Rfe_T = np.transpose(M_Rfe)
                            print(M_Rfe_T)
                            dividendo = np.matmul(M_Rfe_T, V_M_Rfe) ** (1 / 2)
                            sigma_estrela = dividendo / Div
                            sigma_min = 1 / (c ** (1 / 2))
                            x = sigma_min / sigma_estrela
                            porcentagemB3 = x * float(V_M_Rfe[0][0] / Div)
                            porcentagemI3 = x * float(V_M_Rfe[1][0] / Div)
                            xf = 1 - (sigma_min / sigma_estrela)
                            print(xf)
                            print(sigma_min)
                            print(sigma_estrela)
                            print(f"{x} {porcentagemB3} {porcentagemI3}")
                            QntdBova_3 = (valorInvestidoX * porcentagemB3) / readerBOVA[
                                i - 1
                            ]
                            QntdIvvb_3 = (valorInvestidoX * porcentagemI3) / readerIVVB[
                                i - 1
                            ]

                            ValorCDI_3[i] = (valorInvestidoX * xf) * (
                                1 + CDIaux[-1] / 100
                            )  # Calcula o valor do CDI
                            # Calcula o valor que possui atualmente na primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorBova_3[i] = QntdBova_3 * readerBOVA[i - 1]
                            # Calcula o valor que possui atualmente na segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorIvvb_3[i] = QntdIvvb_3 * readerIVVB[i - 1]

                            valorInvestidoEstrategia3[i] = (
                                ValorBova_3[i] + ValorIvvb_3[i] + ValorCDI_3[i]
                            )
                            #######################################################################

                            # Calcula a porcentagem que deve ser investida na primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            porcentagemBOVA = float(V_M_Rfe[0][0] / Div)
                            # Calcula a porcentagem que deve ser investida na segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            porcentagemIVVB = float(V_M_Rfe[1][0] / Div)
                            print("aaaaaaa")
                            # print(MatrizVinv)
                            print(porcentagemBOVA)
                            print(porcentagemIVVB)

                            # Calcula quantas aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½es foram compradas da priemira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            QntdBova11 = (
                                valorInvestidoX * porcentagemBOVA
                            ) / readerBOVA[i - 1]
                            # Calcula quantas aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½es foram compradas da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            QntdIvvb11 = (
                                valorInvestidoX * porcentagemIVVB
                            ) / readerIVVB[i - 1]

                            # Calcula o valor que possui atualmente na primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorBova11[i] = QntdBova11 * readerBOVA[i - 1]
                            # Calcula o valor que possui atualmente na segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i - 1]
                            # Recebe o valor atual investido nas duas aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½es.
                            valorInvestidoEstrategia2[i] = (
                                ValorBova11[i] + ValorIvvb11[i]
                            )

                            # Calcula a cota do primeiro mes da estrategia markowitz.
                            CotasEstrategia2[ContadorMark] = (
                                valorInvestidoEstrategia2[i] / valorInvestidoX
                            )

                            # Atualiza r para sair da condiÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o do primeiro mes.
                            r = 1
                            ComecoMes = i  # Armazena quando comeÃÂ¯ÃÂ¿ÃÂ½ou esse mes.

                            # print(f'{df[i]} QntdBOVA {QntdBova11} -ValorBOVA {ValorBova11[i]} - QntdIvvb {QntdIvvb11} - ValorIvvb{ValorIvvb11[i]} - ValorTotal{valorInvestidoEstrategia2[i]}')#print(f'{df[i]} = Ideal {round(porcentagemBOVA,2)}% BOVA e {round(porcentagemIVVB,2)}% IVVB != Atual {round(((valorInvestidoEstrategia2[i]-ValorBova11[i])*100)/valorInvestidoEstrategia2[i],2)}% IVVB e {round(((valorInvestidoEstrategia2[i]-ValorIvvb11[i])*100)/valorInvestidoEstrategia2[i],2)}% BOVA')
                            lp = 0
                        else:
                            r = r + 1

                            # Incrementa o contador para as cotas.
                            ContadorMark = ContadorMark + 1
                            FimMes = i - 1  # Armazena o final do mes anterior.
                            aux = ComecoMes  # Armazena o comeco do mes anterior.
                            ComecoMes = i  # Armazena o comeco do mes atual.
                            comIaux = 0
                            comFaux = 1
                            comI = 0
                            comF = 1
                            # Eliminar as datas de inicio e fim do primeiro mes sobrescrevendo e deixando espaÃÂ¯ÃÂ¿ÃÂ½o para os dias do proximo mes.
                            for l in range(12):
                                ComecoEFim[comIaux] = ComecoEFim[comI + 2]
                                ComecoEFim[comFaux] = ComecoEFim[comF + 2]
                                comIaux = comIaux + 2
                                comFaux = comFaux + 2
                                comI = comI + 2
                                comF = comF + 2

                            # Atribui no final da lista o novo valor do comeÃÂ¯ÃÂ¿ÃÂ½o do ultimo mes.
                            ComecoEFim[22] = aux
                            # Atribui no final da lista o novo valor do final do ultimo mes.
                            ComecoEFim[23] = FimMes

                            x = ComecoEFim[0]
                            y = ComecoEFim[1]

                            # print(x)
                            # print(FimMes)
                            # print()
                            # readerCovariancia pega os valores da taxa de retorno de cada aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o(Do mes atual).
                            for k in range(aux, FimMes + 1):
                                readerCovarianciaBova[w] = readerBOVAdesvio[k - 1]
                                readerCovarianciaIvvb[w] = readerIVVBdesvio[k - 1]
                                readerRETORNOcdi[w] = cdidiario[k - 1]
                                w = w + 1
                            # print(readerCovarianciaBova)

                            # Vai armazenar todos os retornos diarios em 1 ano
                            readerCovarianciaBova2 = list(range(FimMes + 1))
                            readerCovarianciaIvvb2 = list(range(FimMes + 1))
                            readerRETORNOcdi2 = list(range(FimMes + 1))
                            f = 0
                            # readerCovarianciaBova2 recebe os dados de 1 ano.
                            print()
                            for h, f in zip(
                                range(x - 1 - 19, FimMes + 1), range(0, FimMes + 1)
                            ):
                                readerCovarianciaBova2[f] = readerCovarianciaBova[h - 1]
                                readerCovarianciaIvvb2[f] = readerCovarianciaIvvb[h - 1]
                                readerRETORNOcdi2[f] = readerRETORNOcdi[h]

                            f = 0

                            # Vai armazenar todos os retornos diarios em 1 ano
                            readerCovarianciaBova3 = list(range(FimMes - x + 1))
                            readerCovarianciaIvvb3 = list(range(FimMes - x + 1))
                            readerRETORNOcdi3 = list(range(FimMes - x + 1))
                            # Padroniza os dados para comecar na posicao 0;
                            for h in range(0, (FimMes - x) + 1):
                                readerCovarianciaBova3[f] = readerCovarianciaBova2[h]
                                readerCovarianciaIvvb3[f] = readerCovarianciaIvvb2[h]
                                readerRETORNOcdi3[f] = readerRETORNOcdi2[h]
                                # if lp==0:
                                #    print(f"{readerCovarianciaBova3[f]} {readerCovarianciaBova2[0]}")
                                f = f + 1
                            lp = 1
                            # Transforma os dados de um ano em array.
                            readerCovarianciaBova3 = np.array(readerCovarianciaBova3)
                            readerCovarianciaIvvb3 = np.array(readerCovarianciaIvvb3)

                            if lp == 0:
                                lp = 1
                            # MatrizV a matriz de covariancia dos dados armazenados por um ano
                            MatrizV[0] = np.cov(
                                readerCovarianciaBova3,
                                y=readerCovarianciaBova3,
                                bias=True,
                            )[0][1]
                            MatrizV[1] = np.cov(
                                readerCovarianciaBova3,
                                y=readerCovarianciaIvvb3,
                                bias=True,
                            )[0][1]
                            MatrizV[2] = MatrizV[1]
                            MatrizV[3] = np.cov(
                                readerCovarianciaIvvb3,
                                y=readerCovarianciaIvvb3,
                                bias=True,
                            )[0][1]

                            # Armazeno os dados da MatrizV.
                            MatrizVinv = [
                                [MatrizV[0], MatrizV[1]],
                                [MatrizV[2], MatrizV[3]],
                            ]

                            M1 = np.mean(readerCovarianciaBova3)
                            M2 = np.mean(readerCovarianciaIvvb3)

                            CDIaux = [float(elemento) for elemento in readerRETORNOcdi3]
                            CDIRet = np.mean(CDIaux)

                            M = [[float(M1)], [float(M2)]]
                            # print("Matriz M")
                            # print(M)

                            e = [[1.0], [1.0]]  # vetor elementar
                            eTransposto = [[1.0, 1.0]]
                            # Apos ter armazenado faÃÂ¯ÃÂ¿ÃÂ½o a inversa.
                            MatrizVinv = np.linalg.inv(MatrizVinv)

                            Rf_e = [
                                [1.0 * float(CDIRet / 100)],
                                [1.0 * float(CDIRet / 100)],
                            ]
                            # print("RF_e")
                            # print(Rf_e)

                            # Recebe o valor de V^(-1)*e tem que receber V^(-1)
                            M_Rfe = np.subtract(M, Rf_e)
                            # print("M_RFe")
                            # print(M_Rfe)

                            V_M_Rfe = np.matmul(MatrizVinv, M_Rfe)

                            V_eT = np.matmul(eTransposto, MatrizVinv)

                            Div = np.matmul(V_eT, M_Rfe)

                            # (Variveis temporarias, irÃÂÃÂ£o ser alteradas assim que possivel para melhor entendimento)#
                            # BOVA representa a primeira acao e IVVB a segunda acao#
                            # Calcula a porcentagem que deve ser investida na primeira acao.
                            porcentagemBOVA = float(V_M_Rfe[0][0] / Div)
                            # Calcula a porcentagem que deve ser investida na segunda acao.
                            porcentagemIVVB = float(V_M_Rfe[1][0] / Div)
                            print("porcentagens")
                            # print(MatrizVinv)
                            print(porcentagemBOVA)
                            print(porcentagemIVVB)
                            print("----------------")
                            # SÃÂ¯ÃÂ¿ÃÂ½ serÃÂ¯ÃÂ¿ÃÂ½ feito rebalanceamento apos 12 meses.
                            # Antes disso serÃÂ¯ÃÂ¿ÃÂ½ feito o aporte mensal na aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o que estÃÂ¯ÃÂ¿ÃÂ½ mais distante do ideal indicado pela estrategia.
                            # Calcula a % da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o presente no total do markowitz.
                            diferencaAcao1 = (
                                ValorBova11[i - 1]
                            ) / valorInvestidoEstrategia2[i - 1]
                            # Calcula a % da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o presente no total do markowitz.
                            diferencaAcao2 = (
                                ValorIvvb11[i - 1] / valorInvestidoEstrategia2[i - 1]
                            )

                            # if (r % 12) == 0:
                            # print(f"Ideal {round(porcentagemBOVA,2)}% BOVA e {round(porcentagemIVVB,2)}% IVVB != Atual {round(diferencaAcao1,2)}% IVVB e {round(diferencaAcao2,2)}% BOVA")
                            # print(".")
                            # print(f"Ideal {round(porcentagemBOVA,2)}% BOVA e {round(porcentagemIVVB,2)}% IVVB != Atual {round(((valorInvestidoEstrategia2[i-1]-ValorBova11[i-1])*100)/valorInvestidoEstrategia2[i-1],2)}% IVVB e {round(((valorInvestidoEstrategia2[i-1]-ValorIvvb11[i-1])*100)/valorInvestidoEstrategia2[i-1],2)}% BOVA")
                            # QntdBova11  = (valorInvestidoEstrategia2[i-1]*porcentagemBOVA)/readerBOVA[i-1]
                            # QntdIvvb11 = (valorInvestidoEstrategia2[i-1]*porcentagemIVVB)/readerIVVB[i-1]
                            diferenca = diferencaAcao1 - porcentagemBOVA
                            diferenca2 = diferencaAcao2 - porcentagemIVVB

                            # print(f'{df[i]}  Bova atual {diferencaAcao1} Ivvb atual {diferencaAcao2} sugerido {porcentagemBOVA} {porcentagemIVVB}')
                            # print(f'{df[i]} QntdBOVA {QntdBova11} - QntdIvvb {QntdIvvb11} ValorBOVA {ValorBova11[i]} - ValorIvvb{ValorIvvb11[i]}')
                            # print()
                            # Verifica qual estÃÂ¯ÃÂ¿ÃÂ½ mais distante do ideal pela estrategia e aporta nele.
                            if aporteMensal == 0:  # arrumar segundo escrito no whatsapp
                                # print(df[i])
                                if porcentagemBOVA < 0:
                                    auxAporte = (
                                        valorInvestidoEstrategia2[i - 1]
                                        * porcentagemIVVB
                                    )
                                    QntdBova11 = (auxAporte * -1) / readerBOVA[i - 1]
                                    QntdIvvb11 = (
                                        valorInvestidoEstrategia2[i - 1] + auxAporte
                                    ) / readerIVVB[i - 1]

                                elif porcentagemIVVB < 0:
                                    auxAporte = (
                                        valorInvestidoEstrategia2[i - 1]
                                        * porcentagemBOVA
                                    )
                                    QntdIvvb11 = (auxAporte * -1) / readerIVVB[i - 1]
                                    QntdBova11 = (
                                        valorInvestidoEstrategia2[i - 1] + auxAporte
                                    ) / readerBOVA[i - 1]

                                else:
                                    QntdBova11 = (
                                        valorInvestidoEstrategia2[i - 1]
                                        * porcentagemBOVA
                                    ) / readerBOVA[i - 1]
                                    QntdIvvb11 = (
                                        valorInvestidoEstrategia2[i - 1]
                                        * porcentagemIVVB
                                    ) / readerIVVB[i - 1]

                            elif porcentagemBOVA < 0 or porcentagemIVVB < 0:
                                ValorCDI_2[i] = (ValorCDI_2[i - 1] + aporteMensal) * (
                                    1 + CDIaux[-1] / 100
                                )  # Calcula o valor do CDI
                                print("Valor cdi")
                                print(ValorCDI_2[i])
                            else:
                                aporteAux = (
                                    valorInvestidoEstrategia2[i - 1] + aporteMensal
                                )
                                ValorCDI_2[i] = 0
                                QntdBova11 = (aporteAux * porcentagemBOVA) / readerBOVA[
                                    i - 1
                                ]
                                QntdIvvb11 = (aporteAux * porcentagemIVVB) / readerIVVB[
                                    i - 1
                                ]

                            QntdBova11 = np.round(QntdBova11, 2)
                            QntdIvvb11 = np.round(QntdIvvb11, 2)
                            ValorBova11[i] = QntdBova11 * readerBOVA[i - 1]
                            ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i - 1]
                            valorInvestidoEstrategia2[i] = (
                                ValorBova11[i] + ValorIvvb11[i] + ValorCDI_2[i]
                            )
                            # print("aqui")
                            # print(valorInvestidoEstrategia2[i])
                            # print(f'{df[i]} QntdBOVA {QntdBova11} -ValorBOVA {ValorBova11[i]} - QntdIvvb {QntdIvvb11} - ValorIvvb{ValorIvvb11[i]}')
                            CotasEstrategia2[ContadorMark] = (
                                CotasEstrategia2[ContadorMark - 1]
                                * (valorInvestidoEstrategia2[i] - aporteMensal)
                                / valorInvestidoEstrategia2[i - 1]
                            )

                            #######################################################################
                            # Estrategia 3
                            V_e = np.matmul(MatrizVinv, e)
                            c = np.matmul(eTransposto, V_e)  # Recebe o valor de c
                            M_Rfe_T = np.transpose(M_Rfe)
                            print(M_Rfe_T)
                            dividendo = np.matmul(M_Rfe_T, V_M_Rfe) ** (1 / 2)
                            sigma_estrela = dividendo / Div
                            sigma_min = 1 / (c ** (1 / 2))
                            x = sigma_min / sigma_estrela
                            porcentagemB3 = x * float(V_M_Rfe[0][0] / Div)
                            porcentagemI3 = x * float(V_M_Rfe[1][0] / Div)
                            xf = 1 - (sigma_min / sigma_estrela)

                            diferencaAcao1 = (
                                ValorBova_3[i - 1]
                            ) / valorInvestidoEstrategia3[i - 1]
                            # Calcula a % da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o presente no total do markowitz.
                            diferencaAcao2 = (
                                ValorIvvb_3[i - 1] / valorInvestidoEstrategia3[i - 1]
                            )
                            diferencaCDI = (
                                ValorCDI_3[i - 1] / valorInvestidoEstrategia3[i - 1]
                            )
                            diferenca = diferencaAcao1 - porcentagemB3
                            diferenca2 = diferencaAcao2 - porcentagemI3
                            diferenca3 = diferencaCDI - xf

                            if aporteMensal == 0:  # arrumar segundo escrito no whatsapp
                                QntdBova_3 = (
                                    valorInvestidoEstrategia3[i - 1] * porcentagemB3
                                ) / readerBOVA[i - 1]
                                QntdIvvb_3 = (
                                    valorInvestidoEstrategia3[i - 1] * porcentagemI3
                                ) / readerIVVB[i - 1]
                                ValorCDI_3[i] = (
                                    valorInvestidoEstrategia3[i - 1] * xf
                                ) * (
                                    1 + CDIaux[-1] / 100
                                )  # Calcula o valor do CDI
                            elif xf > 1:
                                ValorCDI_3[i] = (ValorCDI_3[i - 1] + aporteMensal) * (
                                    1 + CDIaux[-1] / 100
                                )  # Calcula o valor do CDI
                            elif diferenca > diferenca2 and diferenca > diferenca3:
                                QntdBova_3 = QntdBova_3 + (
                                    aporteMensal / readerBOVA[i - 1]
                                )
                                ValorCDI_3[i] = ValorCDI_3[
                                    i - 1
                                ]  # Calcula o valor do CDI
                                print("Investindo em ivvb11")
                            elif diferenca2 > diferenca and diferenca2 > diferenca3:
                                QntdIvvb_3 = QntdIvvb_3 + (
                                    aporteMensal / readerIVVB[i - 1]
                                )
                                ValorCDI_3[i] = ValorCDI_3[
                                    i - 1
                                ]  # Calcula o valor do CDI
                                print("Investindo em bova11")
                            elif diferenca3 > diferenca and diferenca3 > diferenca2:
                                ValorCDI_3[i] = (ValorCDI_3[i - 1] + aporteMensal) * (
                                    1 + CDIaux[-1] / 100
                                )  # Calcula o valor do CDI
                                print("Investindo em cdi")

                            # Calcula o valor que possui atualmente na primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorBova_3[i] = QntdBova_3 * readerBOVA[i - 1]
                            # Calcula o valor que possui atualmente na segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorIvvb_3[i] = QntdIvvb_3 * readerIVVB[i - 1]
                            valorInvestidoEstrategia3[i] = (
                                ValorBova_3[i] + ValorIvvb_3[i] + ValorCDI_3[i]
                            )
                            print("-")
                            print(valorInvestidoEstrategia3[i])
                            #######################################################################

            elif j >= 13:  # Para fazer as cotas diarias.
                ContadorMark = ContadorMark + 1
                ValorBova11[i] = QntdBova11 * readerBOVA[i - 1]
                ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i - 1]
                ValorCDI_2[i] = ValorCDI_2[i - 1]
                # print(f"Valor Bova {ValorIvvb11[i]} {readerIVVB[i-1]} Valor Ivvb {ValorBova11[i]} {readerBOVA[i-1]}")
                valorInvestidoEstrategia2[i] = (
                    ValorBova11[i] + ValorIvvb11[i] + ValorCDI_2[i]
                )
                #############################################
                # Estrategia 3
                ValorBova_3[i] = QntdBova_3 * readerBOVA[i - 1]
                ValorIvvb_3[i] = QntdIvvb_3 * readerIVVB[i - 1]
                ValorCDI_3[i] = ValorCDI_3[i - 1]  # Calcula o valor do CDI
                valorInvestidoEstrategia3[i] = (
                    ValorBova_3[i] + ValorIvvb_3[i] + ValorCDI_3[i]
                )

                #############################################

                # print(valorInvestidoEstrategia2[i])
                # if r%12==0:
                # print(valorInvestidoEstrategia2[i])
                CotasEstrategia2[ContadorMark] = CotasEstrategia2[ContadorMark - 1] * (
                    valorInvestidoEstrategia2[i] / valorInvestidoEstrategia2[i - 1]
                )
        valorInvestidoEstrategia3 = [
            np.float64(arr) for arr in valorInvestidoEstrategia3
        ]

        ##############################################################################################

        # Teste  do metodo markowitz
        # Covariancia
        print("-----------------------------------------")
        # Recebe o valor inicial investido.
        valorInvestidoX = input.y()
        # Recebe o aporte mensal.
        aporteMensal = input.z()
        # -------Variaveis para o markowitz e cotas----------
        valorInvestidoMarko = list(range(tamanhoDF))
        CotasMark = list(range(tamanhoDF))
        CotasIngenua = list(range(tamanhoDF))
        ValorIvvb11 = list(range(tamanhoDF))
        ValorBova11 = list(range(tamanhoDF))
        QntdIvvb11 = 0.0
        QntdBova11 = 0.0
        diferenca = 0.0
        diferenca2 = 0.0
        porcentagemBOVA = 0.0
        porcentagemIVVB = 0.0
        diferencaAcao1 = 0.0
        diferencaAcao2 = 0.0
        diferencaMaior = 0.0
        # -------------------------------------------------

        # Para criar um grafico ÃÂ¯ÃÂ¿ÃÂ½ necessario possuir uma lista que represente o X do grafico com o mesmo tamanho dos valores.
        Xmax = list(range(len(readerDATASacao1)))
        # Transforma as strings no tipo pandas dataframe
        df = pd.DataFrame({"Teste": (readerDATASacao1)}, index=Xmax)
        df["Teste"] = pd.to_datetime(df["Teste"], format="%m/%d/%Y")
        df = df["Teste"].dt.strftime("%m")  # Obter apenas os meses

        MatrizV = list(range(4))
        ComecoMes = 0.0
        PrimeiroComeco = 0
        FimMes = 0
        aux = 0
        readerCovarianciaBova = list(range(tamanhoDF))
        readerCovarianciaIvvb = list(range(tamanhoDF))
        # Lista criada para definir o comeÃÂ¯ÃÂ¿ÃÂ½o e fim dos meses que representam um ano de dados do markowitz.
        ComecoEFim = list(range(26))
        for i in range(26):
            ComecoEFim[i] = 0
        j = p = r = w = z = 0
        comI = 0
        comF = 1
        ContadorMark = 1
        ContaAporte = 0
        CotasMark[0] = 1
        for i in range(diaInicio, tamanhoDF):
            # Verifica se mudou de mes.
            if (int(df[i]) - 1) > (int(df[i - 1]) - 1) or (
                int(df[i]) - 1 == 0 and int(df[i - 1]) == 12
            ):
                if (
                    j == 0
                ):  # No primeiro mÃÂ¯ÃÂ¿ÃÂ½s armazena apenas o 'i' em que ele comeÃÂ¯ÃÂ¿ÃÂ½ou.
                    ComecoMes = i
                    PrimeiroComeco = i
                    j = j + 1
                    for z in range(1, tamanhoDF):
                        readerCovarianciaBova[z] = 0
                        readerCovarianciaIvvb[z] = 0
                else:
                    if (
                        j <= 12
                    ):  # Agora comeÃÂ¯ÃÂ¿ÃÂ½a armazenar os dados de 1 ano para os testes do markowitz.
                        j = j + 1
                        # Pega o dia anterior do mes atual, ou seja, o ultimo dia do mes anterior.
                        FimMes = i - 1
                        # Armazeno o comeÃÂ¯ÃÂ¿ÃÂ½o do mes anterior em uma variavel auxiliar.
                        aux = ComecoMes
                        ComecoMes = i  # Armazeno o dia que comeÃÂ¯ÃÂ¿ÃÂ½ou o proximo mes.

                        # Vai armazenando as datas de inicio e fim de cada mes.
                        ComecoEFim[comI] = aux
                        ComecoEFim[comF] = FimMes

                        # Acrescenta 2 para que no proximo mes seja armazenado sem sobrescrever as datas do mes anterior.
                        comI = comI + 2
                        comF = comF + 2

                        # Armazena os valores de cada mes.
                        # readerCovarianciaBOVA armazena as taxas de retorno da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o e a outra lista da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                        for k in range(aux, FimMes + 1):
                            readerCovarianciaBova[w] = readerBOVAdesvio[k - 1]
                            readerCovarianciaIvvb[w] = readerIVVBdesvio[k - 1]
                            w = w + 1

                        # Vai armazenar todos os retornos diarios em 1 ano
                        readerCovarianciaBova2 = list(
                            range(FimMes - PrimeiroComeco + 1)
                        )
                        readerCovarianciaIvvb2 = list(
                            range(FimMes - PrimeiroComeco + 1)
                        )

                        for h in range(0, (FimMes - PrimeiroComeco + 1)):
                            # Como o 'for' anterior comeÃÂ¯ÃÂ¿ÃÂ½a no primeiro dia de cada mes, eu faÃÂ¯ÃÂ¿ÃÂ½o outro 'for' para padronizar os dados
                            # comeÃÂ¯ÃÂ¿ÃÂ½ando por 0, e sendo armazenado os dados de um ano dentro de outra lista.
                            readerCovarianciaBova2[h] = readerCovarianciaBova[h]
                            readerCovarianciaIvvb2[h] = readerCovarianciaIvvb[h]

                        readerCovarianciaBova2 = np.array(
                            readerCovarianciaBova2
                        )  # Transformo em array
                        readerCovarianciaIvvb2 = np.array(
                            readerCovarianciaIvvb2
                        )  # Transformo em array
                        # ComecoTotal representa quando as outras estrategias podem comeÃÂ¯ÃÂ¿ÃÂ½ar(para todas comeÃÂ¯ÃÂ¿ÃÂ½arem apos um ano)
                        ComecoTotal = i

                    if j >= 13:
                        # Apos 12 meses a estrategia comeÃÂ¯ÃÂ¿ÃÂ½a a funcionar.
                        if (
                            r == 0
                        ):  # O primeiro mes apos a coleta de dados ÃÂ¯ÃÂ¿ÃÂ½ aplicado a estrategia separadamente pois ÃÂ¯ÃÂ¿ÃÂ½ feito com o valor aportado incialmente.
                            # MatrizV a matriz de covariancia dos dados armazenados por um ano
                            MatrizV[0] = np.cov(
                                readerCovarianciaBova2,
                                y=readerCovarianciaBova2,
                                bias=True,
                            )[0][1]
                            MatrizV[1] = np.cov(
                                readerCovarianciaBova2,
                                y=readerCovarianciaIvvb2,
                                bias=True,
                            )[0][1]
                            MatrizV[2] = MatrizV[1]
                            MatrizV[3] = np.cov(
                                readerCovarianciaIvvb2,
                                y=readerCovarianciaIvvb2,
                                bias=True,
                            )[0][1]

                            # Armazeno os dados da MatrizV.
                            MatrizVinv = [
                                [MatrizV[0], MatrizV[1]],
                                [MatrizV[2], MatrizV[3]],
                            ]

                            e = [[1], [1]]  # vetor elementar
                            eTransposto = [[1, 1]]
                            # Apos ter armazenado faÃÂ¯ÃÂ¿ÃÂ½o a inversa.
                            MatrizVinv = np.linalg.inv(MatrizVinv)
                            # print(MatrizVinv)
                            # Recebe o valor de V^(-1)*e
                            V_e = np.matmul(MatrizVinv, e)
                            c = np.matmul(eTransposto, V_e)  # Recebe o valor de c

                            # Calcula a porcentagem que deve ser investida na primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            porcentagemBOVA = float(V_e[0][0] / c)
                            # Calcula a porcentagem que deve ser investida na segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            porcentagemIVVB = float(V_e[1][0] / c)

                            # Calcula quantas aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½es foram compradas da priemira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            QntdBova11 = (
                                valorInvestidoX * porcentagemBOVA
                            ) / readerBOVA[i - 1]
                            # Calcula quantas aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½es foram compradas da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            QntdIvvb11 = (
                                valorInvestidoX * porcentagemIVVB
                            ) / readerIVVB[i - 1]

                            # Calcula o valor que possui atualmente na primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorBova11[i] = QntdBova11 * readerBOVA[i - 1]
                            # Calcula o valor que possui atualmente na segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i - 1]
                            # Recebe o valor atual investido nas duas aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½es.
                            valorInvestidoMarko[i] = ValorBova11[i] + ValorIvvb11[i]

                            # Calcula a cota do primeiro mes da estrategia markowitz.
                            CotasMark[ContadorMark] = (
                                valorInvestidoMarko[i] / valorInvestidoX
                            )

                            # Atualiza r para sair da condiÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o do primeiro mes.
                            r = 1
                            ComecoMes = i  # Armazena quando comeÃÂ¯ÃÂ¿ÃÂ½ou esse mes.

                            # print(f'{df[i]} QntdBOVA {QntdBova11} -ValorBOVA {ValorBova11[i]} - QntdIvvb {QntdIvvb11} - ValorIvvb{ValorIvvb11[i]} - ValorTotal{valorInvestidoMarko[i]}')#print(f'{df[i]} = Ideal {round(porcentagemBOVA,2)}% BOVA e {round(porcentagemIVVB,2)}% IVVB != Atual {round(((valorInvestidoMarko[i]-ValorBova11[i])*100)/valorInvestidoMarko[i],2)}% IVVB e {round(((valorInvestidoMarko[i]-ValorIvvb11[i])*100)/valorInvestidoMarko[i],2)}% BOVA')
                        else:
                            r = r + 1

                            # Incrementa o contador para as cotas.
                            ContadorMark = ContadorMark + 1
                            FimMes = i - 1  # Armazena o final do mes anterior.
                            aux = ComecoMes  # Armazena o comeco do mes anterior.
                            ComecoMes = i  # Armazena o comeco do mes atual.
                            comIaux = 0
                            comFaux = 1
                            comI = 0
                            comF = 1
                            # Eliminar as datas de inicio e fim do primeiro mes sobrescrevendo e deixando espaÃÂ¯ÃÂ¿ÃÂ½o para os dias do proximo mes.
                            for l in range(12):
                                ComecoEFim[comIaux] = ComecoEFim[comI + 2]
                                ComecoEFim[comFaux] = ComecoEFim[comF + 2]
                                comIaux = comIaux + 2
                                comFaux = comFaux + 2
                                comI = comI + 2
                                comF = comF + 2

                            # Atribui no final da lista o novo valor do comeÃÂ¯ÃÂ¿ÃÂ½o do ultimo mes.
                            ComecoEFim[22] = aux
                            # Atribui no final da lista o novo valor do final do ultimo mes.
                            ComecoEFim[23] = FimMes

                            x = ComecoEFim[0]
                            y = ComecoEFim[1]

                            # readerCovariancia pega os valores da taxa de retorno de cada aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o(Do mes atual).
                            for k in range(aux, FimMes + 1):
                                readerCovarianciaBova[w] = readerBOVAdesvio[k - 1]
                                readerCovarianciaIvvb[w] = readerIVVBdesvio[k - 1]
                                w = w + 1

                            # Vai armazenar todos os retornos diarios em 1 ano
                            readerCovarianciaBova2 = list(range(FimMes + 1))
                            readerCovarianciaIvvb2 = list(range(FimMes + 1))
                            f = 0
                            # readerCovarianciaBova2 recebe os dados de 1 ano.
                            for h, f in zip(
                                range(x - 1 - 19, FimMes + 1), range(0, FimMes + 1)
                            ):
                                readerCovarianciaBova2[f] = readerCovarianciaBova[h - 1]
                                readerCovarianciaIvvb2[f] = readerCovarianciaIvvb[h - 1]

                            f = 0

                            # Vai armazenar todos os retornos diarios em 1 ano
                            readerCovarianciaBova3 = list(range(FimMes - x + 1))
                            readerCovarianciaIvvb3 = list(range(FimMes - x + 1))

                            # Padroniza os dados para comeÃÂ¯ÃÂ¿ÃÂ½ar na posiÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o 0;
                            for h in range(0, (FimMes - x) + 1):
                                readerCovarianciaBova3[f] = readerCovarianciaBova2[h]
                                readerCovarianciaIvvb3[f] = readerCovarianciaIvvb2[h]
                                f = f + 1

                            # Transforma os dados de um ano em array.
                            readerCovarianciaBova3 = np.array(readerCovarianciaBova3)
                            readerCovarianciaIvvb3 = np.array(readerCovarianciaIvvb3)

                            # MatrizV a matriz de covariancia dos dados armazenados por um ano
                            MatrizV[0] = np.cov(
                                readerCovarianciaBova3,
                                y=readerCovarianciaBova3,
                                bias=True,
                            )[0][1]
                            MatrizV[1] = np.cov(
                                readerCovarianciaBova3,
                                y=readerCovarianciaIvvb3,
                                bias=True,
                            )[0][1]
                            MatrizV[2] = MatrizV[1]
                            MatrizV[3] = np.cov(
                                readerCovarianciaIvvb3,
                                y=readerCovarianciaIvvb3,
                                bias=True,
                            )[0][1]

                            # Armazeno os dados da MatrizV.
                            MatrizVinv = [
                                [MatrizV[0], MatrizV[1]],
                                [MatrizV[2], MatrizV[3]],
                            ]
                            e = [[1], [1]]  # vetor elementar
                            eTransposto = [[1, 1]]
                            # Apos ter armazenado faÃÂ¯ÃÂ¿ÃÂ½o a inversa da matriz.
                            MatrizVinv = np.linalg.inv(MatrizVinv)

                            # Recebe o valor de V^(-1)*e
                            V_e = np.matmul(MatrizVinv, e)
                            c = np.matmul(eTransposto, V_e)  # Recebe o valor de c

                            # Calcula a porcentagem que deve ser investida na primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            porcentagemBOVA = float(V_e[0][0] / c)
                            # Calcula a porcentagem que deve ser investida na segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
                            porcentagemIVVB = float(V_e[1][0] / c)

                            # print("IVVB")
                            # print(porcentagemBOVA)
                            # print("BOVA")
                            # print(porcentagemIVVB)
                            # SÃÂ¯ÃÂ¿ÃÂ½ serÃÂ¯ÃÂ¿ÃÂ½ feito rebalanceamento apos 12 meses.
                            # Antes disso serÃÂ¯ÃÂ¿ÃÂ½ feito o aporte mensal na aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o que estÃÂ¯ÃÂ¿ÃÂ½ mais distante do ideal indicado pela estrategia.
                            # Calcula a % da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o presente no total do markowitz.
                            diferencaAcao1 = (ValorBova11[i - 1]) / valorInvestidoMarko[
                                i - 1
                            ]
                            # Calcula a % da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o presente no total do markowitz.
                            diferencaAcao2 = (
                                ValorIvvb11[i - 1] / valorInvestidoMarko[i - 1]
                            )

                            # if (r % 12) == 0:
                            # print(f"Ideal {round(porcentagemBOVA,2)}% BOVA e {round(porcentagemIVVB,2)}% IVVB != Atual {round(diferencaAcao1,2)}% IVVB e {round(diferencaAcao2,2)}% BOVA")
                            # print(".")
                            # print(f"Ideal {round(porcentagemBOVA,2)}% BOVA e {round(porcentagemIVVB,2)}% IVVB != Atual {round(((valorInvestidoMarko[i-1]-ValorBova11[i-1])*100)/valorInvestidoMarko[i-1],2)}% IVVB e {round(((valorInvestidoMarko[i-1]-ValorIvvb11[i-1])*100)/valorInvestidoMarko[i-1],2)}% BOVA")
                            # QntdBova11  = (valorInvestidoMarko[i-1]*porcentagemBOVA)/readerBOVA[i-1]
                            # QntdIvvb11 = (valorInvestidoMarko[i-1]*porcentagemIVVB)/readerIVVB[i-1]
                            diferenca = diferencaAcao1 - porcentagemBOVA
                            diferenca2 = diferencaAcao2 - porcentagemIVVB
                            # print(f'{df[i]}  Bova atual {diferencaAcao1} Ivvb atual {diferencaAcao2} sugerido {porcentagemBOVA} {porcentagemIVVB}')
                            # print(f'{df[i]} QntdBOVA {QntdBova11} - QntdIvvb {QntdIvvb11} ValorBOVA {ValorBova11[i]} - ValorIvvb{ValorIvvb11[i]}')
                            # print()
                            # Verifica qual estÃÂ¯ÃÂ¿ÃÂ½ mais distante do ideal pela estrategia e aporta nele.
                            if aporteMensal == 0:  # arrumar segundo escrito no whatsapp
                                # print("Marko 0")
                                # print(f"{porcentagemBOVA} {porcentagemIVVB}")
                                if porcentagemBOVA < 0:
                                    auxAporte = (
                                        valorInvestidoMarko[i - 1] * porcentagemIVVB
                                    )
                                    QntdBova11 = (auxAporte * -1) / readerBOVA[i - 1]
                                    QntdIvvb11 = (
                                        valorInvestidoMarko[i - 1] + auxAporte
                                    ) / readerIVVB[i - 1]

                                elif porcentagemIVVB < 0:
                                    auxAporte = (
                                        valorInvestidoMarko[i - 1] * porcentagemBOVA
                                    )
                                    QntdIvvb11 = (auxAporte * -1) / readerIVVB[i - 1]
                                    QntdBova11 = (
                                        valorInvestidoMarko[i - 1] + auxAporte
                                    ) / readerBOVA[i - 1]

                                else:
                                    QntdBova11 = (
                                        valorInvestidoMarko[i - 1] * porcentagemBOVA
                                    ) / readerBOVA[i - 1]
                                    QntdIvvb11 = (
                                        valorInvestidoMarko[i - 1] * porcentagemIVVB
                                    ) / readerIVVB[i - 1]

                            elif diferenca < diferenca2:
                                QntdBova11 = QntdBova11 + (
                                    aporteMensal / readerBOVA[i - 1]
                                )

                            else:
                                QntdIvvb11 = QntdIvvb11 + (
                                    aporteMensal / readerIVVB[i - 1]
                                )

                            QntdBova11 = np.round(QntdBova11, 2)
                            QntdIvvb11 = np.round(QntdIvvb11, 2)
                            ValorBova11[i] = QntdBova11 * readerBOVA[i - 1]
                            ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i - 1]
                            valorInvestidoMarko[i] = ValorBova11[i] + ValorIvvb11[i]
                            # print(f"{valorInvestidoMarko[i]} {porcentagemBOVA} {ValorBova11[i]} {porcentagemIVVB} {ValorIvvb11[i]}")
                            # print(f'{df[i]} QntdBOVA {QntdBova11} -ValorBOVA {ValorBova11[i]} - QntdIvvb {QntdIvvb11} - ValorIvvb{ValorIvvb11[i]}')
                            CotasMark[ContadorMark] = (
                                CotasMark[ContadorMark - 1]
                                * (valorInvestidoMarko[i] - aporteMensal)
                                / valorInvestidoMarko[i - 1]
                            )

            elif j >= 13:  # Para fazer as cotas diarias.
                ContadorMark = ContadorMark + 1
                ValorBova11[i] = QntdBova11 * readerBOVA[i]
                ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i]
                valorInvestidoMarko[i] = ValorBova11[i] + ValorIvvb11[i]
                # if r%12==0:
                # print(valorInvestidoMarko[i])
                CotasMark[ContadorMark] = CotasMark[ContadorMark - 1] * (
                    valorInvestidoMarko[i] / valorInvestidoMarko[i - 1]
                )

        "IngÃÂ¯ÃÂ¿ÃÂ½nua com aporte"
        ValorTotalAportado = valorInvestidoX
        valorInvestidoAporte = list(range(tamanhoDF))
        ValorIvvb11 = list(range(tamanhoDF))
        ValorBova11 = list(range(tamanhoDF))
        QntdIvvb11 = 0
        QntdBova11 = 0
        j = 0
        ContadorIngenua = 1
        CotasIngenua[0] = 1
        ContadorAnos = 0
        Separador = 0

        # A estrategia ingenua so comeÃÂ¯ÃÂ¿ÃÂ½a apos 12 meses(com a markowitz apos a coleta dos dados)
        for i in range(diaInicio + ComecoTotal - 1, tamanhoDF):
            # Verifica a troca entre os meses
            if (int(df[i]) - 1) > (int(df[i - 1]) - 1) or (
                int(df[i]) - 1 == 0 and int(df[i - 1]) == 12
            ):
                if j == 0:  # No primeiro mes faz a divisÃÂ¯ÃÂ¿ÃÂ½o do valor inicial.
                    QntdBova11 = (valorInvestidoX / 2) / readerBOVA[i - 1]
                    QntdIvvb11 = (valorInvestidoX / 2) / readerIVVB[i - 1]
                    ValorBova11[i] = QntdBova11 * readerBOVA[i]
                    ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i]
                    valorInvestidoAporte[i] = ValorBova11[i] + ValorIvvb11[i]

                    CotasIngenua[ContadorIngenua] = (
                        valorInvestidoAporte[i] / valorInvestidoX
                    )

                    j = 1
                    # print(f'{df[i]} QntdBOVA {QntdBova11} -ValorBOVA {ValorBova11[i]} - QntdIvvb {QntdIvvb11} - ValorIvvb{ValorIvvb11[i]}')
                else:
                    j = j + 1
                    ContadorIngenua = ContadorIngenua + 1
                    # print(f'{df[i]}  ValorTotal{valorInvestidoAporte[i-1]}')
                    # if (j % 12) == 0:  # SÃÂ¯ÃÂ¿ÃÂ½ serÃÂ¯ÃÂ¿ÃÂ½ feito rebalanceamento apÃÂ¯ÃÂ¿ÃÂ½s 12 meses.
                    # print(f"Ideal 50% BOVA e 50% IVVB != Atual {round(((valorInvestidoAporte[i-1]-ValorBova11[i-1])*100)/valorInvestidoAporte[i-1],2)}% IVVB e {round(((valorInvestidoAporte[i-1]-ValorIvvb11[i-1])*100)/valorInvestidoAporte[i-1],2)}% BOVA")
                    # if(ValorBova11[i-1]>ValorIvvb11[i-1]):
                    # diferenca = ((ValorBova11[i-1]-ValorIvvb11[i-1])*100)/ValorBova11[i-1]
                    # if(diferenca>10.0):#Outra condiÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o para o rebalanceamento ÃÂ¯ÃÂ¿ÃÂ½ ter uma diferenÃÂ¯ÃÂ¿ÃÂ½a maior que 10% entre as aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½es.
                    # print(f'Rebalanceou 1 {ValorIvvb11[i-1]} {ValorBova11[i-1]}')
                    # QntdBova11  = (valorInvestidoAporte[i-1]/2)/readerBOVA[i-1]
                    # QntdIvvb11 = (valorInvestidoAporte[i-1]/2)/readerIVVB[i-1]
                    # print(".")
                    # else:
                    # diferenca = ((ValorIvvb11[i-1]-ValorBova11[i-1])*100)/ValorIvvb11[i-1]
                    # if(diferenca>10.0):
                    # print(f'Rebalanceou 2{ValorIvvb11[i-1]} {ValorBova11[i-1]}')
                    # QntdBova11  = (valorInvestidoAporte[i-1]/2)/readerBOVA[i-1]
                    # QntdIvvb11 = (valorInvestidoAporte[i-1]/2)/readerIVVB[i-1]

                    # Faz o aporte na aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o que possui menos atualmente.
                    if aporteMensal == 0:  # arrumar segundo escrito no whatsapp
                        if porcentagemBOVA < 0:
                            auxAporte = valorInvestidoAporte[i - 1] * 0.5
                            QntdBova11 = (auxAporte * -1) / readerBOVA[i - 1]
                            QntdIvvb11 = (
                                valorInvestidoAporte[i - 1] + auxAporte
                            ) / readerIVVB[i - 1]

                        elif porcentagemIVVB < 0:
                            auxAporte = valorInvestidoAporte[i - 1] * 0.5
                            QntdIvvb11 = (auxAporte * -1) / readerIVVB[i - 1]
                            QntdBova11 = (
                                valorInvestidoAporte[i - 1] + auxAporte
                            ) / readerBOVA[i - 1]

                        else:
                            QntdBova11 = (
                                valorInvestidoAporte[i - 1] * 0.5
                            ) / readerBOVA[i - 1]
                            QntdIvvb11 = (
                                valorInvestidoAporte[i - 1] * 0.5
                            ) / readerIVVB[i - 1]
                    elif ValorBova11[i - 1] < ValorIvvb11[i - 1]:
                        QntdBova11 = QntdBova11 + (aporteMensal / readerBOVA[i - 1])

                        ValorTotalAportado = ValorTotalAportado + aporteMensal
                    else:
                        QntdIvvb11 = QntdIvvb11 + (aporteMensal / readerIVVB[i - 1])
                        ValorTotalAportado = ValorTotalAportado + aporteMensal

                    ValorBova11[i] = QntdBova11 * readerBOVA[i]
                    ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i]
                    valorInvestidoAporte[i] = ValorBova11[i] + ValorIvvb11[i]
                    CotasIngenua[ContadorIngenua] = (
                        (CotasIngenua[ContadorIngenua - 1])
                        * (valorInvestidoAporte[i] - aporteMensal)
                        / valorInvestidoAporte[i - 1]
                    )
                    # print(f'{df[i]} QntdBOVA {QntdBova11} - QntdIvvb {QntdIvvb11} ValorBOVA {ValorBova11[i]} - ValorIvvb {ValorIvvb11[i]}')

            else:  # Armazena os dados das cotas diariamente.
                ContadorIngenua = ContadorIngenua + 1
                ValorBova11[i] = QntdBova11 * readerBOVA[i]
                ValorIvvb11[i] = QntdIvvb11 * readerIVVB[i]
                valorInvestidoAporte[i] = ValorBova11[i] + ValorIvvb11[i]
                # if j%12==0:
                # print(valorInvestidoAporte[i])
                CotasIngenua[ContadorIngenua] = (CotasIngenua[ContadorIngenua - 1]) * (
                    valorInvestidoAporte[i] / valorInvestidoAporte[i - 1]
                )

        # print(
        #   f'Valor obtido ao final do processo Markowitz: {round(valorInvestidoMarko[-1],2)}')
        # print(
        #    f'Valor obtido ao final do processo ingenuo com aporte: {round(valorInvestidoAporte[-1],2)}')
        RendimentoIngenua = CotasIngenua[ContadorMark] / CotasIngenua[1]
        # print(f'Rendimento cotas ingenua {RendimentoIngenua}')
        # print(f'final {CotasIngenua[ContadorMark]} inicial {CotasIngenua[1]}')

        "------------------------------"
        valorInvestido2 = list(range(tamanhoDF))
        valorInvestido22 = list(range(tamanhoDF))
        ValorIvvb112 = list(range(tamanhoDF))
        ValorBova112 = list(range(tamanhoDF))
        CotaAcao1 = list(range(tamanhoDF))
        CotaAcao2 = list(range(tamanhoDF))

        QntdIvvb112 = 0
        QntdBova112 = 0
        Contador = 1
        j2 = 0
        CotaAcao1[1] = 1
        CotaAcao2[1] = 1
        """for i in range(diaInicio + ComecoTotal - 1, tamanhoDF):  # SÃÂ¯ÃÂ¿ÃÂ½ comeÃÂ¯ÃÂ¿ÃÂ½a apos 12 meses
            # Verifica a troca dos meses
            if ((int(df[i]) - 1) > (int(df[i - 1]) - 1) or (int(df[i]) - 1 == 0 and int(df[i - 1]) == 12)):
                if j2 == 0:  # No primeiro mes cada aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o recebe o valor total investido.
                    QntdBova112 = valorInvestidoX / readerBOVA[i - 1]
                    QntdIvvb112 = valorInvestidoX / readerIVVB[i - 1]
                    j2 = 1
    
                else:
                    QntdBova112 = QntdBova112 + (aporteMensal / readerBOVA[i - 1])
                    QntdIvvb112 = QntdIvvb112 + (aporteMensal / readerIVVB[i - 1])
                    j2 = j2 + 1
    
            Contador = Contador + 1
    
            # Cotas da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
            CotaAcao1[Contador] = readerBOVA[i] / readerBOVA[diaInicio + ComecoTotal - 1]
            # Cotas da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
            CotaAcao2[Contador] = readerIVVB[i] / readerIVVB[diaInicio + ComecoTotal - 1]
            """

        # Transpor a matriz

        readerTVALORESDadosATT = reader[:, 1::2]

        transposed_matrix = np.transpose(readerTVALORESDadosATT)

        # Filtrar as linhas ÃÂÃÂ­mpares (colunas ÃÂÃÂ­mpares originais)
        # filtered_rows = transposed_matrix[1::2]

        # Converter as linhas filtradas em uma lista de listas
        readers = transposed_matrix.tolist()

        # Valor atual da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
        ValorBova112[i] = QntdBova112 * readerBOVA[i]
        # Valor atual da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o;
        ValorIvvb112[i] = QntdIvvb112 * readerIVVB[i]
        valorInvestido2[i] = ValorBova112[i]  # Valor total da primeira aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
        valorInvestido22[i] = ValorIvvb112[i]  # Valor total da segunda aÃÂ¯ÃÂ¿ÃÂ½ÃÂ¯ÃÂ¿ÃÂ½o.
        QntdAcoes = {tuple(reader): [] for reader in readers}
        CotaAcao = {tuple(reader): {} for reader in readers}
        ValorAcao = {tuple(reader): {} for reader in readers}

        valorInvestido2 = {}
        j2 = 0
        QntdAcao = 0.0
        for i in range(diaInicio + ComecoTotal - 1, tamanhoDF):
            if (int(df[i]) - 1) > (int(df[i - 1]) - 1) or (
                int(df[i]) - 1 == 0 and int(df[i - 1]) == 12
            ):
                if j2 == 0:
                    for reader in readers:
                        QntdAcao = valorInvestidoX / reader[i - 1]
                        QntdAcoes[tuple(reader)].append(QntdAcao)
                        j2 = 1
                else:
                    for reader in readers:
                        QntdAcao = QntdAcoes[tuple(reader)][-1] + (
                            aporteMensal / tuple(reader)[i - 1]
                        )
                        QntdAcoes[tuple(reader)].append(QntdAcao)
                    j2 = j2 + 1

            Contador = Contador + 1

            for reader in readers:
                CotaAcao[tuple(reader)][Contador] = (
                    reader[i] / reader[diaInicio + ComecoTotal - 1]
                )
                ValorAcao[tuple(reader)][i] = QntdAcoes[tuple(reader)][-1] * reader[i]
                # print(ValorAcao[tuple(reader)][i])
                valorInvestido2[i] = ValorAcao[tuple(reader)][i]
                # print(f"..{valorInvestido2[i]} {i}")

        # Assuming you have a dictionary 'CotaAcao1' with the required data
        RendimentoAcao1 = CotaAcao1[Contador] / CotaAcao1[1]

        # modo para pegar valores dentro do ipo dict
        # print("Valor final")
        """for reader in readers: 1232132131231231321321312312312312312312312312321312313213123213123213123213213
            for j in range(550,i+1):
                print(ValorAcao[tuple(reader)][j])
        """
        print("-")

        for reader in readers:
            for i in range(ComecoTotal, tamanhoDF):
                if i == tamanhoDF - 1:
                    print(ValorAcao[tuple(reader)][i])

        # print(f'Rendimento acao1 {RendimentoAcao1}')
        # print(f'final {CotaAcao1[Contador]} inicial {CotaAcao1[1]}')
        RendimentoAcao2 = CotaAcao2[Contador] / CotaAcao2[1]
        # print(f'cotas mark {RendimentoAcao2}')
        # print(f'final {CotaAcao2[Contador]} inicial {CotaAcao2[1]}')

        # ------------Rendimento CDI------------

        # Cria um X do tamanho dos dados do CDI para poder plotar o grafico
        XmaxCDI = list(range(tamanhoCDI))

        cdi = [float(i) for i in cdi]
        jcdi = 0
        # Lista criada para as cotas do CDI diarias.
        CotasCDI = list(range(tamanhoDF))
        CotasCDIM = list(range(tamanhoDF))  # Lista para as cotas do CDI mensais.
        CotasCDI[0] = 1
        CotasCDIM[0] = 1
        ContadorCDIM = 1
        ContadorCDI = 1
        valorInvestidoCDI = list(range(tamanhoDF))
        # Como os dados do CDI estÃÂ¯ÃÂ¿ÃÂ½o armazenados mensalmente, ele ira comeÃÂ¯ÃÂ¿ÃÂ½ar apos 12 meses juntamente com os outros.
        for i in range(12, tamanhoCDI):
            if jcdi == 0:
                valorInvestidoCDI[i] = valorInvestidoX * (
                    1 + cdi[i] / 100
                )  # Calcula o valor do CDI
                # Calcula o valor da cota do CDi.
                CotasCDIM[ContadorCDIM] = valorInvestidoCDI[i] / valorInvestidoX
                jcdi = 1

            else:
                # Calcula o valor do CDI agora realizando os aportes mensais.
                valorInvestidoCDI[i] = (valorInvestidoCDI[i - 1] + aporteMensal) * (
                    cdi[i] / 100 + 1
                )
                ContadorCDIM = ContadorCDIM + 1
                # Calculo das cotas com aporte.
                CotasCDIM[ContadorCDIM] = (
                    CotasCDIM[ContadorCDIM - 1]
                    * (valorInvestidoCDI[i] - aporteMensal)
                    / valorInvestidoCDI[i - 1]
                )
                jcdi = jcdi + 1

        # print(f'Valor obtido  ao final do processo CDI: {round(float(valorInvestidoCDI[i]),2)}')
        # print(ValorTotalAportado)
        ValorCDItabela = list(range(tamanhoDF))
        ValorX = ValorXCDI = 0
        j = 12
        ValorX = valorInvestidoCDI[12]
        ValorXCDI = CotasCDIM[1]
        ContadorCDIM = 1
        count = 0
        for i in range(diaInicio + ComecoTotal - 1, tamanhoDF):
            count = count + 1
            if j == 12:
                j = 13
                # Como os dados do CDI sÃÂ¯ÃÂ¿ÃÂ½o mensais, para transformar em diarios e plotar com os outros graficos eu padronizei um mes nos dias dele.
                # Repeti o mesmo processo para as cotas ficarem diarias.
                CotasCDI[ContadorCDI] = ValorXCDI
                ValorCDItabela[i] = ValorX

            # Verifica a troca dos meses
            elif (int(df[i]) - 1) > (int(df[i - 1]) - 1) or (
                int(df[i]) - 1 == 0 and int(df[i - 1]) == 12
            ):
                # Atualiza o valor que possui investido no CDI naquele mes
                ValorX = valorInvestidoCDI[j]
                ContadorCDIM = ContadorCDIM + 1
                # Atualiza o valor das cotas daquele mes
                ValorXCDI = CotasCDIM[ContadorCDIM]

                j = j + 1

            ContadorCDI = ContadorCDI + 1

            # Passa os valores do mes atual para os dias.
            ValorCDItabela[i] = ValorX

            # Passa a cota do mes atual para os dias.
            CotasCDI[ContadorCDI] = ValorXCDI

        # escritor(ValorCDItabela)

        RendimentoCDI = CotasCDI[ContadorCDI - 1] / CotasCDI[0]
        # print(f'cotas cdi {RendimentoCDI}')
        # print(f'final {CotasCDI[ContadorCDI-1]} inicial {CotasCDI[0]}')

        ###--------------------------------------###

        # print(f'Valor total investido: {ValorTotalAportado}') #Apenas para informar quanto foi aportado pelo usuario(Valor inicial + aportes mensais).

        # Grafico das cotas
        # Altero o tipo de todas as listas para tipo NumPy array para evitar warnings.
        count = 0
        # valorInvestido2 = np.asarray(valorInvestido2, dtype=object)
        # valorInvestido22 = np.asarray(valorInvestido22, dtype=object)
        # valorInvestidoAporte = np.asarray(valorInvestidoAporte, dtype=object)
        # valorInvestidoMarko = np.asarray(valorInvestidoMarko, dtype=object)
        # ValorCDItabela = np.asarray(ValorCDItabela, dtype=object)
        # CotasIngenua = np.asarray(CotasIngenua, dtype=object)
        # CotasMark = np.asarray(CotasMark, dtype=object)
        # CotasCDI = np.asarray(CotasCDI, dtype=object)

        t = list(range(tamanhoDF - ComecoTotal))
        i = 0
        verif = 0

        valorInvestidoMarko1 = list(range(tamanhoDF - ComecoTotal))
        valorInvestidoEstrategia_2 = list(range(tamanhoDF - ComecoTotal))
        valorInvestidoEstrategia_3 = list(range(tamanhoDF - ComecoTotal))
        valorInvestidoAporte1 = list(range(tamanhoDF - ComecoTotal))
        ValorCDItabela1 = list(range(tamanhoDF - ComecoTotal))
        valorInvestido21 = list(range(tamanhoDF - ComecoTotal))
        valorInvestido221 = list(range(tamanhoDF - ComecoTotal))
        CotasMark1 = list(range(tamanhoDF - ComecoTotal))
        CotasIngenua1 = list(range(tamanhoDF - ComecoTotal))
        CotaAcao11 = list(range(tamanhoDF - ComecoTotal))
        CotaAcao22 = list(range(tamanhoDF - ComecoTotal))
        CotasCDI1 = list(range(tamanhoDF - ComecoTotal))

        """for i in range(0, tamanhoDF):
            if i + ComecoTotal >= tamanhoDF:
                break
            teste2 = readerDATASacao1[i + ComecoTotal].split()
            auxdata = teste2[0].split("/")

            teste2[0] = auxdata[2] + "/" + auxdata[1] + "/" + auxdata[0]
            t[i] = teste2[0]
            valorInvestidoMarko1[i] = valorInvestidoMarko[i + ComecoTotal]
            valorInvestidoAporte1[i] = valorInvestidoAporte[i + ComecoTotal]
            ValorCDItabela1[i] = ValorCDItabela[i + ComecoTotal]
            valorInvestido21[i] = valorInvestido2[i + ComecoTotal]
            valorInvestido221[i] = valorInvestido22[i + ComecoTotal]
            CotasMark1[i] = CotasMark[i + 1]
            CotasIngenua1[i] = CotasIngenua[i + 1]
            CotaAcao11[i] = CotaAcao1[i + 1]
            CotaAcao22[i] = CotaAcao2[i + 1]
            CotasCDI1[i] = CotasCDI[i + 1]"""

        valorInvestido2Novo = [0] * len(valorInvestido2)
        for i, key in enumerate(valorInvestido2):
            valorInvestido2Novo[i] = valorInvestido2[key]
        aux = 0

        global dados_valores
        dados_cotas = {}
        nomes_dados_aux = copy.copy(nomes_dados)

        for chave, valor in ValorAcao.items():
            novo_chave = nomes_dados.pop(0)
            dados_valores[novo_chave] = valor
        for chave, valor in CotaAcao.items():
            novo_chave = nomes_dados_aux.pop(0)
            dados_cotas[novo_chave] = valor
        for i in range(0, tamanhoDF):
            if i + ComecoTotal >= tamanhoDF:
                break
            teste2 = readerDATASacao1[i + ComecoTotal].split()

            auxdata = teste2[0].split("/")

            teste2[0] = auxdata[2] + "/" + auxdata[1] + "/" + auxdata[0]
            t[i] = teste2[0]
            valorInvestidoMarko1[i] = valorInvestidoMarko[i + ComecoTotal]
            valorInvestidoEstrategia_2[i] = valorInvestidoEstrategia2[i + ComecoTotal]
            valorInvestidoEstrategia_3[i] = valorInvestidoEstrategia3[i + ComecoTotal]
            valorInvestidoAporte1[i] = valorInvestidoAporte[i + ComecoTotal]
            ValorCDItabela1[i] = ValorCDItabela[i + ComecoTotal]

            CotasMark1[i] = CotasMark[i + 1]
            CotasIngenua1[i] = CotasIngenua[i + 1]
            CotaAcao11[i] = CotaAcao1[i + 1]
            # CotaAcao22[i] = Cotacao2[i + 1]
            CotasCDI1[i] = CotasCDI[i + 1]

        # print(valorInvestido221)
        # Preenche o valorInvestido2Novo com os valores de valorInvestido21 e valorInvestido221
        """valorInvestido2Novo[i + ComecoTotal] = sum(
            valorInvestido21[i] + valorInvestido221[i]
        )"""

        # sort the data so it makes clean curves
        xdata1 = t
        # create some y data points
        chaves = []
        for y in range(ComecoTotal, len(valorInvestido21) + ComecoTotal):
            chaves.append(y)
        dicionario_estrategia2 = dict(zip(chaves, valorInvestidoEstrategia_2))
        dicionario_estrategia3 = dict(zip(chaves, valorInvestidoEstrategia_3))
        dicionario_marko = dict(zip(chaves, valorInvestidoMarko1))
        dicionario_ingenua = dict(zip(chaves, valorInvestidoAporte1))
        dicionario_cdi = dict(zip(chaves, ValorCDItabela1))
        dados_valores["Estrategia3"] = dicionario_estrategia3
        dados_valores["Estrategia2"] = dicionario_estrategia2
        dados_valores["Markowitz"] = dicionario_marko
        dados_valores["Ingenua"] = dicionario_ingenua
        dados_valores["CDI"] = dicionario_cdi

        dicionarioCotas_estrategia2 = dict(zip(chaves, CotasEstrategia2))
        dicionarioCotas_mark = dict(zip(chaves, CotasMark1))
        dicionarioCotas_ingenua = dict(zip(chaves, CotasIngenua1))
        dicionarioCotas_cdi = dict(zip(chaves, CotasCDI1))
        dados_cotas["Estrategia2"] = dicionarioCotas_estrategia2
        dados_cotas["Markowitz"] = dicionarioCotas_mark
        dados_cotas["Ingenua"] = dicionarioCotas_ingenua
        dados_cotas["CDI"] = dicionarioCotas_cdi

        ydata1 = valorInvestidoMarko1
        ydata2 = valorInvestidoAporte1
        ydata3 = valorInvestido21
        ydata4 = valorInvestido221
        ydata5 = ValorCDItabela1
        dadosCotas1 = CotasMark1
        dadosCotas2 = CotasIngenua1
        dadosCotas3 = CotaAcao11
        dadosCotas4 = CotaAcao22
        dadosCotas5 = CotasCDI1
        verif = 0
        rotulos_x = [data.split("/")[2] + "-" + data.split("/")[0] for data in t]
        print("-")

        print(ValorTotalAportado)
        if input.grafico() == "linhas":
            lineplot = go.FigureWidget()
            
            lineplot.data = []
            
            for dado, valores in dados_valores.items():
                if dado not in selected:
                    continue
            
                x = xdata1
                y = list(valores.values())
                lineplot.add_scatter(x=x, y=y, mode='lines', name=dado)
            
            # ConfiguraÃ§Ãµes do grÃ¡fico
            lineplot.update_layout(
                title="Graficos de Linhas",
                xaxis_title="Datas",
                yaxis_title="Patrimonio Final",
                legend_title="Dados",
                xaxis=dict(
                    tickmode='array',
                    tickvals=[xdata1[i] for i in [0, len(xdata1) // 4, len(xdata1) // 2, (len(xdata1) // 2 + len(xdata1) // 4), -1]],
                    ticktext=[rotulos_x[i] for i in [0, len(xdata1) // 4, len(xdata1) // 2, (len(xdata1) // 2 + len(xdata1) // 4), -1]]
                )
            )
            
            register_widget("plot", lineplot)
        elif input.grafico() == "barras":
            
            barchart = go.FigureWidget()
            barchart.data = []

            string_list = []
            values = []
            categories = []
            verif = 0
            
            if "Markowitz" in selected:
                string_list.append("Markowitz")
                values.append(
                    round(
                        dados_valores["Markowitz"][
                            len(valorInvestidoMarko1) + ComecoTotal - 1
                        ],
                        2,
                    )
                )
                categories.append("Markowitz")
                verif = 1
            if "Estrategia2" in selected:
                string_list.append("Estrategia2")
                values.append(
                    round(
                        dados_valores["Estrategia2"][
                            len(valorInvestidoEstrategia_2) + ComecoTotal - 1
                        ],
                        2,
                    )
                )
                categories.append("Estrategia2")
                verif = 1
            if "Estrategia3" in selected:
                string_list.append("Estrategia3")
                values.append(
                    round(
                        dados_valores["Estrategia3"][
                            len(valorInvestidoEstrategia_2) + ComecoTotal - 1
                        ],
                        2,
                    )
                )
                categories.append("Estrategia3")
                verif = 1
            if "Ingenua" in selected:
                string_list.append("Ingenua")
                values.append(
                    round(
                        dados_valores["Ingenua"][
                            len(valorInvestidoMarko1) + ComecoTotal - 1
                        ],
                        2,
                    )
                )
                categories.append("Ingenua")
                verif = 1
            if "BOVA11" in selected:
                string_list.append("BOVA11")
                values.append(
                    round(
                        dados_valores["BOVA11"][
                            len(valorInvestidoMarko1) + ComecoTotal - 1
                        ],
                        2,
                    )
                )
                categories.append("BOVA11")
                verif = 1
            if "IVVB11" in selected:
                string_list.append("IVVB11")
                values.append(
                    round(
                        dados_valores["IVVB11"][
                            len(valorInvestidoMarko1) + ComecoTotal - 1
                        ],
                        2,
                    )
                )
                categories.append("IVVB11")
                verif = 1
            if "SMAL11" in selected:
                string_list.append("SMAL11")
                values.append(
                    round(
                        dados_valores["SMAL11"][
                            len(valorInvestidoMarko1) + ComecoTotal - 1
                        ],
                        2,
                    )
                )
                categories.append("SMAL11")
                verif = 1
            if "CDI" in selected:
                string_list.append("CDI")
                values.append(round(ydata5[-1], 2))
                categories.append("CDI")
                verif = 1
            if verif == 1:
                for i, category in enumerate(categories):
                    if category in string_list:
                        barchart.add_bar(x=[category], y=[values[i]], name=category)
                        # Adicionando texto sobre as barras
                        barchart.add_annotation(x=category, y=values[i] + 5, text=str(values[i]), showarrow=False)
    
                # ConfiguraÃ§Ãµes do grÃ¡fico
                barchart.update_layout(
                    title="Graficos de Barras",
                    xaxis_title="Estrategias",
                    yaxis_title="Patrimonio Final",
                    showlegend=False
                )
    
            register_widget("plot", barchart)
        """elif input.grafico() == "cotas":
            # Grafico das cotas

            fig, ax = plt.subplots()
            for dado, valores in dados_cotas.items():
                if dado not in input.w():
                    continue  # Pular se a opÃÂÃÂ§ÃÂÃÂ£o nÃÂÃÂ£o estiver selecionada
                x = xdata1
                y = list(valores.values())
                ax.plot(x, y, label=dado)
                verif = 1
            # SeleÃÂÃÂ§ÃÂÃÂ£o dos valores a serem exibidos no eixo x
            if verif == 1:
                ax.set_xlabel("Datas")
                ax.set_ylabel("Cotas Final")
                ax.set_title("Graficos de Cotas")
                ax.legend()
                tamanho_x = len(xdata1)
                indices_mostrar = [
                    0,
                    tamanho_x // 4,
                    tamanho_x // 2,
                    (tamanho_x // 2 + tamanho_x // 4),
                    -1,
                ]
                x_mostrar = [xdata1[i] for i in indices_mostrar]
                x_mostrar2 = [rotulos_x[i] for i in indices_mostrar]
                ax.set_xticks(x_mostrar)
                ax.set_xticklabels(x_mostrar2, rotation=45)

            return fig
        else:
            fig, (ax2, ax1) = plt.subplots(2, 1, figsize=(10, 20))
            plt.subplots_adjust(hspace=10)
            for dado, valores in dados_valores.items():
                if dado not in input.w():
                    continue  # Pular se a opÃÂÃÂ§ÃÂÃÂ£o nÃÂÃÂ£o estiver selecionada
                x = xdata1
                y = list(valores.values())
                ax2.plot(x, y, label=dado)
                verif = 1
            for dado, valores in dados_cotas.items():
                if dado not in input.w():
                    continue  # Pular se a opÃÂÃÂ§ÃÂÃÂ£o nÃÂÃÂ£o estiver selecionada
                x = xdata1
                y = list(valores.values())
                ax1.plot(x, y, label=dado)
                verif = 1
            # SeleÃÂÃÂ§ÃÂÃÂ£o dos valores a serem exibidos no eixo x
            if verif == 1:
                ax1.set_xlabel("Datas")
                ax1.set_ylabel("Cotas Final")
                ax1.set_title("Graficos de Cotas")
                ax1.legend(loc=2)
                tamanho_x = len(xdata1)
                indices_mostrar = [
                    0,
                    tamanho_x // 4,
                    tamanho_x // 2,
                    (tamanho_x // 2 + tamanho_x // 4),
                    -1,
                ]
                x_mostrar = [xdata1[i] for i in indices_mostrar]
                x_mostrar2 = [rotulos_x[i] for i in indices_mostrar]
                ax1.set_xticks(x_mostrar)
                ax1.set_xticklabels(x_mostrar2, rotation=45)

                ax2.set_xlabel("Datas")
                ax2.set_ylabel("Patrimonio Final")
                ax2.set_title("Graficos de Linhas")
                ax2.legend(loc=2)
                ax2.set_xticks(x_mostrar)
                ax2.set_xticklabels(x_mostrar2, rotation=45)

                fig.tight_layout()
                fig.subplots_adjust(hspace=5)

            return fig
            """
    @output
    @render.plot
    @reactive.event(input.run, ignore_none=False)
    async def plot2():
        for nome_subdicionario in dados_valores.keys():
            # Extrair o valor final do CDI
            cdi_final = obter_ultimo_valor(dados_valores["CDI"])
            # Calcular a performance relativa ao CDI e armazenar em um novo dicionÃÂ¡rio
            performances = {
                nome: 100 * (obter_ultimo_valor(valor) / cdi_final - 1)
                for nome, valor in dados_valores.items()
                if nome != "CDI"
            }
            # Plotagem
            # Criar figura e eixo
            fig, ax = plt.subplots(figsize=(10, 6))

            # Adicionar barras ao eixo
            bars = ax.bar(performances.keys(), performances.values())

            # Adicionar rÃÂ³tulos e tÃÂ­tulo
            ax.set_ylabel("Performance Relativa ao CDI (%)")
            ax.set_title("Comparacao da Performance dos Ativos Relativa ao CDI")

            # Calcular altura mÃÂ¡xima para ajustar a posiÃÂ§ÃÂ£o do texto
            max_height = max([bar.get_height() for bar in bars])

            # Adicionar a porcentagem em cima de cada barra
            for bar in bars:
                height = bar.get_height()
                # Ajustar a posiÃÂ§ÃÂ£o do texto para barras muito altas
                if (
                    height / max_height > 0.95
                ):  # Se a barra for maior que 95% da altura mÃÂ¡xima
                    vertical_offset = -15  # Colocar o texto dentro da barra
                else:
                    vertical_offset = 3  # Colocar o texto acima da barra

                ax.annotate(
                    f"{height:.2f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, vertical_offset),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                )

            # Linha horizontal no y=0
            ax.axhline(0, color="gray", linewidth=0.8)

            # RotaÃÂ§ÃÂ£o dos rÃÂ³tulos no eixo x
            plt.xticks(rotation=45)

            # Retornar a figura
            return fig

    @output
    @render.table
    @reactive.event(input.run, ignore_none=False)
    async def plot3():
        # Extrair o ÃÂºltimo valor de cada subdicionÃÂ¡rio
        ultimos_valores = {ativo: valores[max(valores.keys())] for ativo, valores in dados_valores.items()}
        
        # Crie um DataFrame vazio para a tabela de comparaÃÂ§ÃÂ£o
        ativos = list(dados_valores.keys())
        comparacao_df = pd.DataFrame('-', columns=ativos, index=ativos)
        
        # Preencha a tabela de comparaÃÂ§ÃÂ£o com as diferenÃÂ§as percentuais no triÃÂ¢ngulo superior
        for i in range(len(ativos)):
            for j in range(i+1, len(ativos)):
                ativo1 = ativos[i]
                ativo2 = ativos[j]
                valor1 = ultimos_valores[ativo1]
                valor2 = ultimos_valores[ativo2]
                diferenca_percentual = ((valor1 - valor2) / valor2) * 100  # CÃÂ¡lculo da diferenÃÂ§a percentual
                comparacao_df.at[ativo1, ativo2] = round(diferenca_percentual, 2)  # Arredondar para 2 casas decimais
        # Adicione os nomes dos ativos como ÃÂ­ndice e como uma coluna ÃÂ  esquerda
        comparacao_df.index = ativos
        comparacao_df.insert(0, 'Ativos', ativos)

        return comparacao_df
    # FunÃÂ§ÃÂ£o para obter o ÃÂºltimo valor de um dicionÃÂ¡rio
    def obter_ultimo_valor(dic):
            return list(dic.values())[-1]
        
    print(f"teste {dados_valores}")


www_dir = Path(__file__).parent
app = App(app_ui, server, static_assets=www_dir)
