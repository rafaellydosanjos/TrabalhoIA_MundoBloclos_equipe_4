"""
Mundo dos Blocos de Tamanho Variavel - Codificacao CNF Completa.

Uso:
  python3 bw2cnf_axioms2_corrigido.py 1          # Situacao 1: S0 -> Sf4
  python3 bw2cnf_axioms2_corrigido.py 2          # Situacao 2: S0 -> S5
  python3 bw2cnf_axioms2_corrigido.py 3          # Situacao 3: S0 -> S7
  python3 bw2cnf_axioms2_corrigido.py 1 -T 3     # muda o horizonte (prova de otimalidade)
  python3 bw2cnf_axioms2_corrigido.py --listar   # mostra os cenarios disponiveis

Cada cenario grava em sua propria pasta, sem sobrescrever os outros:
  cenarioN/trab01_blocos2SAT.cnf
  cenarioN/trab01_blocos2SAT.map
Depois: minisat cenarioN/trab01_blocos2SAT.cnf cenarioN/resultadoN.txt
"""

import argparse
import itertools
import os

# Configuracao fixa do dominio
BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}   # nome -> comprimento
TABLE = 'T'
MAX_POINT = 6                                # pontos 0..6 (6 slots)
MAX_LEVEL = len(BLOCKS) - 1                  # niveis 0..3

# Cenarios do enunciado: bloco -> (ponto inicial, nivel)
# ------------------------------------------------------------
# ORDEM PARCIAL (phi1 -<P phi2): "phi2 so pode valer depois que phi1 ja
# tiver valido em algum instante t' <= t".
# Cada condicao phi e um dicionario lido como CONJUNCAO:
#   {'d': 2}       -> at(d,2,t)                 (so a posicao)
#   {'d': (2, 0)}  -> at(d,2,t) ^ lev(d,0,t)    (posicao e nivel)
# Formato de cada ordem: (nome, phi1, phi2)
# ------------------------------------------------------------
# 'horizonte' = T minimo (com T-1 o miniSAT devolve UNSAT).
# ============================================================
S0_SIT1 = {'c': (0, 0), 'a': (3, 0), 'b': (5, 0), 'd': (3, 1)}

CENARIOS = {
    '1': {
        'descricao': 'Situacao 1: S0 -> Sf4',
        'inicial':   S0_SIT1,
        'meta':      {'c': (0, 0), 'a': (0, 1), 'd': (2, 0), 'b': (5, 0)},
        'horizonte': 4,
        #   clausula: NOT at(a,0,t) v at(d,2,0) v ... v at(d,2,t)
        'ordens': [
            ('d na posicao 2 antes de a na posicao 0', {'d': 2}, {'a': 0}),
        ],
    },
    '2': {
        'descricao': 'Situacao 2: S0 -> S5',
        'inicial':   {'c': (0, 0), 'd': (3, 0), 'a': (0, 1), 'b': (1, 1)},
        'meta':      {'d': (3, 0), 'c': (4, 1), 'a': (4, 2), 'b': (5, 2)},
        'horizonte': 5,
        'ordens': [
            ('c sobre d antes de a sobre c', {'c': (4, 1)}, {'a': (4, 2)}),
            ('c sobre d antes de b sobre c', {'c': (4, 1)}, {'b': (5, 2)}),
        ],
    },
    '3': {
        'descricao': 'Situacao 3: S0 -> S7',
        'inicial':   S0_SIT1,
        'meta':      {'c': (0, 0), 'a': (0, 1), 'b': (1, 1), 'd': (3, 0)},
        'horizonte': 6,
        'ordens': [
            ('a sobre c antes de b sobre c', {'a': (0, 1)}, {'b': (1, 1)}),
            ('b sobre c antes de d na mesa em p=3', {'b': (1, 1)}, {'d': (3, 0)}),
        ],
    },
    # Demais metas Situacao 1 (opcionais)
    '1-sf1': {'descricao': 'Situacao 1: S0 -> Sf1', 'inicial': S0_SIT1, 'horizonte': 9, 'ordens': [],
              'meta': {'d': (3, 0), 'a': (4, 1), 'b': (5, 1), 'c': (4, 2)}},
    '1-sf2': {'descricao': 'Situacao 1: S0 -> Sf2', 'inicial': S0_SIT1, 'horizonte': 10, 'ordens': [],
              'meta': {'d': (3, 0), 'c': (4, 1), 'a': (4, 2), 'b': (5, 2)}},
    '1-sf3': {'descricao': 'Situacao 1: S0 -> Sf3', 'inicial': S0_SIT1, 'horizonte': 10, 'ordens': [],
              'meta': {'c': (0, 0), 'a': (2, 0), 'd': (0, 1), 'b': (5, 0)}},
}

