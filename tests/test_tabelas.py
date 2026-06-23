import unittest

import pandas as pd

from app.views.tabelas import (
    RODADAS,
    format_rodada_label,
    get_default_rodada_index,
    is_rodada_disponivel,
)


class TestTabelasRodadas(unittest.TestCase):
    def test_future_rounds_are_marked_unavailable_before_start_date(self):
        hoje = pd.Timestamp("2026-06-23")

        labels = [format_rodada_label(rodada, hoje) for rodada in RODADAS]

        self.assertEqual(labels[0], "Primeira Rodada (11/06 a 17/06)")
        self.assertEqual(labels[1], "Segunda Rodada (18/06 a 23/06)")
        self.assertEqual(labels[2], "Terceira Rodada (24/06 a 27/06) - indisponível")
        self.assertEqual(labels[3], "Playoffs (28/06 a 19/07) - indisponível")
        self.assertEqual(get_default_rodada_index(RODADAS, hoje), 1)

    def test_third_round_is_available_on_june_24(self):
        hoje = pd.Timestamp("2026-06-24")

        self.assertTrue(is_rodada_disponivel(RODADAS[2], hoje))
        self.assertFalse(is_rodada_disponivel(RODADAS[3], hoje))
        self.assertEqual(format_rodada_label(RODADAS[2], hoje), "Terceira Rodada (24/06 a 27/06)")
        self.assertEqual(get_default_rodada_index(RODADAS, hoje), 2)

    def test_playoffs_are_available_on_june_28(self):
        hoje = pd.Timestamp("2026-06-28")

        self.assertTrue(is_rodada_disponivel(RODADAS[3], hoje))
        self.assertEqual(format_rodada_label(RODADAS[3], hoje), "Playoffs (28/06 a 19/07)")
        self.assertEqual(get_default_rodada_index(RODADAS, hoje), 3)


if __name__ == "__main__":
    unittest.main()
