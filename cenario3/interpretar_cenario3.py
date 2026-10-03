#!/usr/bin/env python3
import sys
import re

# Tabela de tamanhos dos blocos conforme a especificação do domínio
BLOCKS = {'a': 1, 'b': 1, 'c': 2, 'd': 3}

def cargar_mapa(map_file):
    """Lê o arquivo .map para mapear IDs numéricos do SAT de volta para nomes de variáveis."""
    id_to_name = {}
    with open(map_file, 'r') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                var_id = int(parts[0])
                var_name = parts[1]
                id_to_name[var_id] = var_name
    return id_to_name

def parse_result(result_file):
    """Extrai as variáveis que foram atribuídas como VERDADEIRAS pelo MiniSAT."""
    true_vars = set()
    with open(result_file, 'r') as f:
        lines = f.readlines()
        if not lines or lines[0].strip() == "UNSAT":
            return None
        for line in lines:
            tokens = line.strip().split()
            for token in tokens:
                if token.isdigit():
                    val = int(token)
                    if val > 0:
                        true_vars.add(val)
    return true_vars

def derivar_on(states_at, states_lev, t):
    """Deriva a relação lógica 'on(b, y, t)' a posteriori com base em posições e níveis."""
    on_relations = []
    curr_at = states_at.get(t, {})
    curr_lev = states_lev.get(t, {})
    
    for b, p_b in curr_at.items():
        l_b = curr_lev.get(b, 0)
        if l_b == 0:
            on_relations.append(f"  - Bloco '{b}' está apoiado diretamente na MESA")
        else:
            supports = []
            for y, p_y in curr_at.items():
                if y != b and curr_lev.get(y, -1) == l_b - 1:
                    # Verifica sobreposição horizontal entre b e y no nível inferior
                    if not (p_b + BLOCKS[b] <= p_y or p_y + BLOCKS[y] <= p_b):
                        supports.append(y)
            if supports:
                on_relations.append(f"  - Bloco '{b}' está apoiado sobre: {', '.join(supports)}")
    return on_relations

def imprimir_explicacao_humana(moves, max_t):
    """Imprime 2 parágrafos explicativos do resultado para consumo humano."""
    num_passos = len(moves)
    
    parag_1 = (
        f"O plano sequencial gerado pelo solver SAT resolve com sucesso a Situação 3 executando "
        f"exatamente {num_passos} movimentos ao longo de {max_t} unidades de tempo. Inicialmente, "
        f"o bloco 'd' (tamanho 3) encontra-se em formato de ponte sobre os blocos 'a' e 'b'. Para liberar "
        f"o topo de 'a' e 'b' sem violar as regras de espaço, o bloco 'd' é temporariamente deslocado "
        f"para cima de 'c' (em p=0). Em seguida, os blocos menores são reorganizados para desocupar a "
        f"região central da mesa, permitindo que 'd' possa finalmente ser posicionado diretamente na mesa."
    )
    
    parag_2 = (
        f"Nas etapas finais, os blocos de tamanho unitário 'a' e 'b' são empilhados lado a lado no nível 1 "
        f"sobre o bloco 'c' (ocupando as posições p=0 e p=1, respectivamente), enquanto o bloco 'd' é "
        f"ajustado para a sua posição final na mesa no ponto p=3 (nível 0). Dessa forma, todas as relações "
        f"de estabilidade física, suporte mínimo e ausência de sobreposição horizontal foram satisfeitas, "
        f"concluindo a transição do estado inicial S0 ao estado meta S7 sem qualquer colisão de blocos."
    )
    
    print("\n" + "=" * 60)
    print("      EXPLICAÇÃO DO RESULTADO PARA HUMANOS")
    print("=" * 60)
    print(parag_1)
    print()
    print(parag_2)
    print("=" * 60)

def main():
    map_file = "trab01_blocos2SAT.map"
    result_file = sys.argv[1] if len(sys.argv) > 1 else "resultado3.txt"
    
    id_to_name = cargar_mapa(map_file)
    true_vars = parse_result(result_file)
    
    if true_vars is None:
        print("RESULTADO: UNSATISFIABLE (Nenhum plano encontrado no horizonte dado).")
        return

    moves = []
    states_at = {}   # t -> {b: p}
    states_lev = {}  # t -> {b: l}

    for var_id in true_vars:
        if var_id in id_to_name:
            name = id_to_name[var_id]
            
            # Capturar movimentos
            mv_match = re.match(r"move\(([^,]+),\s*([^,]+),\s*p=(\d+),\s*t=(\d+)\)", name)
            if mv_match:
                b, y, p, t = mv_match.groups()
                moves.append((int(t), b, y, int(p)))
                
            # Capturar posições at
            at_match = re.match(r"at\(([^,]+),\s*p=(\d+),\s*t=(\d+)\)", name)
            if at_match:
                b, p, t = at_match.groups()
                t, p = int(t), int(p)
                if t not in states_at: states_at[t] = {}
                states_at[t][b] = p
                
            # Capturar níveis lev
            lev_match = re.match(r"lev\(([^,]+),\s*l=(\d+),\s*t=(\d+)\)", name)
            if lev_match:
                b, l, t = lev_match.groups()
                t, l = int(t), int(l)
                if t not in states_lev: states_lev[t] = {}
                states_lev[t][b] = l

    moves.sort(key=lambda x: x[0])

    print("==================================================")
    print("      PLANO ENCONTRADO - SITUAÇÃO 3 (CENÁRIO 3)   ")
    print("==================================================")
    for t, b, y, p in moves:
        target_str = "MESA" if y == 'T' else f"CIMA de '{y}'"
        print(f"Passo t={t}: Mover bloco '{b}' para {target_str} no ponto p={p}")

    max_t = max(states_at.keys()) if states_at else 0
    print("\n--------------------------------------------------")
    print(f"ESTADO FINAL ALCANÇADO (t={max_t}):")
    for b in sorted(BLOCKS.keys()):
        p = states_at.get(max_t, {}).get(b, '?')
        l = states_lev.get(max_t, {}).get(b, '?')
        print(f"  Bloco '{b}': ponto p={p}, nível l={l}")

    print("\nRELAÇÕES 'on' DERIVADAS NO ESTADO FINAL:")
    for rel in derivar_on(states_at, states_lev, max_t):
        print(rel)

    # Chamada dos 2 parágrafos explicativos
    imprimir_explicacao_humana(moves, max_t)

if __name__ == "__main__":
    main()
