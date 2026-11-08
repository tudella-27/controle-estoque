# Controle de estoque

Case em Python com interface Streamlit para registrar entradas, saídas, reservas por pedido, bloqueios e liberações individuais. Permite consultar total, disponível, reservado e bloqueado por produto e uma visão geral. O escopo é uma demonstração local, com dados temporários por sessão.

## Execução local

Pré-requisitos: Git e Python 3.14 (validado com 3.14.10 no Windows). Outras versões de Python não foram certificadas nesta revisão. No PowerShell:

```powershell
git clone https://github.com/tudella-27/controle-estoque.git
cd controle-estoque
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço local informado pelo Streamlit (normalmente http://localhost:8501). Execute os comandos na raiz do projeto. Encerre com Ctrl+C. Não é necessário ativar a venv nem alterar a ExecutionPolicy. Se `py` não for reconhecido após instalar Python, reabra o terminal/VS Code.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

A suíte contém 20 testes: 18 de domínio e dois de integração dos formulários com Streamlit AppTest. Foram executados e aprovados no Windows/Python 3.14.10 em 08/11/2026. Cobrem múltiplos pedidos e bloqueios, liberação individual, saldo exato, excesso de quantidade, tipos inválidos, referências, IDs, isolamento entre produtos, preservação do estado em erros e filtros da interface. Os testes usam instâncias novas e não dependem de uma ordem de execução.

O AppTest executa a interface sem navegador: não comprova aparência, rolagem, acessibilidade ou concorrência. Avisos `missing ScriptRunContext` podem aparecer no modo de teste; confira o resultado final `OK`. Não há medição de cobertura percentual nem teste de carga.

Na revisão com uma venv nova, a instalação foi concluída e `pip check` não encontrou incompatibilidades. A primeira suíte teve um timeout de 15 segundos ao iniciar o AppTest; a segunda passou os 20 testes sem mudança de código ou timeout. A causa da lentidão inicial não foi determinada. Se ocorrer, preserve a saída e repita para diagnóstico; falhas recorrentes precisam ser investigadas, não ignoradas.

## Arquitetura e estrutura

- [estoque.py](estoque.py): regras, validações, saldos e registros; sem dependência de Streamlit.
- [app.py](app.py): formulários, mensagens, filtros e objeto de estoque em `st.session_state`.
- [estilo.css](estilo.css) e [configuração do tema](.streamlit/config.toml): apresentação.
- [tests](tests/): testes com unittest e AppTest.
- [requirements.txt](requirements.txt): dependências da aplicação.
- [Registro de IA](docs/uso_ia.md) e [visão de engenharia](docs/visao_engenharia.md): entregáveis de documentação dos itens 7.4 e 7.5 do case.

O domínio armazena totais por código e registros por UUID em dicionários. `Registro` e `SituacaoEstoque` são dataclasses imutáveis. A interface chama o domínio e apresenta `ErroEstoque` junto da operação. Erros inesperados não são mascarados como sucesso.

## Decisões técnicas e premissas

- Python permite expressar as regras com pouca infraestrutura; Streamlit oferece formulários locais sem uma API ou frontend separado. unittest evita outra dependência de testes.
- Memória por sessão reduz o escopo operacional. Não há banco nem compartilhamento entre usuários. Persistência não é obrigatória no enunciado.
- A primeira entrada válida cria o produto. Seu identificador textual é normalizado com remoção de espaços nas extremidades e conversão para maiúsculas. Não há nome descritivo separado.
- Quantidades devem ter tipo `int` exato e ser positivas: booleanos, textos, frações e `2.0` são rejeitados pelo domínio.
- `total = disponível + reservado + bloqueado`. Reservado e bloqueado são somas dos registros ativos; disponível é calculado. Entrada aumenta total; saída reduz total; reserva/bloqueio apenas retiram disponibilidade.
- Reserva exige pedido/solicitação textual. Bloqueio e saída aceitam referência textual opcional. O mesmo pedido pode ter reservas distintas, cada uma com ID próprio.
- A consulta aceita o ID completo de reservas (`RES-`), bloqueios (`BLQ-`) e saídas (`SAI-`). A liberação aceita apenas reservas e bloqueios ativos, é integral e individual e mantém o registro como inativo. Uma segunda tentativa de liberação é rejeitada.
- Saídas têm histórico consultável, mas não podem ser liberadas. Para retirar unidades reservadas, seria necessário liberá-las e efetuar uma saída; não há operação atômica de atendimento de pedido.
- As validações ocorrem antes das alterações. Isso preserva o estado nas rejeições previstas, em execução sequencial. Não equivale a uma transação de banco nem a proteção contra concorrência.

## Limitações conhecidas

Dados desaparecem ao encerrar a aplicação e podem se perder ao recarregar a página/perder a sessão. Cada sessão mantém seu próprio estoque. Não há autenticação, armazenamento durável, estorno, liberação parcial, idempotência ou histórico de entradas. O histórico disponível é de saídas, reservas e bloqueios, sem data/hora.

Consultas percorrem os registros e a visão geral repete consultas por produto; o histórico cresce durante a sessão. É adequado ao pequeno volume demonstrativo, sem validação de escala. Duas chamadas concorrentes sobre a mesma instância não têm sincronização.

As tabelas usam `st.dataframe`. Foi relatado um problema visual no qual a caixa de detalhe de uma célula fica deslocada após duplo clique e rolagem. A substituição por tabelas estáticas foi proposta, mas não aplicada. O problema permanece pendente de investigação; não foi constatada alteração dos dados relacionada a esse comportamento. Os testes com AppTest não reproduzem essa interação no navegador.

Dependências diretas observadas na revisão: Streamlit 1.67.0, pandas 3.1.1 e Jinja2 3.1.6. O intervalo de pandas e dependências transitivas não constitui um ambiente totalmente travado.

## Evolução para produção

Usaria banco relacional para produtos e movimentações, com restrições de integridade e transações. A verificação do disponível e a alteração seriam feitas juntas, com bloqueio por produto ou controle de versão para evitar duas reservas das mesmas unidades. Acrescentaria idempotência para requisições repetidas, autenticação/autorização, auditoria com horários, logs, monitoramento, backup e recuperação testada.

Separaria o serviço de estoque da interface se houvesse outros consumidores. Criaria índices e avaliaria consultas com volume real antes de otimizar. Adicionaria testes de concorrência, persistência, falhas, navegador e acessibilidade, além de integração contínua e versões reproduzíveis das dependências. A ordem dessas evoluções dependeria dos riscos e requisitos reais.
