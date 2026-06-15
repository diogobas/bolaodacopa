import unittest
import pandas as pd
import numpy as np
from app.utils import statistics


class TestStatistics(unittest.TestCase):
    def setUp(self):
        # Cria um DataFrame de histórico fictício para testar as métricas
        # Participante A: 1º -> 2º -> 1º (Mais consistente, líder 2 vezes, melhor pontuação: 120)
        # Participante B: 2º -> 1º -> 3º (Líder 1 vez, subiu 1 pos, caiu 2 pos)
        # Participante C: 3º -> 3º -> 2º (Subiu 1 pos)
        self.mock_data = pd.DataFrame([
            # Rodada 1
            {"data_hora": "2026-06-10 10:00:00", "coleta_id": "R1", "participante": "Part A", "arroba": "@a", "posicao": 1, "pontos": 100, "placar_exato": 3, "sem_pontos": 1},
            {"data_hora": "2026-06-10 10:00:00", "coleta_id": "R1", "participante": "Part B", "arroba": "@b", "posicao": 2, "pontos": 90, "placar_exato": 2, "sem_pontos": 2},
            {"data_hora": "2026-06-10 10:00:00", "coleta_id": "R1", "participante": "Part C", "arroba": "@c", "posicao": 3, "pontos": 80, "placar_exato": 1, "sem_pontos": 3},
            # Rodada 2
            {"data_hora": "2026-06-10 11:00:00", "coleta_id": "R2", "participante": "Part A", "arroba": "@a", "posicao": 2, "pontos": 110, "placar_exato": 6, "sem_pontos": 1},
            {"data_hora": "2026-06-10 11:00:00", "coleta_id": "R2", "participante": "Part B", "arroba": "@b", "posicao": 1, "pontos": 115, "placar_exato": 4, "sem_pontos": 2},
            {"data_hora": "2026-06-10 11:00:00", "coleta_id": "R2", "participante": "Part C", "arroba": "@c", "posicao": 3, "pontos": 85, "placar_exato": 2, "sem_pontos": 4},
            # Rodada 3
            {"data_hora": "2026-06-10 12:00:00", "coleta_id": "R3", "participante": "Part A", "arroba": "@a", "posicao": 1, "pontos": 120, "placar_exato": 10, "sem_pontos": 2},
            {"data_hora": "2026-06-10 12:00:00", "coleta_id": "R3", "participante": "Part B", "arroba": "@b", "posicao": 3, "pontos": 118, "placar_exato": 5, "sem_pontos": 8},
            {"data_hora": "2026-06-10 12:00:00", "coleta_id": "R3", "participante": "Part C", "arroba": "@c", "posicao": 2, "pontos": 95, "placar_exato": 2, "sem_pontos": 12},
        ])

    def test_global_statistics(self):
        stats = statistics.calculate_global_statistics(self.mock_data)
        
        # 1. Valida Dias na Liderança
        dias_lideranca = {x["arroba"]: x["coleta_id"] for x in stats["dias_lideranca"]}
        self.assertEqual(dias_lideranca.get("@a"), 2)  # Part A liderou nas coletas R1 e R3
        self.assertEqual(dias_lideranca.get("@b"), 1)  # Part B liderou na coleta R2
        self.assertNotIn("@c", dias_lideranca)          # Part C nunca liderou
        
        # 2. Valida Melhor Pontuação
        self.assertEqual(stats["melhor_pontuacao"]["arroba"], "@a")
        self.assertEqual(stats["melhor_pontuacao"]["valor"], 120)
        
        # 3. Valida Maior Subida (Part B subiu 1 pos, Part A subiu 1 pos de R2 para R3, Part C subiu 1 pos)
        self.assertEqual(stats["maior_subida"]["valor"], 1)
        
        # 4. Valida Maior Queda (Part B caiu de 1º para 3º -> caiu 2 posições de R2 para R3)
        self.assertEqual(stats["maior_queda"]["arroba"], "@b")
        self.assertEqual(stats["maior_queda"]["valor"], 2)
        
        # 5. Valida Participante Mais Consistente (Part A: std de [1, 2, 1] = 0.58; Part C: std de [3, 3, 2] = 0.58)
        self.assertIn(stats["mais_consistente"]["arroba"], ["@a", "@c"])

        # 6. Valida Recordista de Placares Exatos (Part A com 10 no último snapshot R3)
        self.assertEqual(stats["mais_placares_exatos"]["arroba"], "@a")
        self.assertEqual(stats["mais_placares_exatos"]["valor"], 10)

        # 7. Valida Recordista Sem Pontos (Part C com 12 no último snapshot R3)
        self.assertEqual(stats["mais_sem_pontos"]["arroba"], "@c")
        self.assertEqual(stats["mais_sem_pontos"]["valor"], 12)

    def test_individual_statistics(self):
        # Testando estatísticas individuais do participante A (@a)
        ind_stats = statistics.calculate_individual_statistics(self.mock_data, "@a")
        
        self.assertEqual(ind_stats["posicao_atual"], 1)
        self.assertEqual(ind_stats["melhor_posicao"], 1)
        self.assertEqual(ind_stats["pior_posicao"], 2)
        self.assertEqual(ind_stats["media_posicao"], 1.3)  # Média de 1, 2, 1 é 1.333... -> arredondado para 1.3
        self.assertEqual(len(ind_stats["evolucao_pontos"]), 3)
        self.assertEqual(ind_stats["evolucao_pontos"][-1]["pontos"], 120)


if __name__ == "__main__":
    unittest.main()
