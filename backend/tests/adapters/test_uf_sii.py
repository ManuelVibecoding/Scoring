from datetime import date

from score.adapters.uf_sii import leer_uf

HTML = """
<div class='meses' id='mes_septiembre'><table><tr>
<th width='40'><strong>22</strong></th><td width='200'>40.900,00</td></tr></table></div>
<div class='meses' id='mes_octubre'><table><tr>
<th width='40'><strong>21</strong></th><td width='200'>41.194,55</td>
<th width='40'><strong>22</strong></th><td width='200'>41.199,85</td></tr></table></div>
"""


def test_lee_el_valor_del_dia_en_su_mes() -> None:
    assert leer_uf(HTML, date(2026, 10, 22)) == 41_199.85
    assert leer_uf(HTML, date(2026, 9, 22)) == 40_900.00


def test_dia_sin_valor() -> None:
    assert leer_uf(HTML, date(2026, 11, 1)) is None
