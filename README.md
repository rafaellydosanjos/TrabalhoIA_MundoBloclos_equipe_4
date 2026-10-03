# Trabalho 1: Mundo dos Blocos de Tamanho Variável via SAT Solver

**Disciplina:** Fundamentos de Inteligência Artificial  
**Professor:** Edjard Mota  
**Repositório Oficial:** TrabalhoIA_MundoBloclos_equipe_4

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

**Passo 1: Gerar a Codificação CNF**
Execute o script principal informando o cenário desejado. O programa é parametrizado para gerar a codificação CNF correspondente às três situações do trabalho.

Para a **Situação 1**:

```bash
python3 bw2cnf_var.py 1

```
Para a **Situação 2**:

```bash
python3 bw2cnf_var.py 2

```
Para a **Situação 3**:

```bash
python3 bw2cnf_var.py 3

```


**Passo 2: Executar o SAT Solver**
Submeta o ficheiro CNF gerado ao miniSAT para encontrar a solução.

Para a **Situação 1**:

```bash
minisat cenario1/trab01_blocos2SAT.cnf cenario1/resultado1.txt

```

Para a **Situação 2**:

```bash
minisat cenario2/trab01_blocos2SAT.cnf cenario2/resultado2.txt
```

Para a **Situação 3**:

```bash
minisat cenario3/trab01_blocos2SAT.cnf cenario3/resultado3.txt
```

### Por que essa alteração?

Porque o código atual não é mais executado simplesmente com:

```bash
python3 bw2cnf_var.py
```

### O código fará a seleção de cenário:
```bash
python3 bw2cnf_var.py 1  → Situação 1
python3 bw2cnf_var.py 2  → Situação 2
python3 bw2cnf_var.py 3  → Situação 3
```

**Passo 3: Interpretar a Saída**
Traduza a saída numérica devolvida pelo miniSAT de volta para um plano de ações legível em português.

```bash
python3 interpretar.py resultado1.txt -verbose

```

**Passo 4: Executar os Testes**
O ficheiro `testes_blocos.py` é utilizado como recurso auxiliar para testar a geração e a resolução dos cenários.

```bash
python3 testes_blocos.py
---
````

## 4. Mapa de Artefactos Entregues

Para efeitos de avaliação, este repositório contém todos os ficheiros exigidos:

* `README.md`: Explicação da solução e guia de execução (este documento).
* **Scripts Python:** `bw2cnf_var.py` (código integrado com as regras do domínio), `interpretar.py` e `testes_blocos.py` (script auxiliar para testes e validação dos cenários).
* **Ficheiros SAT:** `trab01_blocos2SAT.cnf` (cláusulas) e `trab01_blocos2SAT.map` (mapeamento de variáveis).
* **Resultados das Execuções:** `resultado1.txt`, `resultado2.txt` e `resultado3.txt` correspondentes aos cenários testados.
* **Documentação Teórica:** Ficheiro fonte `.tex` e o PDF final gerado via Overleaf, detalhando o mapeamento formal e a codificação.


### Organização dos Artefactos por Cenário

Os ficheiros gerados pelo programa estão organizados em pastas separadas para cada situação:

#### `cenario1/`

* `trab01_blocos2SAT.cnf`
* `trab01_blocos2SAT.map`
* `resultado1.txt`

#### `cenario2/`

* `trab01_blocos2SAT.cnf`
* `trab01_blocos2SAT.map`
* `resultado2.txt`

#### `cenario3/`

* `trab01_blocos2SAT.cnf`
* `trab01_blocos2SAT.map`
* `resultado3.txt`

```
>>>>>>> 98cd934012161eb976816d916f1acef2cade6381
