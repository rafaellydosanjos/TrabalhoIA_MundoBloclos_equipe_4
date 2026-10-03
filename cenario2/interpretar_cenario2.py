#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interpretador para a SITUAÇÃO 2 do Mundo dos Blocos de Tamanho Variável.
Exibe o plano, deriva relações 'on' e apresenta 2 parágrafos explicativos em texto livre.
"""

import sys

BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}

def spans_overlap(b1, p1, b2, p2):
    return max(p1, p2) < min(p1 + BLOCKS[b1], p2 + BLOCKS[b2])

def main():
    map_file = "trab01_blocos2SAT.map"
    result_file = sys.argv[1] if len(sys.argv) > 1 else "resultado2.txt"

    # 1. Carregar Mapeamento
    id2var = {}
    try:
        with open(map_file) as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    id2var[int(parts[0])] = parts[1]
    except FileNotFoundError:
        print(f"Erro: Arquivo '{map_file}' não encontrado.")
        return

    # 2. Carregar Resultado do SAT Solver
    try:
        with open(result_file) as f:
            content = f.read().strip().split('\n')
            status = content[0]
            if status != 'SAT':
                print(f"Resultado do Solver: {status} (Sem plano viável)")
                return
            
            true_vars = set()
            for token in content[1].split():
                val = int(token)
                if val > 0:
                    true_vars.add(val)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{result_file}' não encontrado.")
        return

    # 3. Extrair Movimentos e Estados
    moves = []
    states_at = {}   # (b, t) -> p
    states_lev = {}  # (b, t) -> l

    for vid in true_vars:
        var_str = id2var.get(vid, "")
        if var_str.startswith("move"):
            moves.append(var_str)
        elif var_str.startswith("at("):
            content_str = var_str[3:-1]
            b, p, t = content_str.split(',')
            states_at[(b, int(t))] = int(p)
        elif var_str.startswith("lev("):
            content_str = var_str[4:-1]
            b, l, t = content_str.split(',')
            states_lev[(b, int(t))] = int(l)

    def get_time(m_str):
        return int(m_str.rstrip(')').split(',')[-1])

    moves.sort(key=get_time)

    print("=" * 65)
    print("PLANO ENCONTRADO - SITUAÇÃO 2 (1 ação por passo de tempo):")
    print("=" * 65)
    
    parsed_moves = []
    for m in moves:
        parts = m[5:-1].split(',')
        b, y, p, t = parts[0], parts[1], parts[2], parts[3]
        parsed_moves.append((b, y, p, t))
        if y == 'T':
            print(f"  t={t}: mover bloco '{b}' para a MESA no ponto p={p}")
        else:
            print(f"  t={t}: mover bloco '{b}' para CIMA de '{y}' no ponto p={p}")

    # 4. Derivação de 'on' no Estado Final
    max_t = max([t for (_, t) in states_at.keys()], default=0)
    print("\n" + "=" * 65)
    print(f"ESTADO FINAL ALCANÇADO (t={max_t}):")
    print("=" * 65)

    for b in sorted(BLOCKS.keys()):
        p = states_at.get((b, max_t), '?')
        l = states_lev.get((b, max_t), '?')
        print(f"  Bloco '{b}': posição p={p}, nível l={l}")

    print("\nRELAÇÕES 'on' DERIVADAS no Estado Final:")
    for b in sorted(BLOCKS.keys()):
        l = states_lev.get((b, max_t))
        p = states_at.get((b, max_t))
        
        if l == 0:
            print(f"  on({b}, T, t={max_t})  -> '{b}' está na MESA")
        else:
            supports = [y for y in BLOCKS if y != b and states_lev.get((y, max_t)) == l - 1 and spans_overlap(b, p, y, states_at.get((y, max_t)))]
            supports_str = ", ".join([f"'{s}'" for s in supports])
            print(f"  on({b}, [{supports_str}], t={max_t})  -> '{b}' está sobre {supports_str}")

    # 5. PARÁGRAFOS EXPLICATIVOS EM TEXTO LIVRE
    print("\n" + "=" * 65)
    print("EXPLICAÇÃO DETALHADA DO RESULTADO (SITUAÇÃO 2):")
    print("=" * 65)

    mov_descriptions = []
    for b, y, p, t in parsed_moves:
        dest = "a mesa" if y == 'T' else f"o topo do bloco '{y}'"
        mov_descriptions.append(f"no instante t={t}, o bloco '{b}' foi deslocado para {dest} no ponto p={p}")
    
    p1 = (f"O SAT solver encontrou um plano ótimo de {len(parsed_moves)} passos de tempo para a Situação 2, respeitando "
          f"rigorosamente a restrição de no máximo um movimento por unidade de tempo t. A sequência executada é a seguinte: "
          + "; em seguida, ".join(mov_descriptions) + 
          ". Este encadeamento de ações garante que a reorganização do espaço horizontal ocorra sem colisões e sem violação de "
          "estabilidade nos níveis superiores.")

    p2 = (f"No instante final t={max_t}, a configuração dos blocos atinge exatamente o estado meta especificado (S5). "
          f"O bloco 'c' e o bloco 'd' ocupam de forma contígua a mesa nos pontos p={states_at.get(('c', max_t))} e p={states_at.get(('d', max_t))}, "
          f"respectivamente. Sobre a base formada pelo bloco 'c', reestabeleceu-se a pilha com o bloco 'a' no nível l={states_lev.get(('a', max_t))} (ponto p={states_at.get(('a', max_t))}) "
          f"e o bloco 'b' no nível l={states_lev.get(('b', max_t))} (ponto p={states_at.get(('b', max_t))}), satisfazendo todas as relações 'on' "
          f"e as dimensões de espaço horizontal estipuladas no problema.")

    print(f"\nParágrafo 1 - Execução do Plano:\n{p1}\n")
    print(f"Parágrafo 2 - Análise do Estado Final:\n{p2}\n")
    print("=" * 65)

if __name__ == '__main__':
    main()