parser = argparse.ArgumentParser(description='Gera o CNF de um cenario do Mundo dos Blocos.')
parser.add_argument('cenario', nargs='?', default='1', help='1, 2, 3, 1-sf1, 1-sf2 ou 1-sf3 (padrao: 1)')
parser.add_argument('-T', '--horizonte', type=int, help='sobrescreve o horizonte do cenario')
parser.add_argument('--listar', action='store_true', help='lista os cenarios e sai')
args = parser.parse_args()

if args.listar:
    for k, c in CENARIOS.items():
        print(f"  {k:6s} {c['descricao']}  (T minimo = {c['horizonte']})")
    raise SystemExit
if args.cenario not in CENARIOS:
    parser.error(f"cenario '{args.cenario}' nao existe. Use --listar.")

CEN = CENARIOS[args.cenario]
INITIAL = CEN['inicial']
GOAL    = CEN['meta']
HORIZON = args.horizonte if args.horizonte is not None else CEN['horizonte']
PARTIAL_ORDERS = CEN['ordens']
OUT_DIR = f'cenario{args.cenario}'
# ---- fim da configuracao ----

def validar_configuracao():
    """Confere o cenario antes de gerar o CNF, com mensagens claras."""
    erros = []
    if HORIZON < 0:
        erros.append(f'HORIZON deve ser >= 0 (recebido {HORIZON}).')

    def checa_pos(onde, b, pos, exige_nivel=True):
        if b not in BLOCKS:
            erros.append(f'{onde}: bloco "{b}" nao existe (blocos: {list(BLOCKS)}).')
            return
        if isinstance(pos, tuple):
            if len(pos) != 2:
                erros.append(f'{onde}: {b} deve ser (ponto, nivel), recebido {pos}.')
                return
            p, l = pos
        elif exige_nivel:
            erros.append(f'{onde}: {b} deve ser (ponto, nivel), recebido {pos}.')
            return
        else:
            p, l = pos, 0
        if p not in valid_positions(BLOCKS[b]):
            erros.append(f'{onde}: {b} (comprimento {BLOCKS[b]}) nao pode comecar em p={p}; '
                         f'validas: {list(valid_positions(BLOCKS[b]))}.')
        if not 0 <= l <= MAX_LEVEL:
            erros.append(f'{onde}: nivel {l} de {b} fora de 0..{MAX_LEVEL}.')

    faltando = set(BLOCKS) - set(INITIAL)
    if faltando:
        erros.append(f'INITIAL: faltam os blocos {sorted(faltando)} (todos precisam de posicao em t=0).')
    for b, pos in INITIAL.items():
        checa_pos('INITIAL', b, pos)
    for b, pos in GOAL.items():
        checa_pos('GOAL', b, pos)
    for nome, phi1, phi2 in PARTIAL_ORDERS:
        for phi in (phi1, phi2):
            for b, pos in phi.items():
                checa_pos(f'ordem "{nome}"', b, pos, exige_nivel=False)
    if erros:
        raise SystemExit('Configuracao invalida:\n  - ' + '\n  - '.join(erros))

