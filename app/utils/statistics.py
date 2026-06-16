import pandas as pd
import numpy as np


def calculate_global_statistics(df_historico: pd.DataFrame) -> dict:
    """
    Calcula as estatísticas globais do bolão com base no histórico completo.
    Retorna um dicionário contendo rankings e recordes de cada categoria.
    """
    stats = {
        "dias_lideranca": [],
        "maior_subida": {"participante": "N/A", "arroba": "N/A", "valor": 0},
        "maior_queda": {"participante": "N/A", "arroba": "N/A", "valor": 0},
        "melhor_sequencia": {"participante": "N/A", "arroba": "N/A", "valor": 0},
        "melhor_pontuacao": {"participante": "N/A", "arroba": "N/A", "valor": 0},
        "mais_consistente": {"participante": "N/A", "arroba": "N/A", "desvio": 0.0},
        "mais_placares_exatos": {"participante": "N/A", "arroba": "N/A", "valor": 0},
        "mais_sem_pontos": {"participante": "N/A", "arroba": "N/A", "valor": 0}
    }
    
    if df_historico.empty:
        return stats
        
    df = df_historico.copy()
    # Garante ordenação cronológica por data_hora
    df = df.sort_values(by="data_hora")
    
    # 1. Dias na Liderança (contagem de coletas em 1º lugar)
    df_lideres = df[df["posicao"] == 1]
    if not df_lideres.empty:
        lideres_series = df_lideres.groupby(["participante", "arroba"])["coleta_id"].nunique()
        lideres_sorted = lideres_series.reset_index().sort_values(by="coleta_id", ascending=False)
        stats["dias_lideranca"] = lideres_sorted.to_dict(orient="records")
        
    # 2. Maior Pontuação Individual (absoluta)
    if not df.empty:
        idx_max_pontos = df["pontos"].idxmax()
        row_max_pontos = df.loc[idx_max_pontos]
        stats["melhor_pontuacao"] = {
            "participante": row_max_pontos["participante"],
            "arroba": row_max_pontos["arroba"],
            "valor": int(row_max_pontos["pontos"])
        }
        
    # Cálculos que necessitam de comparação temporal entre coletas consecutivas
    # Agrupa por participante/arroba para calcular deltas
    subidas_globais = []
    sequencias_globais = []
    consistencias = []
    
    # Lista de participantes únicos
    participantes = df.groupby(["participante", "arroba"])
    
    for (nome, arroba), df_part in participantes:
        # Ordena a trajetória do participante cronologicamente
        df_part_sorted = df_part.sort_values(by="data_hora").copy()
        
        # Diferença de posições (posição anterior - posição atual)
        # Ex: estava em 5º, foi para 2º -> 5 - 2 = +3 (subiu 3 posições)
        df_part_sorted["delta"] = df_part_sorted["posicao"].shift(1) - df_part_sorted["posicao"]
        
        # Guarda maior subida e queda individuais
        maior_subida_part = df_part_sorted["delta"].max()
        maior_queda_part = df_part_sorted["delta"].min()
        
        if not pd.isna(maior_subida_part) and maior_subida_part > 0:
            subidas_globais.append({
                "participante": nome,
                "arroba": arroba,
                "subida": int(maior_subida_part)
            })
            
        if not pd.isna(maior_queda_part) and maior_queda_part < 0:
            subidas_globais.append({
                "participante": nome,
                "arroba": arroba,
                "queda": int(abs(maior_queda_part))
            })
            
        # 3. Melhor sequência de acertos (aumento nos palpites corretos acumulados)
        cols_acerto = ["placar_exato", "gols_vencedor", "saldo_gols", "gols_perdedor", "vencedor_certo"]
        total_acertos = pd.Series(0, index=df_part_sorted.index)
        for col in cols_acerto:
            if col in df_part_sorted.columns:
                total_acertos += df_part_sorted[col].fillna(0)
        df_part_sorted["total_acertos"] = total_acertos
        df_part_sorted["delta_acertos"] = df_part_sorted["total_acertos"] - df_part_sorted["total_acertos"].shift(1)
        
        max_seq = 0
        current_seq = 0
        for da in df_part_sorted["delta_acertos"].tolist():
            if pd.isna(da):
                continue
            if da > 0:
                current_seq += 1
                max_seq = max(max_seq, current_seq)
            else:
                current_seq = 0
        sequencias_globais.append({
            "participante": nome,
            "arroba": arroba,
            "sequencia": max_seq
        })
        
        # 4. Consistência (desvio padrão das posições)
        # Requisito: ter participado de pelo menos 2 coletas para desvio ser válido
        if len(df_part_sorted) >= 2:
            std_dev = df_part_sorted["posicao"].std()
            if not pd.isna(std_dev):
                consistencias.append({
                    "participante": nome,
                    "arroba": arroba,
                    "desvio": float(std_dev)
                })
                
    # Determina os recordistas
    if subidas_globais:
        # Maior subida
        subidas_only = [x for x in subidas_globais if "subida" in x]
        if subidas_only:
            record_subida = max(subidas_only, key=lambda x: x["subida"])
            stats["maior_subida"] = {
                "participante": record_subida["participante"],
                "arroba": record_subida["arroba"],
                "valor": record_subida["subida"]
            }
            
        # Maior queda
        quedas_only = [x for x in subidas_globais if "queda" in x]
        if quedas_only:
            record_queda = max(quedas_only, key=lambda x: x["queda"])
            stats["maior_queda"] = {
                "participante": record_queda["participante"],
                "arroba": record_queda["arroba"],
                "valor": record_queda["queda"]
            }
            
    if sequencias_globais:
        record_seq = max(sequencias_globais, key=lambda x: x["sequencia"])
        stats["melhor_sequencia"] = {
            "participante": record_seq["participante"],
            "arroba": record_seq["arroba"],
            "valor": record_seq["sequencia"]
        }
        
    if consistencias:
        # O mais consistente é quem tem o menor desvio padrão
        record_consist = min(consistencias, key=lambda x: x["desvio"])
        stats["mais_consistente"] = {
            "participante": record_consist["participante"],
            "arroba": record_consist["arroba"],
            "desvio": round(record_consist["desvio"], 2)
        }
        
    # Recordistas de Acertos Detalhados no último snapshot
    if not df.empty:
        ultimo_coleta_id = df["coleta_id"].iloc[-1]
        df_ultimo = df[df["coleta_id"] == ultimo_coleta_id]
        
        if "placar_exato" in df_ultimo.columns and not df_ultimo.empty:
            idx_max_pe = df_ultimo["placar_exato"].idxmax()
            row_max_pe = df_ultimo.loc[idx_max_pe]
            stats["mais_placares_exatos"] = {
                "participante": row_max_pe["participante"],
                "arroba": row_max_pe["arroba"],
                "valor": int(row_max_pe["placar_exato"])
            }
            
        if "sem_pontos" in df_ultimo.columns and not df_ultimo.empty:
            idx_max_sp = df_ultimo["sem_pontos"].idxmax()
            row_max_sp = df_ultimo.loc[idx_max_sp]
            stats["mais_sem_pontos"] = {
                "participante": row_max_sp["participante"],
                "arroba": row_max_sp["arroba"],
                "valor": int(row_max_sp["sem_pontos"])
            }
        
    return stats


