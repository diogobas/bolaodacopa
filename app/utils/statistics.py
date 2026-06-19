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
        
    subidas_globais = []
    sequencias_globais = []
    consistencias = []
    
    participantes = df.groupby(["participante", "arroba"])
    
    for (nome, arroba), df_part in participantes:
        df_part_sorted = df_part.sort_values(by="data_hora").copy()
        
        df_part_sorted["delta"] = df_part_sorted["posicao"].shift(1) - df_part_sorted["posicao"]
        
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
            
        # 3. Melhor sequência de acertos
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
        subidas_only = [x for x in subidas_globais if "subida" in x]
        if subidas_only:
            record_subida = max(subidas_only, key=lambda x: x["subida"])
            stats["maior_subida"] = {
                "participante": record_subida["participante"],
                "arroba": record_subida["arroba"],
                "valor": record_subida["subida"]
            }
            
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
    
    posicoes = df_part["posicao"].tolist()
    ind_stats["posicao_atual"] = int(posicoes[-1])
    ind_stats["melhor_posicao"] = int(min(posicoes))
    ind_stats["pior_posicao"] = int(max(posicoes))
    ind_stats["media_posicao"] = round(float(np.mean(posicoes)), 1)
    
    ind_stats["evolucao_pontos"] = df_part[["data_hora", "pontos"]].to_dict(orient="records")
    ind_stats["evolucao_ranking"] = df_part[["data_hora", "posicao"]].to_dict(orient="records")
    
    return ind_stats