def valid_positions(L):
    return range(MAX_POINT - L + 1)

def spans_overlap(b1, p1, b2, p2):
    """True se [p1, p1+l1] e [p2, p2+l2] compartilham algum slot."""
    return p1 < p2 + BLOCKS[b2] and p2 < p1 + BLOCKS[b1]

validar_configuracao()

# Variaveis: at, lev, clr, mv  (on NAO e codificado, e derivado)

at, lev, clr, mv = {}, {}, {}, {}
next_id = 0

def new_var():
    global next_id
    next_id += 1
    return next_id

for t in range(HORIZON + 1):
    for b, L in BLOCKS.items():
        for p in valid_positions(L):
            at[(b, p, t)] = new_var()
        for l in range(MAX_LEVEL + 1):
            lev[(b, l, t)] = new_var()
        clr[(b, t)] = new_var()

for t in range(HORIZON):
    for b, L in BLOCKS.items():
        for y in [x for x in BLOCKS if x != b] + [TABLE]:
            for p in valid_positions(L):
                mv[(b, y, p, t)] = new_var()

clauses = []

def add(*lits):
    clauses.append(list(lits))

def moves_of(b, t):
    """Todas as acoes que movem o bloco b no passo t."""
    return [v for (bb, y, p, tt), v in mv.items() if bb == b and tt == t]

# 3.1 ESTADO INICIAL (t = 0)

for b, L in BLOCKS.items():
    p0, l0 = INITIAL[b]
    for p in valid_positions(L):
        add(at[(b, p, 0)] if p == p0 else -at[(b, p, 0)])
    for l in range(MAX_LEVEL + 1):
        add(lev[(b, l, 0)] if l == l0 else -lev[(b, l, 0)])

# 3.2 META (t = HORIZON) - blocos fora de GOAL ficam livres

for b, (pg, lg) in GOAL.items():
    add(at[(b, pg, HORIZON)])
    add(lev[(b, lg, HORIZON)])

# 3.3 (A),(B) UNICIDADE: cada bloco em exatamente uma posicao e um nivel

for t in range(HORIZON + 1):
    for b, L in BLOCKS.items():
        ps = [at[(b, p, t)] for p in valid_positions(L)]
        add(*ps)                                   # (A) pelo menos uma posicao
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                add(-ps[i], -ps[j])                # (B) no maximo uma posicao
        ls = [lev[(b, l, t)] for l in range(MAX_LEVEL + 1)]
        add(*ls)                                   # (A) pelo menos um nivel
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                add(-ls[i], -ls[j])                # (B) no maximo um nivel

# 3.5 FRAME AXIOMS (at e lev): so mudam se o proprio bloco for movido

for t in range(HORIZON):
    for b, L in BLOCKS.items():
        movs = moves_of(b, t)
        for p in valid_positions(L):
            add(-at[(b, p, t)], at[(b, p, t + 1)], *movs)
            add(at[(b, p, t)], -at[(b, p, t + 1)],
                *[mv[(b, y, p, t)] for y in [x for x in BLOCKS if x != b] + [TABLE]])
        for l in range(MAX_LEVEL + 1):
            # lev(b,l,t) persiste / so muda se b for movido
            add(-lev[(b, l, t)], lev[(b, l, t + 1)], *movs)
            add(lev[(b, l, t)], -lev[(b, l, t + 1)], *movs)

# IMPLEMENTAÇÃO DAS REGRAS DO DOMÍNIO (GANCHOS COMPLETA)

