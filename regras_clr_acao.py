import itertools

# --- REGRA DA FUNÇÃO 6: Ação única por passo ---
# Garante que, num dado instante t, apenas uma ação 'mv' pode ser verdadeira.
for t in range(HORIZON):
    acoes_no_instante = []
    
    # 1. Recolher as variáveis numéricas de todas as ações possíveis no instante t
    for b in BLOCKS:
        destinos = list(BLOCKS.keys()) + ['T'] # Pode mover para outro bloco ou Mesa ('T')
        for y in destinos:
            if b != y: # Não pode mover para cima de si mesmo
                for p in valid_positions(BLOCKS[b]):
                    acoes_no_instante.append(mv[(b, y, p, t)])
    
    # 2. Gerar todos os pares possíveis e proibir que aconteçam ao mesmo tempo
    for acao1, acao2 in itertools.combinations(acoes_no_instante, 2):
        add_clause([-acao1, -acao2])


    # --- REGRA DA FUNÇÃO 6: Bloco #3.3 (E) - Definição de clr ---
for t in range(HORIZON + 1):
    for b in BLOCKS:
        blocos_acima = [] # Lista para guardar as condições de bloqueio
        
        for b_linha in BLOCKS:
            if b != b_linha:
                for p_b in valid_positions(BLOCKS[b]):
                    for p_blinha in valid_positions(BLOCKS[b_linha]):
                        
                        # Verifica se os spans se sobrepõem no eixo horizontal
                        if spans_overlap(b, p_b, b_linha, p_blinha):
                            for l in range(MAX_LEVEL):
                                # Condição: b_linha está no nível l+1 (acima) e b está no nível l
                                if (b_linha, l+1, t) in lev and (b, l, t) in lev:
                                    bloqueio = and_vars([at[(b_linha, p_blinha, t)], lev[(b_linha, l+1, t)], at[(b, p_b, t)], lev[(b, l, t)]])
                                    blocos_acima.append(bloqueio)
        
        # Aplicação das cláusulas lógicas
        if blocos_acima:
            condicao_bloqueado = or_vars(blocos_acima)
            # Se a condição de bloqueio for verdadeira, então clr é falso
            add_clause([-condicao_bloqueado, -clr[(b, t)]]) 
            # Se a condição de bloqueio for falsa, então clr é verdadeiro
            add_clause([condicao_bloqueado, clr[(b, t)]])   
        else:
            # Se for fisicamente impossível ter algo acima, o topo está sempre livre
            add_clause([clr[(b, t)]])    