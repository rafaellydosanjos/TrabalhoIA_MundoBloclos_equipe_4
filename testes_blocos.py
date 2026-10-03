"""
Testes do codificador CNF do Mundo dos Blocos de Tamanho Variavel.

Uso:  python3 testes_blocos.py                  (acha o gerador bw2cnf*.py sozinho)
      python3 testes_blocos.py bw2cnf_var.py    (ou indica o arquivo)

Deixe este arquivo na MESMA PASTA do gerador (bw2cnf*.py). Pode ser
executado de qualquer pasta do terminal.

Requer um SAT solver:
  - pip install python-sat        (recomendado), ou
  - minisat instalado no PATH

O script troca INITIAL / GOAL / HORIZON no gerador, gera o CNF, resolve e:
  * Testes POSITIVOS: acha o T minimo e valida o plano com um SIMULADOR
    independente (que aplica as regras fisicas passo a passo).
  * Testes NEGATIVOS: situacoes fisicamente impossiveis devem dar UNSAT.
"""
import os, re, sys, subprocess, tempfile

MARCA = '# ---- fim da configuracao ----'
PASTA = os.path.dirname(os.path.abspath(__file__))

def achar_gerador():
    """Usa o arquivo passado na linha de comando; senao procura um bw2cnf*.py
    (versao com cenarios) na pasta deste script e na pasta atual."""
    if len(sys.argv) > 1:
        for cand in (sys.argv[1], os.path.join(PASTA, sys.argv[1])):
            if os.path.isfile(cand):
                return os.path.abspath(cand)
        raise SystemExit(f'ERRO: arquivo "{sys.argv[1]}" nao encontrado.')
    vistos = []
    for pasta in dict.fromkeys([PASTA, os.getcwd()]):
        for nome in sorted(os.listdir(pasta)):
            if nome.startswith('bw2cnf') and nome.endswith('.py'):
                cam = os.path.join(pasta, nome)
                vistos.append(cam)
                if MARCA in open(cam, encoding='utf-8', errors='ignore').read():
                    return cam
    msg = 'ERRO: nao achei o gerador (versao com cenarios) na pasta deste teste.'
    if vistos:
        msg += '\nArquivos bw2cnf*.py encontrados, mas de versao antiga:\n  ' + '\n  '.join(vistos)
    msg += '\nColoque testes_blocos.py na mesma pasta do gerador ou rode:\n  python3 testes_blocos.py CAMINHO/DO/GERADOR.py'
    raise SystemExit(msg)

GERADOR = achar_gerador()
BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}
MAX_POINT, MAX_LEVEL = 6, 3

# Estados (bloco -> (ponto inicial, nivel)), lidos das figuras do enunciado
SIT1_S0  = {'c': (0, 0), 'a': (3, 0), 'b': (5, 0), 'd': (3, 1)}
SIT1_SF1 = {'d': (3, 0), 'a': (4, 1), 'b': (5, 1), 'c': (4, 2)}
SIT1_SF2 = {'d': (3, 0), 'c': (4, 1), 'a': (4, 2), 'b': (5, 2)}
SIT1_SF3 = {'c': (0, 0), 'a': (2, 0), 'd': (0, 1), 'b': (5, 0)}
SIT1_SF4 = {'c': (0, 0), 'a': (0, 1), 'd': (2, 0), 'b': (5, 0)}

SIT2_S0  = {'c': (0, 0), 'd': (3, 0), 'a': (0, 1), 'b': (1, 1)}
SIT2_S5  = {'d': (3, 0), 'c': (4, 1), 'a': (4, 2), 'b': (5, 2)}

SIT3_S0  = SIT1_S0
SIT3_S7  = {'c': (0, 0), 'a': (0, 1), 'b': (1, 1), 'd': (3, 0)}

# ------------------------------------------------------------------
# Simulador independente (NAO usa o CNF) -- confere a fisica do plano
# ------------------------------------------------------------------
def slots(b, p):
    return set(range(p, p + BLOCKS[b]))

