#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de CNF para a SITUAÇÃO 2 do Mundo dos Blocos de Tamanho Variável.
Garante EXATAMENTE 1 movimento por unidade de tempo t.
"""

# ==========================================
# CONFIGURAÇÃO DO PROBLEMA (SITUAÇÃO 2)
# ==========================================
BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}
MAX_POINT = 6
MAX_LEVEL = 3
HORIZON = 3  # T = 3 passos para atingir S5

# Estado Inicial (S0 da Situação 2): (ponto_p, nivel_l)
INITIAL = {
    'c': (0, 0),
    'a': (0, 1),
    'b': (1, 1),
    'd': (3, 0)
}

# Estado Meta (S5 da Situação 2): (ponto_p, nivel_l)
GOAL = {
    'c': (0, 0),
    'd': (2, 0),
    'a': (0, 1),
    'b': (1, 1)
}

# ==========================================
# GERENCIAMENTO DE VARIÁVEIS PROPOSICIONAIS
# ==========================================
var_counter = 0
var_map = {}      # (nome, ...) -> id
inv_var_map = {}  # id -> string legivel

def get_var(key_tuple, name_str=""):
    global var_counter
    if key_tuple not in var_map:
        var_counter += 1
        var_map[key_tuple] = var_counter
        inv_var_map[var_counter] = name_str if name_str else str(key_tuple)
    return var_map[key_tuple]

def valid_positions(b):
    return list(range(0, MAX_POINT - BLOCKS[b] + 1))

def spans_overlap(b1, p1, b2, p2):
    start1, end1 = p1, p1 + BLOCKS[b1]
    start2, end2 = p2, p2 + BLOCKS[b2]
    return max(start1, start2) < min(end1, end2)

# ==========================================
# CONSTRUÇÃO DAS CLÁUSULAS CNF
# ==========================================
clauses = []

def add_clause(lits):
    clauses.append(lits)

# 1. Mapear variáveis
for t in range(HORIZON + 1):
    for b in BLOCKS:
        for p in valid_positions(b):
            get_var(('at', b, p, t), f"at({b},{p},{t})")
        for l in range(MAX_LEVEL + 1):
            get_var(('lev', b, l, t), f"lev({b},{l},{t})")
        get_var(('clr', b, t), f"clr({b},{t})")

for t in range(HORIZON):
    for b in BLOCKS:
        for p in valid_positions(b):
            get_var(('mv', b, 'T', p, t), f"move({b},T,{p},{t})")
            for y in BLOCKS:
                if y != b:
                    get_var(('mv', b, y, p, t), f"move({b},{y},{p},{t})")

# 2. Fixar Estado Inicial Rigorosamente em t=0
for b in BLOCKS:
    init_p, init_l = INITIAL[b]
    # Posição verdadeira e posições falsas
    for p in valid_positions(b):
        v = get_var(('at', b, p, 0), "")
        if p == init_p:
            add_clause([v])
        else:
            add_clause([-v])
            
    # Nível verdadeiro e níveis falsos
    for l in range(MAX_LEVEL + 1):
        v = get_var(('lev', b, l, 0), "")
        if l == init_l:
            add_clause([v])
        else:
            add_clause([-v])

# 3. Fixar Estado Meta em t=HORIZON
for b, (p, l) in GOAL.items():
    add_clause([get_var(('at', b, p, HORIZON), "")])
    add_clause([get_var(('lev', b, l, HORIZON), "")])

# 4. Restrições Estruturais em Todos os Instantes
for t in range(HORIZON + 1):
    for b in BLOCKS:
        # Pelo menos uma posição e no máximo uma
        lits_p = [get_var(('at', b, p, t), "") for p in valid_positions(b)]
        add_clause(lits_p)
        for i in range(len(lits_p)):
            for j in range(i + 1, len(lits_p)):
                add_clause([-lits_p[i], -lits_p[j]])

        # Pelo menos um nível e no máximo um
        lits_l = [get_var(('lev', b, l, t), "") for l in range(MAX_LEVEL + 1)]
        add_clause(lits_l)
        for i in range(len(lits_l)):
            for j in range(i + 1, len(lits_l)):
                add_clause([-lits_l[i], -lits_l[j]])

    # Exclusão Horizontal: dois blocos no mesmo nível não compartilham posições
    blocks_list = list(BLOCKS.keys())
    for i in range(len(blocks_list)):
        b1 = blocks_list[i]
        for j in range(i + 1, len(blocks_list)):
            b2 = blocks_list[j]
            for p1 in valid_positions(b1):
                for p2 in valid_positions(b2):
                    if spans_overlap(b1, p1, b2, p2):
                        for l in range(MAX_LEVEL + 1):
                            v_at1 = get_var(('at', b1, p1, t), "")
                            v_lev1 = get_var(('lev', b1, l, t), "")
                            v_at2 = get_var(('at', b2, p2, t), "")
                            v_lev2 = get_var(('lev', b2, l, t), "")
                            add_clause([-v_at1, -v_lev1, -v_at2, -v_lev2])

    # Definição do Predicado Clear (clr)
    for b in BLOCKS:
        v_clr = get_var(('clr', b, t), "")
        for b2 in BLOCKS:
            if b2 != b:
                for p in valid_positions(b):
                    for p2 in valid_positions(b2):
                        if spans_overlap(b, p, b2, p2):
                            for l in range(MAX_LEVEL):
                                v_at = get_var(('at', b, p, t), "")
                                v_lev = get_var(('lev', b, l, t), "")
                                v_at2 = get_var(('at', b2, p2, t), "")
                                v_lev2 = get_var(('lev', b2, l + 1, t), "")
                                add_clause([-v_clr, -v_at, -v_lev, -v_at2, -v_lev2])

# 5. Ações, Transições e Exatamente 1 Movimento por t
for t in range(HORIZON):
    all_moves_t = []
    
    for b in BLOCKS:
        for p in valid_positions(b):
            # Mover para Mesa
            v_mv_T = get_var(('mv', b, 'T', p, t), "")
            all_moves_t.append(v_mv_T)
            
            v_clr_b = get_var(('clr', b, t), "")
            add_clause([-v_mv_T, v_clr_b])
            add_clause([-v_mv_T, get_var(('at', b, p, t + 1), "")])
            add_clause([-v_mv_T, get_var(('lev', b, 0, t + 1), "")])

            # Mover para cima de outro bloco
            for y in BLOCKS:
                if y != b:
                    v_mv_y = get_var(('mv', b, y, p, t), "")
                    all_moves_t.append(v_mv_y)
                    
                    v_clr_y = get_var(('clr', y, t), "")
                    add_clause([-v_mv_y, v_clr_b])
                    add_clause([-v_mv_y, v_clr_y])
                    
                    valid_y_pos = [py for py in valid_positions(y) if spans_overlap(b, p, y, py)]
                    if valid_y_pos:
                        lits_y_pos = [get_var(('at', y, py, t), "") for py in valid_y_pos]
                        add_clause([-v_mv_y] + lits_y_pos)
                    else:
                        add_clause([-v_mv_y]) # Posição inválida proíbe movimento
                    
                    for ly in range(MAX_LEVEL):
                        v_lev_y = get_var(('lev', y, ly, t), "")
                        v_lev_b_next = get_var(('lev', b, ly + 1, t + 1), "")
                        add_clause([-v_mv_y, -v_lev_y, v_lev_b_next])
                    
                    add_clause([-v_mv_y, get_var(('at', b, p, t + 1), "")])

    # OBRIGATÓRIO: Pelo menos 1 movimento deve ocorrer no tempo t
    add_clause(all_moves_t)

    # NO MÁXIMO 1 movimento pode ocorrer no tempo t
    for i in range(len(all_moves_t)):
        for j in range(i + 1, len(all_moves_t)):
            add_clause([-all_moves_t[i], -all_moves_t[j]])

    # Frame Axioms (Persistência do estado quando o bloco NÃO se move)
    for b in BLOCKS:
        moves_of_b = [v for k, v in var_map.items() if k[0] == 'mv' and k[1] == b and k[4] == t]
        for p in valid_positions(b):
            v_at_curr = get_var(('at', b, p, t), "")
            v_at_next = get_var(('at', b, p, t + 1), "")
            add_clause([-v_at_curr] + moves_of_b + [v_at_next])
            
        for l in range(MAX_LEVEL + 1):
            v_lev_curr = get_var(('lev', b, l, t), "")
            v_lev_next = get_var(('lev', b, l, t + 1), "")
            add_clause([-v_lev_curr] + moves_of_b + [v_lev_next])

# ==========================================
# GRAVAÇÃO DOS ARQUIVOS CNF E MAP
# ==========================================
cnf_filename = "trab01_blocos2SAT.cnf"
map_filename = "trab01_blocos2SAT.map"

with open(cnf_filename, "w") as f:
    f.write(f"p cnf {var_counter} {len(clauses)}\n")
    for c in clauses:
        f.write(" ".join(map(str, c)) + " 0\n")

with open(map_filename, "w") as f:
    for vid in sorted(inv_var_map.keys()):
        f.write(f"{vid} {inv_var_map[vid]}\n")

print(f"CNF gerado com SUCESSO! ({var_counter} variaveis, {len(clauses)} clausulas)")