def calculate_individual_statistics(df_historico: pd.DataFrame, arroba_participante: str) -> dict:
    """
    Calcula as estatísticas de desempenho de um único participante.
    """
    ind_stats = {
        "posicao_atual": "N/A",
        "melhor_posicao": "N/A",
        "pior_posicao": "N/A",
        "media_posicao": 0.0,
        "evolucao_pontos": [],
        "evolucao_ranking": []
    }
    
    if df_historico.empty:
        return ind_stats
        
    df_part = df_historico[df_historico["arroba"] == arroba_participante].copy()
    if df_part.empty:
        return ind_stats
        
    df_part = df_part.sort_values(by="data_hora")
    
    # Posições
    posicoes = df_part["posicao"].tolist()
    ind_stats["posicao_atual"] = int(posicoes[-1])
    ind_stats["melhor_posicao"] = int(min(posicoes))
    ind_stats["pior_posicao"] = int(max(posicoes))
    ind_stats["media_posicao"] = round(float(np.mean(posicoes)), 1)
    
    # Trajetórias
    ind_stats["evolucao_pontos"] = df_part[["data_hora", "pontos"]].to_dict(orient="records")
    ind_stats["evolucao_ranking"] = df_part[["data_hora", "posicao"]].to_dict(orient="records")
    
    return ind_stats