def calculate_perolas(df_palpites: pd.DataFrame, df_historico: pd.DataFrame = None) -> dict:
    """
    Calcula as estatísticas divertidas "Pérolas do Bolão".

    Métricas disponíveis:
      visionario    — apostou sozinho e acertou o placar
      nostradamus   — mais placares exatos acertados
      ousado        — mais palpites únicos (só ele apostou aquele placar em um jogo)
      maria         — mais vezes coincidiu com o palpite majoritário
      retranqueiro  — menos gols apostados no total
      futebol_arte  — mais gols apostados no total
      zicado        — mais erros por 1 gol de diferença no somatório
      pe_frio       — mais partidas sem nenhum ponto (Sem pontos)
      golfinho      — mais alternâncias de posição no ranking
      rocha         — menos mudanças de posição no ranking
      diplomata     — mais empates apostados
      arroz_feijao  — menor variedade de placares distintos
    """
    resultado = {
        "visionario": [],
        "nostradamus": [],
        "ousado": [],
        "maria": [],
        "retranqueiro": [],
        "futebol_arte": [],
        "zicado": [],
        "pe_frio": [],
        "golfinho": [],
        "rocha": [],
        "diplomata": [],
        "arroz_feijao": [],
    }

    if df_palpites is None or df_palpites.empty:
        return resultado

    df = df_palpites.copy()

    # Usa o snapshot mais recente apenas (última coleta)
    ultimo_coleta_id = df["coleta_id"].iloc[-1]
    df = df[df["coleta_id"] == ultimo_coleta_id].copy()

    if df.empty:
        return resultado

    # Coluna auxiliar de palpite formatado
    df["palpite_str"] = df["palpite_m"].astype(str) + "x" + df["palpite_v"].astype(str)

    # ── 1. Visionário ────────────────────────────────────────────────────────
    # Acertou sozinho o placar exato de uma partida (categoria == 'Placar exato' E único apostador daquele placar)
    df_exatos = df[df["categoria"].str.strip().str.lower() == "placar exato"].copy()
    visionario_counts = {}
    visionario_placares = {}
    if not df_exatos.empty:
        for (mandante, visitante), grupo in df_exatos.groupby(["mandante", "visitante"]):
            contagem = grupo.groupby("palpite_str")["arroba"].count()
            unicos = contagem[contagem == 1].index.tolist()
            for pal_str in unicos:
                linha = grupo[grupo["palpite_str"] == pal_str].iloc[0]
                arroba = linha["arroba"]
                nome = linha["participante"]
                if arroba not in visionario_counts:
                    visionario_counts[arroba] = {"participante": nome, "arroba": arroba, "valor": 0}
                    visionario_placares[arroba] = []
                visionario_counts[arroba]["valor"] += 1
                visionario_placares[arroba].append(f"{mandante} {pal_str} {visitante}")
    if visionario_counts:
        top = sorted(visionario_counts.values(), key=lambda x: x["valor"], reverse=True)[:3]
        for o in top:
            o["placares"] = visionario_placares.get(o["arroba"], [])
        resultado["visionario"] = top

    # ── 2. Nostradamus ───────────────────────────────────────────────────────
    # Ranking exclusivo pela quantidade de placares exatos acertados
    df_exatos_all = df[df["categoria"].str.strip().str.lower() == "placar exato"].copy()
    if not df_exatos_all.empty:
        nostra = df_exatos_all.groupby(["participante", "arroba"]).size().reset_index(name="valor")
        nostra_sorted = nostra.sort_values(by="valor", ascending=False).head(3)
        resultado["nostradamus"] = nostra_sorted[["participante", "arroba", "valor"]].to_dict(orient="records")

    # ── 3. Ousadia e Alegria ─────────────────────────────────────────────────
    # Apostou sozinho (palpite único em um jogo), independente de acertar
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

    # ── 4. Maria vai com as outras ────────────────────────────────────────────
    maria_counts = {}
    maria_placares = {}
    for (mandante, visitante), grupo in df.groupby(["mandante", "visitante"]):
        contagem_palpites = grupo.groupby("palpite_str")["arroba"].count()
        max_count = contagem_palpites.max()
        if max_count < 2:
            continue
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

    # ── 5. Retranqueiro ──────────────────────────────────────────────────────
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

    # ── 6. Futebol Arte ──────────────────────────────────────────────────────
    # Oposto do Retranqueiro: quem mais gols apostou no total
    if not gols_totais.empty:
        gols_arte_sorted = gols_totais.sort_values(by="total_gols_palpite", ascending=False).head(3)
        for _, row in gols_arte_sorted.iterrows():
            resultado["futebol_arte"].append({
                "participante": row["participante"],
                "arroba": row["arroba"],
                "valor": int(row["total_gols_palpite"])
            })

    # ── 7. Zicado ────────────────────────────────────────────────────────────
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

    # ── 8. Pé Frio ───────────────────────────────────────────────────────────
    # Mais partidas sem nenhum ponto (categoria == 'Sem pontos' ou semelhante)
    df_com_real2 = df[(df["placar_real_m"] >= 0) & (df["placar_real_v"] >= 0)].copy()
    if not df_com_real2.empty:
        df_sem_ponto = df_com_real2[
            df_com_real2["categoria"].str.strip().str.lower().isin(["sem pontos", ""])
        ]
        if not df_sem_ponto.empty:
            pe_counts = df_sem_ponto.groupby(["participante", "arroba"]).size().reset_index(name="valor")
            pe_sorted = pe_counts.sort_values(by="valor", ascending=False).head(3)
            for _, row in pe_sorted.iterrows():
                resultado["pe_frio"].append({
                    "participante": row["participante"],
                    "arroba": row["arroba"],
                    "valor": int(row["valor"])
                })

    # ── 9. Golfinho ──────────────────────────────────────────────────────────
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
            resultado["golfinho"] = sorted(golfinhos, key=lambda x: x["valor"], reverse=True)[:3]

    # ── 10. Rocha ────────────────────────────────────────────────────────────
    # Menos mudanças de posição; desempate por menor amplitude (pior - melhor posição)
    if df_historico is not None and not df_historico.empty:
        rochas = []
        for (nome, arroba), df_part in df_historico.groupby(["participante", "arroba"]):
            if len(df_part) >= 2:
                df_part_sorted = df_part.sort_values(by="data_hora").copy()
                df_part_sorted["delta"] = df_part_sorted["posicao"].diff().abs()
                mudancas = int(df_part_sorted["delta"].fillna(0).sum())
                amplitude = int(df_part_sorted["posicao"].max() - df_part_sorted["posicao"].min())
                rochas.append({
                    "participante": nome,
                    "arroba": arroba,
                    "valor": mudancas,
                    "amplitude": amplitude
                })
        if rochas:
            # Ordena por menos mudanças; desempata por menor amplitude
            rochas_sorted = sorted(rochas, key=lambda x: (x["valor"], x["amplitude"]))[:3]
            resultado["rocha"] = rochas_sorted

    # ── 11. Diplomata ─────────────────────────────────────────────────────────
    # Mais empates apostados (palpite_m == palpite_v)
    df_empates = df[df["palpite_m"] == df["palpite_v"]].copy()
    if not df_empates.empty:
        dipl_counts = df_empates.groupby(["participante", "arroba"]).size().reset_index(name="valor")
        dipl_sorted = dipl_counts.sort_values(by="valor", ascending=False).head(3)
        for _, row in dipl_sorted.iterrows():
            resultado["diplomata"].append({
                "participante": row["participante"],
                "arroba": row["arroba"],
                "valor": int(row["valor"])
            })

    # ── 12. Arroz com Feijão ─────────────────────────────────────────────────
    # Menor variedade de placares distintos; desempate por quem mais repetiu seu placar favorito
    arroz = []
    for (nome, arroba), grupo in df.groupby(["participante", "arroba"]):
        contagem_placares = grupo["palpite_str"].value_counts()
        qtd_distintos = int(contagem_placares.nunique() if not contagem_placares.empty else 0)
        # Considera qtd_distintos = número de placares únicos apostados
        qtd_distintos = int(grupo["palpite_str"].nunique())
        placar_fav = contagem_placares.index[0] if not contagem_placares.empty else "N/A"
        repeticoes = int(contagem_placares.iloc[0]) if not contagem_placares.empty else 0
        arroz.append({
            "participante": nome,
            "arroba": arroba,
            "valor": qtd_distintos,
            "repeticoes": repeticoes,
            "placar_fav": placar_fav,
            "info_extra": f"Placar favorito: {placar_fav} ({repeticoes}x)"
        })
    if arroz:
        # Ordena por menos placares distintos; desempata por mais repetições do favorito
        arroz_sorted = sorted(arroz, key=lambda x: (x["valor"], -x["repeticoes"]))[:3]
        resultado["arroz_feijao"] = arroz_sorted

    return resultado
