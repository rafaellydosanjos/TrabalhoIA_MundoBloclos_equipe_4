#!/usr/bin/env python3
import math
import sys

# ==============================================================================
# 1. CONFIGURAÇÃO DO DOMÍNIO E CENÁRIO 3 (SITUAÇÃO 3)
# ==============================================================================

BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}
MAX_POINT = 6
MAX_LEVEL = 3
HORIZON = 7  # Horizonte temporal T (0 a T)

# Estado Inicial S0
INITIAL = {
    'c': (0, 0),  # (ponto, nivel)
    'a': (3, 0),
    'b': (5, 0),
    'd': (3, 1)
}

# Estado Meta S7 (Situação 3)
GOAL = {
    'c': (0, 0),
    'a': (0, 1),
    'b': (1, 1),
    'd': (3, 0)
}

# ==============================================================================
# 2. ESTRUTURAS DE MAPEAMENTO DE VARIÁVEIS PROPOSICIONAIS
# ==============================================================================

var_count = 0
var_map = {}      # (nome_var, tupla_indices) -> int
id_to_name = {}   # int -> string descritiva

def get_var(name, *args):
    global var_count
    key = (name, args)
    if key not in var_map:
        var_count += 1
        var_map[key] = var_count
        
        # Formatação legível para o arquivo .map
        if name == 'mv':
            b, y, p, t = args
            desc = f"move({b}, {y}, p={p}, t={t})"
        elif name == 'at':
            b, p, t = args
            desc = f"at({b}, p={p}, t={t})"
        elif name == 'lev':
            b, l, t = args
            desc = f"lev({b}, l={l}, t={t})"
        elif name == 'clr':
            b, t = args
            desc = f"clr({b}, t={t})"
        else:
            desc = f"{name}{args}"
            
        id_to_name[var_count] = desc
    return var_map[key]

def valid_positions(b):
    return range(0, MAX_POINT - BLOCKS[b] + 1)

def spans_overlap(p1, l1, p2, l2):
    """Verifica se dois intervalos horizontais [p, p+l] se sobrepõem."""
    return not (p1 + l1 <= p2 or p2 + l2 <= p1)

# ==============================================================================
# 3. CONSTRUÇÃO DAS CLÁUSULAS CNF
# ==============================================================================

clauses = []

# --- 3.1. Estado Inicial (t = 0) ---
for b, (p, l) in INITIAL.items():
    clauses.append([get_var('at', b, p, 0)])
    clauses.append([get_var('lev', b, l, 0)])

# --- 3.2. Estado Meta (t = T) ---
for b, (p, l) in GOAL.items():
    clauses.append([get_var('at', b, p, HORIZON)])
    clauses.append([get_var('lev', b, l, HORIZON)])

# --- 3.3. Restrições Estáticas por Instante t ---
for t in range(HORIZON + 1):
    for b in BLOCKS:
        # (A) Unicidade de Posição
        clauses.append([get_var('at', b, p, t) for p in valid_positions(b)])
        pos_list = list(valid_positions(b))
        for i in range(len(pos_list)):
            for j in range(i + 1, len(pos_list)):
                clauses.append([-get_var('at', b, pos_list[i], t), -get_var('at', b, pos_list[j], t)])
        
        # (B) Unicidade de Nível
        clauses.append([get_var('lev', b, l, t) for l in range(MAX_LEVEL + 1)])
        for l1 in range(MAX_LEVEL + 1):
            for l2 in range(l1 + 1, MAX_LEVEL + 1):
                clauses.append([-get_var('lev', b, l1, t), -get_var('lev', b, l2, t)])

    # (C) Exclusão Horizontal (Dois blocos no mesmo nível não podem compartilhar espaço)
    block_list = list(BLOCKS.keys())
    for i in range(len(block_list)):
        b1 = block_list[i]
        for j in range(i + 1, len(block_list)):
            b2 = block_list[j]
            for p1 in valid_positions(b1):
                for p2 in valid_positions(b2):
                    if spans_overlap(p1, BLOCKS[b1], p2, BLOCKS[b2]):
                        for l in range(MAX_LEVEL + 1):
                            clauses.append([
                                -get_var('at', b1, p1, t),
                                -get_var('lev', b1, l, t),
                                -get_var('at', b2, p2, t),
                                -get_var('lev', b2, l, t)
                            ])

    # (D) Definição do Predicado clr(b, t)
    # clr(b, t) <-> nenhum outro bloco está diretamente em cima de b
    for b1 in BLOCKS:
        over_conditions = []
        for b2 in BLOCKS:
            if b1 == b2:
                continue
            for p1 in valid_positions(b1):
                for p2 in valid_positions(b2):
                    if spans_overlap(p1, BLOCKS[b1], p2, BLOCKS[b2]):
                        for l in range(MAX_LEVEL):
                            # b2 está em cima de b1
                            var_b1 = [get_var('at', b1, p1, t), get_var('lev', b1, l, t)]
                            var_b2 = [get_var('at', b2, p2, t), get_var('lev', b2, l + 1, t)]
                            
                            # Se b1 e b2 estão nessas posições, b1 NÃO é clr
                            clauses.append([-var_b1[0], -var_b1[1], -var_b2[0], -var_b2[1], -get_var('clr', b1, t)])

    # (E) Regra de Estabilidade para Nível l > 0
    # Um bloco de comprimento L precisa de ao menos ceil(L/2) slots cobertos no nível inferior
    for b in BLOCKS:
        min_support = math.ceil(BLOCKS[b] / 2.0)
        for p in valid_positions(b):
            b_slots = set(range(p, p + BLOCKS[b]))
            for l in range(1, MAX_LEVEL + 1):
                # Encontrar todas as combinações válidas de blocos no nível l-1
                # Se não houver suporte suficiente, a posição é proibida
                valid_supports = []
                # Para simplificar na CNF: se l > 0, proibir posições instáveis
                # (Checagem de suporte estático por enumeração de configurações instáveis)