def valido(est):
    """Exclusao horizontal + estabilidade (>= ceil(l/2) slots apoiados)."""
    for b, (p, l) in est.items():
        if not (0 <= p <= MAX_POINT - BLOCKS[b]):
            return f'{b} fora da mesa'
        for y, (py, ly) in est.items():
            if y != b and ly == l and slots(b, p) & slots(y, py):
                return f'{b} e {y} sobrepostos no nivel {l}'
        if l > 0:
            apoio = set()
            for y, (py, ly) in est.items():
                if y != b and ly == l - 1:
                    apoio |= slots(b, p) & slots(y, py)
            if len(apoio) < (BLOCKS[b] + 1) // 2:
                return f'{b} instavel (apoio em {len(apoio)} slot(s))'
    return None

def livre(est, b):
    p, l = est[b]
    return not any(ly == l + 1 and slots(b, p) & slots(y, py)
                   for y, (py, ly) in est.items() if y != b)

def aplicar(est, b, y, p):
    if not livre(est, b):
        return None, f'{b} nao esta livre'
    if y == 'T':
        nl = 0
    else:
        py, ly = est[y]
        if not slots(b, p) & slots(y, py):
            return None, f'{b} em p={p} nao fica sobre {y}'
        nl = ly + 1
    if (p, nl) == est[b]:
        return None, 'movimento nulo'
    # nada pode estar no nivel-alvo OU acima, sobre os slots de destino
    for z, (pz, lz) in est.items():
        if z != b and lz >= nl and slots(b, p) & slots(z, pz):
            return None, f'destino bloqueado por {z} (nivel {lz})'
    novo = dict(est); novo[b] = (p, nl)
    erro = valido(novo)
    return (None, erro) if erro else (novo, None)

# ------------------------------------------------------------------
# Geracao + resolucao
# ------------------------------------------------------------------
def resolver(inicial, meta, H, ordens=()):
    src = open(GERADOR, encoding='utf-8').read()
    marca = MARCA
    sobrescreve = (f'INITIAL = {inicial!r}\nGOAL = {meta!r}\nHORIZON = {H}\n'
                   f'PARTIAL_ORDERS = {list(ordens)!r}\nOUT_DIR = "."\n')
    if marca not in src:
        raise SystemExit(f'ERRO: {GERADOR} e uma versao antiga do gerador (sem cenarios).')
    src = src.replace(marca, marca + '\n' + sobrescreve)
    d = tempfile.mkdtemp()
    open(os.path.join(d, 'g.py'), 'w', encoding='utf-8').write(src)
    r = subprocess.run([sys.executable, 'g.py', '1'], cwd=d, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'ERRO ao executar o gerador {os.path.basename(GERADOR)}:\n{r.stderr or r.stdout}')
    cnf = os.path.join(d, 'trab01_blocos2SAT.cnf')
    mapa = {}
    for linha in open(os.path.join(d, 'trab01_blocos2SAT.map')):
        i, s = linha.split(maxsplit=1)
        mapa[int(i)] = s.strip()
    modelo = _sat(cnf, d)
    if modelo is None:
        return None
    acoes = []
    for v in modelo:
        m = re.match(r'(?:move|mv)\((\w),(\w),(\d),(\d+)\)', mapa.get(v, ''))
        if m:
            acoes.append((int(m[4]), m[1], m[2], int(m[3])))
    return sorted(acoes)

def _escolher_solver():
    try:
        from pysat.solvers import Minisat22  # noqa: F401
        return 'pysat'
    except ImportError:
        pass
    import shutil
    if shutil.which('minisat'):
        return 'minisat'
    raise SystemExit('ERRO: nenhum SAT solver encontrado. Instale um deles:\n'
                     '  pip install python-sat        (ou: pip install python-sat --break-system-packages)\n'
                     '  sudo apt install minisat')

SOLVER = _escolher_solver()

def _sat(cnf, d):
    if SOLVER == 'pysat':
        from pysat.formula import CNF
        from pysat.solvers import Minisat22
        with Minisat22(bootstrap_with=CNF(from_file=cnf).clauses) as s:
            return [x for x in s.get_model() if x > 0] if s.solve() else None
    out = os.path.join(d, 'res.txt')
    subprocess.run(['minisat', cnf, out], capture_output=True)
    if not os.path.isfile(out):
        raise SystemExit('ERRO: o minisat nao gerou o arquivo de resultado.')
    linhas = open(out).read().split()
    return None if not linhas or linhas[0] != 'SAT' else [int(x) for x in linhas[1:] if int(x) > 0]