def clausulas_exclusao_horizontal():   # 3.3 (C)
    """Dois blocos distintos no mesmo nivel nao cobrem o mesmo slot.
    -at(b1,p1,t) v -at(b2,p2,t) v -lev(b1,l,t) v -lev(b2,l,t)"""
    res = []
    blocks_list = list(BLOCKS.keys())
    for t in range(HORIZON + 1):
        for i in range(len(blocks_list)):
            b1 = blocks_list[i]
            for j in range(i + 1, len(blocks_list)):
                b2 = blocks_list[j]
                for p1 in valid_positions(BLOCKS[b1]):
                    for p2 in valid_positions(BLOCKS[b2]):
                        if spans_overlap(b1, p1, b2, p2):
                            for l in range(MAX_LEVEL + 1):
                                res.append([
                                    -at[(b1, p1, t)],
                                    -at[(b2, p2, t)],
                                    -lev[(b1, l, t)],
                                    -lev[(b2, l, t)]
                                ])
    return res

def clausulas_estabilidade():          # 3.3 (D)
    """Se b esta em (p,l) com l > 0, pelo menos ceil(l(b)/2) slots sob seu
    span devem estar cobertos por blocos no nivel l-1."""
    res = []
    for t in range(HORIZON + 1):
        for b, L in BLOCKS.items():
            req = (L + 1) // 2
            other_blocks = [x for x in BLOCKS if x != b]
            for p in valid_positions(L):
                span = list(range(p, p + L))
                subset_size = L - req + 1
                for U in itertools.combinations(span, subset_size):
                    supp_info = []
                    for b_prime in other_blocks:
                        L_prime = BLOCKS[b_prime]
                        pos_list = [p_prime for p_prime in valid_positions(L_prime)
                                    if any(p_prime <= s < p_prime + L_prime for s in U)]
                        if pos_list:
                            supp_info.append((b_prime, pos_list))
                    
                    if not supp_info:
                        for l in range(1, MAX_LEVEL + 1):
                            res.append([-at[(b, p, t)], -lev[(b, l, t)]])
                    else:
                        for l in range(1, MAX_LEVEL + 1):
                            choices = []
                            for b_prime, pos_list in supp_info:
                                l_lit = lev[(b_prime, l - 1, t)]
                                at_lits = [at[(b_prime, p_prime, t)] for p_prime in pos_list]
                                choices.append(([l_lit], at_lits))
                            
                            for prod in itertools.product(*choices):
                                clause = [-at[(b, p, t)], -lev[(b, l, t)]]
                                for lits in prod:
                                    clause.extend(lits)
                                res.append(clause)
    return res

def clausulas_clear():                 # 3.3 (E)
    """clr(b,t) <-> nenhum bloco y no nivel lev(b)+1 com span sobreposto ao de b."""
    res = []
    for t in range(HORIZON + 1):
        for b, L in BLOCKS.items():
            other_blocks = [y for y in BLOCKS if y != b]
            for pb in valid_positions(L):
                for l in range(MAX_LEVEL + 1):
                    if l == MAX_LEVEL:
                        res.append([-at[(b, pb, t)], -lev[(b, l, t)], clr[(b, t)]])
                        continue

                    supp_info = []
                    for y in other_blocks:
                        Ly = BLOCKS[y]
                        pos_list = [py for py in valid_positions(Ly) if spans_overlap(b, pb, y, py)]
                        if pos_list:
                            supp_info.append((y, pos_list))
                            for py in pos_list:
                                # clr(b,t) -> NOT (y sobre b no nivel l+1)
                                res.append([
                                    -clr[(b, t)],
                                    -at[(b, pb, t)],
                                    -lev[(b, l, t)],
                                    -at[(y, py, t)],
                                    -lev[(y, l + 1, t)]
                                ])
                    
                    if not supp_info:
                        res.append([-at[(b, pb, t)], -lev[(b, l, t)], clr[(b, t)]])
                    else:
                        choices = []
                        for y, pos_list in supp_info:
                            l_lit = lev[(y, l + 1, t)]
                            at_lits = [at[(y, py, t)] for py in pos_list]
                            choices.append(([l_lit], at_lits))
                        
                        for prod in itertools.product(*choices):
                            clause = [-at[(b, pb, t)], -lev[(b, l, t)], clr[(b, t)]]
                            for lits in prod:
                                clause.extend(lits)
                            res.append(clause)
    return res