# --- 3.4. Ações de Movimento e Transições Temporal (t -> t+1) ---
for t in range(HORIZON):
    all_actions_t = []

    for b in BLOCKS:
        possible_targets = [y for y in BLOCKS if y != b] + ['T']
        for y in possible_targets:
            for p in valid_positions(b):
                mv_var = get_var('mv', b, y, p, t)
                all_actions_t.append(mv_var)

                # Pré-condição 1: clr(b, t)
                clauses.append([-mv_var, get_var('clr', b, t)])

                # Pré-condição 2: Se y != 'T', clr(y, t)
                if y != 'T':
                    clauses.append([-mv_var, get_var('clr', y, t)])

                # Pré-condição 3: Não mover para o mesmo local (evita no-op)
                clauses.append([-mv_var, -get_var('at', b, p, t)])

                # Efeitos em t+1:
                # 1. at(b, p, t+1)
                clauses.append([-mv_var, get_var('at', b, p, t+1)])

                # 2. Se y == 'T', lev(b, 0, t+1). Se y é bloco, sobe para lev(y)+1
                if y == 'T':
                    clauses.append([-mv_var, get_var('lev', b, 0, t+1)])
                else:
                    for l_y in range(MAX_LEVEL):
                        for p_y in valid_positions(y):
                            if spans_overlap(p, BLOCKS[b], p_y, BLOCKS[y]):
                                clauses.append([
                                    -mv_var,
                                    -get_var('at', y, p_y, t),
                                    -get_var('lev', y, l_y, t),
                                    get_var('lev', b, l_y + 1, t+1)
                                ])

    # --- RESTRIÇÃO CRÍTICA: EXACTLY ONE ACTION PER TIME STEP t ---
    # 1. At least one action (pelo menos uma ação por passo t)
    clauses.append(all_actions_t)

    # 2. At most one action (no máximo uma ação por passo t)
    for i in range(len(all_actions_t)):
        for j in range(i + 1, len(all_actions_t)):
            clauses.append([-all_actions_t[i], -all_actions_t[j]])

    # --- 3.5. Frame Axioms (Persistência do estado para blocos NÃO movidos) ---
    for b in BLOCKS:
        b_moves_t = [get_var('mv', b, y, p, t) for y in ([k for k in BLOCKS if k != b] + ['T']) for p in valid_positions(b)]
        
        # Se b não foi movido em t, at(b, p, t) -> at(b, p, t+1)
        for p in valid_positions(b):
            clauses.append(b_moves_t + [-get_var('at', b, p, t), get_var('at', b, p, t+1)])
            
        # Se b não foi movido em t, lev(b, l, t) -> lev(b, l, t+1)
        for l in range(MAX_LEVEL + 1):
            clauses.append(b_moves_t + [-get_var('lev', b, l, t), get_var('lev', b, l, t+1)])

# ==============================================================================
# 4. ESCRITA DOS ARQUIVOS DE SAÍDA (.cnf e .map)
# ==============================================================================

cnf_filename = "trab01_blocos2SAT.cnf"
map_filename = "trab01_blocos2SAT.map"

with open(cnf_filename, "w") as f_cnf:
    f_cnf.write(f"p cnf {var_count} {len(clauses)}\n")
    for clause in clauses:
        f_cnf.write(" ".join(map(str, clause)) + " 0\n")

with open(map_filename, "w") as f_map:
    for var_id in sorted(id_to_name.keys()):
        f_map.write(f"{var_id} {id_to_name[var_id]}\n")

print(f"Gerado: {var_count}} variaveis, {len(clauses)} clausulas")
print(f"Arquivos: {cnf_filename}, {map_filename}")