def t_minimo(inicial, meta, hmax, ordens=()):
    for H in range(hmax + 1):
        plano = resolver(inicial, meta, H, ordens)
        if plano is not None:
            return H, plano
    return None, None

# ------------------------------------------------------------------
# Execucao dos testes
# ------------------------------------------------------------------
ok = falhas = 0
def checa(nome, cond, detalhe=''):
    global ok, falhas
    print(f"  [{'OK ' if cond else 'FALHOU'}] {nome}" + (f'  -> {detalhe}' if detalhe and (not cond or 'T minimo' in detalhe) else ''))
    ok += cond; falhas += (not cond)

def vale(est, phi):
    return all(est[b] == pl if isinstance(pl, tuple) else est[b][0] == pl
               for b, pl in phi.items())

def teste_positivo(nome, inicial, meta, hmax, ordens=()):
    print(f'\n== {nome} ==')
    H, plano = t_minimo(inicial, meta, hmax, ordens)
    checa('encontra plano', H is not None, f'nenhum plano ate T={hmax}' if H is None else f'T minimo = {H}')
    if H is None:
        return
    est = dict(inicial)
    estados = [est]
    for t, b, y, p in plano:
        alvo = 'a MESA' if y == 'T' else f'CIMA de {y}'
        est, erro = aplicar(est, b, y, p)
        checa(f't={t}: mover {b} para {alvo} em p={p}', erro is None, erro or '')
        if erro:
            return
        estados.append(est)
    checa('estado final == meta', all(est[b] == meta[b] for b in meta))
    for nome_o, phi1, phi2 in ordens:
        t1 = next((i for i, e in enumerate(estados) if vale(e, phi1)), None)
        t2 = next((i for i, e in enumerate(estados) if vale(e, phi2)), None)
        checa(f'ordem parcial respeitada: {nome_o}',
              t2 is None or (t1 is not None and t1 <= t2), f'phi1 em t={t1}, phi2 em t={t2}')

def teste_negativo(nome, inicial, meta, H, ordens=()):
    checa(nome + f' (T={H})', resolver(inicial, meta, H, ordens) is None, 'deveria ser UNSAT')

print(f'Gerador testado: {GERADOR}')
print(f'SAT solver:      {SOLVER}')

# ---------- Positivos: cenarios do enunciado ----------
teste_positivo('Situacao 1: S0 -> Sf1', SIT1_S0, SIT1_SF1, 12)
teste_positivo('Situacao 1: S0 -> Sf2', SIT1_S0, SIT1_SF2, 12)
teste_positivo('Situacao 1: S0 -> Sf3', SIT1_S0, SIT1_SF3, 12)
teste_positivo('Situacao 1: S0 -> Sf4', SIT1_S0, SIT1_SF4, 12)
teste_positivo('Situacao 2: S0 -> S5',  SIT2_S0, SIT2_S5,  12)
teste_positivo('Situacao 3: S0 -> S7',  SIT3_S0, SIT3_S7,  12)

# ---------- Sanidade ----------
print('\n== Sanidade ==')
for nome, s in [('Sit1 S0', SIT1_S0), ('Sit2 S0', SIT2_S0), ('Sit2 S5', SIT2_S5), ('Sit3 S7', SIT3_S7)]:
    checa(f'{nome} e um estado valido (T=0, meta = proprio estado)', resolver(s, s, 0) == [])
checa('Ponte de S0 (d sobre a e b, slot 4 vazio) e aceita', resolver(SIT1_S0, SIT1_S0, 0) is not None)
checa('Lado a lado: b ao lado de a sobre c (Sf4 -> b em (1,1)) em 1 passo',
      resolver(SIT1_SF4, {'b': (1, 1)}, 1) is not None)

# ---------- Negativos: cada regra do dominio ----------
print('\n== Regras (devem dar UNSAT) ==')
teste_negativo('Estabilidade: d apoiado so em a',
               {'a': (3, 0), 'b': (0, 0), 'c': (1, 0), 'd': (3, 1)}, {}, 0)