def clausulas_precondicoes_move():     # 3.4 (G)
    """mv(b,y,p,t) -> pre-condicoes e efeitos de transicao."""
    res = []
    for t in range(HORIZON):
        for b, Lb in BLOCKS.items():
            for p in valid_positions(Lb):
                targets = [x for x in BLOCKS if x != b] + [TABLE]
                for y in targets:
                    mvar = mv[(b, y, p, t)]

                    # 1. Pre-condicao: clr(b, t)
                    res.append([-mvar, clr[(b, t)]])

                    # 2. NAO exigimos clr(y, t) inteiro: com blocos de tamanho
                    #    variavel, y pode ter algo em parte do topo e ainda haver
                    #    espaco para b (ex.: a e b lado a lado sobre c). O que
                    #    importa sao os slots de destino livres (item "Slots no
                    #    nivel-alvo livres" abaixo), que ja garantem a fisica.

                    # 3. Efeito: at(b, p, t+1)
                    res.append([-mvar, at[(b, p, t + 1)]])

                    # 4. Destino & Efeito de Nivel
                    if y == TABLE:
                        # Nao pode ser no-op no nivel 0
                        res.append([-mvar, -at[(b, p, t)], -lev[(b, 0, t)]])
                        # Efeito: lev(b, 0, t+1)
                        res.append([-mvar, lev[(b, 0, t + 1)]])

                        # Slots do nivel 0 livres de outros blocos
                        for b_prime in [x for x in BLOCKS if x != b]:
                            Lp = BLOCKS[b_prime]
                            for p_prime in valid_positions(Lp):
                                if spans_overlap(b, p, b_prime, p_prime):
                                    # nivel 0 livre E nada "pendurado" acima (sob ponte/balanco)
                                    for l2 in range(MAX_LEVEL + 1):
                                        res.append([-mvar, -at[(b_prime, p_prime, t)], -lev[(b_prime, l2, t)]])
                    else:
                        Ly = BLOCKS[y]
                        for py in valid_positions(Ly):
                            if not spans_overlap(b, p, y, py):
                                res.append([-mvar, -at[(y, py, t)]])
                            else:
                                for ly in range(MAX_LEVEL):
                                    target_level = ly + 1
                                    # Efeito: lev(b, target_level, t+1)
                                    res.append([-mvar, -at[(y, py, t)], -lev[(y, ly, t)], lev[(b, target_level, t + 1)]])
                                    # Nao pode ser no-op
                                    res.append([-mvar, -at[(y, py, t)], -lev[(y, ly, t)], -at[(b, p, t)], -lev[(b, target_level, t)]])

                                    # Slots no nivel-alvo livres
                                    for b_prime in [x for x in BLOCKS if x not in (b, y)]:
                                        Lp = BLOCKS[b_prime]
                                        for p_prime in valid_positions(Lp):
                                            if spans_overlap(b, p, b_prime, p_prime):
                                                for l2 in range(target_level, MAX_LEVEL + 1):
                                                    res.append([
                                                        -mvar,
                                                        -at[(y, py, t)],
                                                        -lev[(y, ly, t)],
                                                        -at[(b_prime, p_prime, t)],
                                                        -lev[(b_prime, l2, t)]
                                                    ])

                        # Bloqueia se o nivel do bloco y exceder MAX_LEVEL
                        for py in valid_positions(Ly):
                            res.append([-mvar, -at[(y, py, t)], -lev[(y, MAX_LEVEL, t)]])
    return res

def clausulas_acao_unica():            # No maximo 1 acao por passo
    res = []
    for t in range(HORIZON):
        all_moves = [v for (b, y, p, tt), v in mv.items() if tt == t]
        for i in range(len(all_moves)):
            for j in range(i + 1, len(all_moves)):
                res.append([-all_moves[i], -all_moves[j]])
    return res

