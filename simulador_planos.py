#!/usr/bin/env python3
"""
simulador_planos.py -- Verificador independente de planos manuais
Mundo dos Blocos de Tamanho Variavel (FIA - Trabalho 1, Funcao 3)

Implementa as regras da Secao 2 do manual (at, lev, clr, overlap, stable e
move(b,y,p,t)) e oferece:
  * apply(): executa um plano passo a passo, validando cada acao;
  * bfs():   busca em largura -> comprimento minimo do plano.

Estado = dicionario {bloco: (p, nivel)}.  Acao = (b, y, p), y em {blocos, 'T'}.

Modo `strict=True`  : exige clr(y) global (leitura literal do manual).
Modo `strict=False` : exige apenas slots livres no nivel-alvo + overlap com y
                      (ajuste adotado nos planos manuais; ver relatorio).
"""
from collections import deque
from math import ceil

L = {'a': 1, 'b': 1, 'c': 2, 'd': 3}      # comprimentos l(b)
MAXP, MAXLEV = 6, 3                        # pontos 0..6 ; niveis 0..3


def slots(b, p):
    return set(range(p, p + L[b]))


def valid_pos(b):
    return range(0, MAXP - L[b] + 1)


def no_overlap(st):
    """Exclusao horizontal: dois blocos no mesmo nivel nao dividem slots."""
    bl = list(st)
    for i in range(len(bl)):
        for j in range(i + 1, len(bl)):
            x, y = bl[i], bl[j]
            if st[x][1] == st[y][1] and slots(x, st[x][0]) & slots(y, st[y][0]):
                return False
    return True


def stable_state(st):
    """Estabilidade: >= ceil(l(b)/2) slots sob b ocupados no nivel l-1."""
    for b, (p, l) in st.items():
        if l > 0:
            sup = sum(1 for s in slots(b, p)
                      if any(o != b and ol == l - 1 and s in slots(o, op)
                             for o, (op, ol) in st.items()))
            if sup < ceil(L[b] / 2):
                return False
    return True


def clr(st, b):
    """clr(b): nenhum bloco no nivel acima de b sobrepondo o span de b."""
    p, l = st[b]
    return not any(o != b and ol == l + 1 and slots(o, op) & slots(b, p)
                   for o, (op, ol) in st.items())


def moves(st, strict=False):
    for b in st:
        if not clr(st, b):
            continue
        for y in list(st) + ['T']:
            if y == b:
                continue
            if y != 'T':
                if strict and not clr(st, y):
                    continue
                lv = st[y][1] + 1
            else:
                lv = 0
            if lv > MAXLEV:
                continue
            for p in valid_pos(b):
                if (p, lv) == st[b]:
                    continue                                   # no-op
                if y != 'T' and not (slots(b, p) & slots(y, st[y][0])):
                    continue                                   # overlap
                new = dict(st)
                new[b] = (p, lv)
                if no_overlap(new) and stable_state(new):      # slots livres + estab.
                    yield (b, y, p), new


def key(st):
    return tuple(sorted(st.items()))


def bfs(init, goal, strict=False, limit=12):
    g = key(goal)
    q, seen = deque([(init, [])]), {key(init)}
    while q:
        st, pl = q.popleft()
        if key(st) == g:
            return pl
        if len(pl) >= limit:
            continue
        for a, n in moves(st, strict):
            if key(n) not in seen:
                seen.add(key(n))
                q.append((n, pl + [a]))
    return None


def apply(st, plan, strict=False):
    """Retorna (lista de estados, None) ou (None, t_da_acao_invalida)."""
    st, out = dict(st), [dict(st)]
    for t, act in enumerate(plan):
        ok = [n for a, n in moves(st, strict) if a == act]
        if not ok:
            return None, t
        st = ok[0]
        out.append(dict(st))
    return out, None


# ------------------------------------------------------------------ cenarios
SIT2_S0 = {'c': (0, 0), 'd': (3, 0), 'a': (0, 1), 'b': (1, 1)}
SIT2_S5 = {'d': (3, 0), 'c': (4, 1), 'a': (4, 2), 'b': (5, 2)}
SIT2_PLANO = [('b', 'T', 2), ('a', 'b', 2), ('c', 'd', 4), ('a', 'c', 4), ('b', 'c', 5)]

SIT3_S0 = {'c': (0, 0), 'a': (3, 0), 'b': (5, 0), 'd': (3, 1)}
SIT3_S7 = {'c': (0, 0), 'a': (0, 1), 'b': (1, 1), 'd': (3, 0)}
SIT3_PLANO = [('d', 'c', 0), ('a', 'b', 5), ('d', 'T', 2),
              ('a', 'c', 0), ('b', 'c', 1), ('d', 'T', 3)]


def fmt(act, t):
    b, y, p = act
    dest = "a MESA" if y == 'T' else f"CIMA de '{y}'"
    return f"t={t}: mover bloco '{b}' para {dest} em p={p}"


if __name__ == '__main__':
    for nome, s0, sf, plano in (("Situacao 2", SIT2_S0, SIT2_S5, SIT2_PLANO),
                                ("Situacao 3", SIT3_S0, SIT3_S7, SIT3_PLANO)):
        print(f"=== {nome} ===")
        est, falha = apply(s0, plano)
        print("plano manual valido:", est is not None and key(est[-1]) == key(sf))
        for t, a in enumerate(plano):
            print("  ", fmt(a, t))
        for strict in (True, False):
            r = bfs(s0, sf, strict)
            modo = "estrito (clr(y) global)" if strict else "relaxado (slots livres)"
            print(f"  BFS {modo}:", "inalcancavel" if r is None else f"{len(r)} acoes")
