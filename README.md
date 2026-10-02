# Trabalho 1: Mundo dos Blocos de Tamanho Variável via SAT Solver

**Disciplina:** Fundamentos de Inteligência Artificial  
**Professor:** Edjard Mota  
**Repositório Oficial:** TrabalhoIA_MundoBloclos_equipe_X  

## Registo Académico
* Adrya Vieira
* Hagata Rodrigues
* Luís Abdalla
* Maria Penha
* Miguel Bezerra
* Rafaelly Dos Anjos

---

## 1. Explicação da Solução
Este projeto resolve o problema de planeamento do Mundo dos Blocos adaptado para dimensões variáveis. A solução foi inicialmente modelada em Lógica de Primeira Ordem (LPO) — definindo predicados como `at`, `lev`, `clr` e a relação derivada `on` — e, em seguida, traduzida para Lógica Proposicional (CNF). 

Para encontrar os planos ótimos (Situações 1, 2 e 3), implementámos regras físicas rigorosas no código Python, tais como exclusão horizontal, estabilidade (blocos maiores requerem apoio estrutural proporcional) e a restrição de uma única ação `move` por instante. O modelo gerado é então resolvido utilizando um SAT Solver booleano.

---

## 2. Pré-requisitos e Instalação
* **Python 3:** Necessário para correr os scripts geradores e interpretadores.
* **miniSAT (SAT Solver):** Utilizado para processar as cláusulas CNF.
  * Para instalar em distribuições Linux (ou WSL no Windows), utilize o comando:
    ```bash
    sudo apt install minisat
    ```

---

## 3. Instruções de Execução (Passo a Passo)

**Passo 1: Gerar a Codificação CNF**
Compile o script principal parametrizado para o cenário desejado. Este comando gera automaticamente os ficheiros `trab01_blocos2SAT.cnf` e `trab01_blocos2SAT.map`.
```bash
python3 bw2cnf_var.py

```

**Passo 2: Executar o SAT Solver**
Submeta o ficheiro CNF gerado ao miniSAT para encontrar a solução (exemplo para a Situação 1).

```bash
minisat trab01_blocos2SAT.cnf resultado1.txt

```

**Passo 3: Interpretar a Saída**
Traduza a saída numérica devolvida pelo miniSAT de volta para um plano de ações legível em português.

```bash
python3 interpretar.py resultado1.txt -verbose

```

---

## 4. Mapa de Artefactos Entregues

Para efeitos de avaliação, este repositório contém todos os ficheiros exigidos:

* `README.md`: Explicação da solução e guia de execução (este documento).
* **Scripts Python:** `bw2cnf_var.py` (código integrado com as regras do domínio) e `interpretar.py`.
* **Ficheiros SAT:** `trab01_blocos2SAT.cnf` (cláusulas) e `trab01_blocos2SAT.map` (mapeamento de variáveis).
* **Resultados das Execuções:** `resultado1.txt`, `resultado2.txt` e `resultado3.txt` correspondentes aos cenários testados.
* **Documentação Teórica:** Ficheiro fonte `.tex` e o PDF final gerado via Overleaf, detalhando o mapeamento formal e a codificação.

```

Substitua os dados de identificação e faça o *commit* para o GitHub. A sua secção de infraestrutura e registo documental ficará totalmente alinhada com as exigências de entrega do professor.

```