ordem = {}   # (k, i, t) -> variavel auxiliar "phi_i do par k vale em t"

def literais_phi(phi, t):
    """Literais (em conjuncao) da condicao phi no instante t.
    bloco -> p       : so at(b,p,t)               (ex.: {'d': 2} = at(d,2,t))
    bloco -> (p, l)  : at(b,p,t) ^ lev(b,l,t)     (ex.: {'d': (2, 0)})"""
    lits = []
    for b, pos in phi.items():
        if isinstance(pos, tuple):
            p, l = pos
            lits += [at[(b, p, t)], lev[(b, l, t)]]
        else:
            lits.append(at[(b, pos, t)])
    return lits

def clausulas_ordem_parcial():         # Ordem Parcial (Item 4)
    """phi1 -<P phi2:  para todo t,  NOT phi2(t) v phi1(0) v ... v phi1(t).
    Se phi e um unico literal (ex.: at(d,2,t)), ele entra direto na clausula,
    exatamente como na formalizacao. Se phi e uma conjuncao (varios at/lev),
    criamos uma variavel auxiliar h(t) <-> phi(t) para cada instante."""
    res = []
    for k, (nome, phi1, phi2) in enumerate(PARTIAL_ORDERS):
        for i, phi in ((1, phi1), (2, phi2)):
            for t in range(HORIZON + 1):
                lits = literais_phi(phi, t)
                if len(lits) == 1:
                    ordem[(k, i, t)] = lits[0]           # literal direto
                    continue
                h = new_var()
                ordem[(k, i, t)] = h
                for x in lits:
                    res.append([-h, x])                  # h -> cada literal
                res.append([h] + [-x for x in lits])     # todos -> h
        for t in range(HORIZON + 1):
            res.append([-ordem[(k, 2, t)]] +
                       [ordem[(k, 1, tp)] for tp in range(t + 1)])
    return res

# Adiciona todos os ganchos a lista global de clausulas
for gancho in (clausulas_exclusao_horizontal, clausulas_estabilidade,
               clausulas_clear, clausulas_precondicoes_move,
               clausulas_acao_unica, clausulas_ordem_parcial):
    clauses.extend(gancho())

NUM_VARS = next_id   # depois dos ganchos: a ordem parcial cria variaveis auxiliares

# Escrita do CNF (DIMACS) e do mapa
os.makedirs(OUT_DIR, exist_ok=True)
CNF_PATH = os.path.join(OUT_DIR, 'trab01_blocos2SAT.cnf')
MAP_PATH = os.path.join(OUT_DIR, 'trab01_blocos2SAT.map')

with open(CNF_PATH, 'w') as f:
    f.write(f"p cnf {NUM_VARS} {len(clauses)}\n")
    for c in clauses:
        f.write(" ".join(str(l) for l in c) + " 0\n")

with open(MAP_PATH, 'w') as f:
    for (b, p, t), v in at.items():
        f.write(f"{v} at({b},{p},{t})\n")
    for (b, l, t), v in lev.items():
        f.write(f"{v} lev({b},{l},{t})\n")
    for (b, t), v in clr.items():
        f.write(f"{v} clr({b},{t})\n")
    for (b, y, p, t), v in mv.items():
        f.write(f"{v} move({b},{y},{p},{t})\n")
    for (k, i, t), v in ordem.items():
        if v > len(at) + len(lev) + len(clr) + len(mv):   # so as auxiliares
            f.write(f"{v} ordem(par={k},phi{i},{t})\n")

n = args.cenario.split('-')[0]
print(f"{CEN['descricao']}  (HORIZON = {HORIZON})")
print(f"Gerado: {NUM_VARS} variaveis, {len(clauses)} clausulas")
print(f"Arquivos: {CNF_PATH}, {MAP_PATH}")
print(f"Proximo passo: minisat {CNF_PATH} {os.path.join(OUT_DIR, f'resultado{n}.txt')}")