teste_negativo('Estabilidade: c (l=2) com 0 slots de apoio',
               {'a': (0, 0), 'b': (1, 0), 'c': (3, 1), 'd': (0, 2)}, {}, 0)
teste_negativo('Exclusao horizontal: c e d no mesmo slot',
               {'a': (5, 0), 'b': (4, 0), 'c': (0, 0), 'd': (1, 0)}, {}, 0)
teste_negativo('Clear: mover a com d em cima (S0 -> a na mesa em p=1)',
               SIT1_S0, {'a': (1, 0)}, 1)
teste_negativo('Destino ocupado: colocar c sobre a enquanto d esta em a',
               SIT1_S0, {'c': (3, 1)}, 1)
teste_negativo('Sob balanco: enfiar a no slot 4 embaixo de d',
               {'a': (0, 0), 'b': (5, 0), 'c': (2, 0), 'd': (2, 1)}, {'a': (4, 0)}, 1)
teste_negativo('Slot ocupado no topo de c: b em p=0 onde ja esta a',
               SIT1_SF4, {'b': (0, 1)}, 1)
teste_negativo('Acao unica: Sf4 exige 4 passos, nao 3', SIT1_S0, SIT1_SF4, 3)
teste_negativo('Meta instavel: d sobre a apenas',
               SIT1_S0, {'d': (3, 1), 'b': (0, 0), 'c': (1, 0), 'a': (3, 0)}, 5)

# ---------- Ordem parcial ----------
PO_SF4 = [('d na mesa em p=2 antes de a sobre c', {'d': (2, 0)}, {'a': (0, 1)})]
PO_S5  = [('c sobre d antes de a sobre c', {'c': (4, 1)}, {'a': (4, 2)}),
          ('c sobre d antes de b sobre c', {'c': (4, 1)}, {'b': (5, 2)})]
PO_S7  = [('a sobre c antes de b sobre c', {'a': (0, 1)}, {'b': (1, 1)}),
          ('b sobre c antes de d na mesa em p=3', {'b': (1, 1)}, {'d': (3, 0)})]
PO_S7_INV = [('b sobre c (p=0) antes de a sobre c (p=1)', {'b': (0, 1)}, {'a': (1, 1)})]
teste_positivo('Ordem parcial: Sit1 S0 -> Sf4', SIT1_S0, SIT1_SF4, 12, PO_SF4)
teste_positivo('Ordem parcial (exemplo do Item 4): at(d,2) antes de at(a,0)', SIT1_S0, SIT1_SF4, 12,
               [('d na posicao 2 antes de a na posicao 0', {'d': 2}, {'a': 0})])
teste_positivo('Ordem parcial: Sit2 S0 -> S5',  SIT2_S0, SIT2_S5,  12, PO_S5)
teste_positivo('Ordem parcial: Sit3 S0 -> S7',  SIT3_S0, SIT3_S7,  12, PO_S7)
# meta alternativa (b a esquerda de a sobre c) exigindo b antes de a
teste_positivo('Ordem parcial: Sit3 S0 -> b,a sobre c (b primeiro)', SIT3_S0,
               {'c': (0, 0), 'b': (0, 1), 'a': (1, 1), 'd': (3, 0)}, 12, PO_S7_INV)
# ordem invertida em relacao ao plano otimo: ainda ha plano, mas mais longo
teste_positivo('Ordem parcial muda o plano: Sf4 com a sobre c ANTES de d na mesa', SIT1_S0,
               SIT1_SF4, 12, [('a sobre c antes de d na mesa em p=2', {'a': (0, 1)}, {'d': (2, 0)})])

print('\n== Ordem parcial (deve dar UNSAT) ==')
teste_negativo('Ordem contraditoria: X antes de Y e Y antes de X (metas distintas)',
               SIT3_S0, SIT3_S7, 8,
               [('a antes de b', {'a': (0, 1)}, {'b': (1, 1)}),
                ('b antes de a', {'b': (1, 1)}, {'a': (0, 1)})])

print(f'\nResultado: {ok} OK, {falhas} falha(s)')
sys.exit(1 if falhas else 0)