def calculate_perolas(df_palpites: pd.DataFrame, df_historico: pd.DataFrame = None) -> dict:
    """
    Calcula as estatísticas divertidas "Pérolas do Bolão" a partir dos palpites individuais e histórico.

    Métricas:
    - ousado:     Top 3 participantes que mais apostaram palpites únicos (só ele apostou aquele placar naquele jogo).
    - maria:      Top 3 participantes que mais vezes coincidiram com o palpite majoritário do grupo.
    - retranqueiro: Top 3 participantes que apostaram menos gols no total (soma de todos os palpites).
    - zicado:     Top 3 participantes que mais vezes erraram por exatamente 1 gol no somatório do placar.
    - golfinho:   Top 3 participantes que mais alternaram posições na classificação geral ao longo do tempo.
    """
    resultado = {
        "ousado": [],
        "maria": [],
        "retranqueiro": [],
        "zicado": [],
        "golfinho": []
    }

    if df_palpites is None or df_palpites.empty:
        return resultado

    df = df_palpites.copy()

    # Usa o snapshot mais recente apenas (última coleta)
    ultimo_coleta_id = df["coleta_id"].iloc[-1]
    df = df[df["coleta_id"] == ultimo_coleta_id].copy()

    if df.empty:
        return resultado

    # ── 1. Ousado do Rolê ─────────────────────────────────────────────────
    df["palpite_str"] = df["palpite_m"].astype(str) + "x" + df["palpite_v"].astype(str)
    
    ousadia_counts = {}
    ousadia_placares = {}
    for (mandante, visitante), grupo in df.groupby(["mandante", "visitante"]):
        contagem_palpites = grupo.groupby("palpite_str")["arroba"].count()
        palpites_unicos = contagem_palpites[contagem_palpites == 1].index.tolist()
        for pal_str in palpites_unicos:
            linha = grupo[grupo["palpite_str"] == pal_str].iloc[0]
            arroba = linha["arroba"]
            nome = linha["participante"]
            if arroba not in ousadia_counts:
                ousadia_counts[arroba] = {"participante": nome, "arroba": arroba, "valor": 0}
                ousadia_placares[arroba] = []
            ousadia_counts[arroba]["valor"] += 1
            label = f"{mandante} {pal_str} {visitante}"
            ousadia_placares[arroba].append(label)
    
    if ousadia_counts:
        top_ousados = sorted(ousadia_counts.values(), key=lambda x: x["valor"], reverse=True)[:3]
        for o in top_ousados:
            o["placares"] = ousadia_placares.get(o["arroba"], [])
        resultado["ousado"] = top_ousados

    # ── 2. Maria vai com as outras ────────────────────────────────────────
    maria_counts = {}
    maria_placares = {}
    for (mandante, visitante), grupo in df.groupby(["mandante", "visitante"]):
        contagem_palpites = grupo.groupby("palpite_str")["arroba"].count()
        max_count = contagem_palpites.max()
        if max_count < 2:
            continue  # Não há maioria se todos apostaram diferente
        palpites_mais_comuns = contagem_palpites[contagem_palpites == max_count].index.tolist()
        palpite_majoritario = palpites_mais_comuns[0]
        
        marias = grupo[grupo["palpite_str"] == palpite_majoritario]
        for _, row in marias.iterrows():
            arroba = row["arroba"]
            nome = row["participante"]
            if arroba not in maria_counts:
                maria_counts[arroba] = {"participante": nome, "arroba": arroba, "valor": 0}
                maria_placares[arroba] = []
            maria_counts[arroba]["valor"] += 1
            label = f"{mandante} {palpite_majoritario} {visitante}"
            maria_placares[arroba].append(label)
    
    if maria_counts:
        top_marias = sorted(maria_counts.values(), key=lambda x: x["valor"], reverse=True)[:3]
        for m in top_marias:
            m["placares"] = maria_placares.get(m["arroba"], [])
        resultado["maria"] = top_marias

    # ── 3. Retranqueiro ──────────────────────────────────────────────────
    df["total_gols_palpite"] = df["palpite_m"].fillna(0) + df["palpite_v"].fillna(0)
    gols_totais = df.groupby(["participante", "arroba"])["total_gols_palpite"].sum().reset_index()
    if not gols_totais.empty:
        gols_totais_sorted = gols_totais.sort_values(by="total_gols_palpite").head(3)
        for _, row in gols_totais_sorted.iterrows():
            resultado["retranqueiro"].append({
                "participante": row["participante"],
                "arroba": row["arroba"],
                "valor": int(row["total_gols_palpite"])
            })

    # ── 4. Zicado ────────────────────────────────────────────────────────
    df_com_real = df[(df["placar_real_m"] >= 0) & (df["placar_real_v"] >= 0)].copy()
    if not df_com_real.empty:
        df_com_real["soma_real"] = df_com_real["placar_real_m"] + df_com_real["placar_real_v"]
        df_com_real["soma_palpite"] = df_com_real["palpite_m"] + df_com_real["palpite_v"]
        df_com_real["diff_soma"] = (df_com_real["soma_real"] - df_com_real["soma_palpite"]).abs()
        
        df_zicados = df_com_real[df_com_real["diff_soma"] == 1]
        if not df_zicados.empty:
            zicado_counts = df_zicados.groupby(["participante", "arroba"]).size().reset_index(name="valor")
            zicado_counts_sorted = zicado_counts.sort_values(by="valor", ascending=False).head(3)
            for _, row in zicado_counts_sorted.iterrows():
                resultado["zicado"].append({
                    "participante": row["participante"],
                    "arroba": row["arroba"],
                    "valor": int(row["valor"])
                })

    # ── 5. Golfinho ──────────────────────────────────────────────────────
    if df_historico is not None and not df_historico.empty:
        golfinhos = []
        for (nome, arroba), df_part in df_historico.groupby(["participante", "arroba"]):
            if len(df_part) >= 2:
                df_part_sorted = df_part.sort_values(by="data_hora").copy()
                df_part_sorted["delta"] = df_part_sorted["posicao"].shift(1) - df_part_sorted["posicao"]
                alternancia_total = int(df_part_sorted["delta"].abs().sum())
                if alternancia_total > 0:
                    golfinhos.append({
                        "participante": nome,
                        "arroba": arroba,
                        "valor": alternancia_total
                    })
        if golfinhos:
            top_golfinhos = sorted(golfinhos, key=lambda x: x["valor"], reverse=True)[:3]
            resultado["golfinho"] = top_golfinhos

    return resultado
