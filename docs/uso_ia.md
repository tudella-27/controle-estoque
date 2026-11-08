# Uso de IA

A IA apoiou o planejamento, a modelagem, a implementação, os testes e a documentação do case. As interações abaixo são resumos dos pedidos registrados durante o desenvolvimento, não transcrições literais.

## Principais interações

| Etapa | Pedido resumido | Contribuição para o projeto |
|---|---|---|
| Planejamento | Ler o PDF, mapear requisitos e entregáveis e orientar a preparação do ambiente. | Organização do escopo e proposta de Python, armazenamento em memória e testes com unittest. |
| Modelagem | Definir saldos, identificação de reservas e bloqueios, liberação e validações antes de implementar. | Regras separadas da interface, IDs individuais, liberação integral e validações antes de alterar o estado. |
| Implementação e testes | Implementar as operações e verificar múltiplos registros, limites de saldo e preservação do estado em erros. | Registros imutáveis, saldos calculados sobre reservas e bloqueios ativos e testes dos principais fluxos e rejeições. |
| Interface | Apresentar todos os produtos, identificar saídas e permitir consulta e filtros por tipo de operação. | Visão geral dos saldos, IDs de saída e filtros de produto e operação na interface Streamlit. |
| Revisão final | Comparar os arquivos reais com o PDF, executar testes e revisar os entregáveis. | Conferência dos requisitos, execução local da suíte e organização da documentação técnica. |

## Onde a IA ajudou

As contribuições se concentraram em transformar os requisitos em regras explícitas e cenários de teste, implementar a interface e organizar a documentação. Na modelagem, o apoio incluiu a distinção entre total, disponível, reservado e bloqueado, além do tratamento individual de múltiplas reservas e bloqueios.

Nos testes, a IA ajudou a cobrir situações que exigem atenção além do fluxo válido: saldo insuficiente, quantidades inválidas, referência obrigatória, ID inexistente e tentativa de liberar novamente um registro.

## Exemplos de decisões e verificação

Os exemplos a seguir detalham os resumos acima; não são prompts literais nem registram uma conversa completa.

- **Saldos e registros:** o pedido resumido foi modelar total, disponível, reservas e bloqueios com liberações individuais. A solução adotou registros identificados e calculou reservado e bloqueado a partir dos ativos; o disponível resulta do total menos essas somas. A verificação está nos testes de operações, que conferem os saldos e liberações individuais.
- **Operações inválidas:** o pedido resumido foi verificar limites e preservação do estado. A solução valida as condições antes de alterar os dados; os testes comparam saldos e registros antes e depois de rejeições. Essa verificação cobre a execução sequencial em memória, não concorrência ou transações de banco.
- **Interface:** foi solicitada uma visão dos produtos, consulta por ID e filtros. A implementação usa formulários Streamlit e mantém as regras no domínio. Os testes de interface exercitam os formulários e conferem os dados apresentados; eles não substituem uma verificação visual em navegador.

## Sugestão modificada

A proposta inicial incluía uma interface por terminal. Conforme registrado durante o planejamento, o candidato preferiu uma apresentação visual simples e adotou Streamlit. A mudança manteve as regras separadas da interface, o armazenamento em memória por sessão e os testes com unittest.

O motivo registrado foi facilitar a apresentação visual da solução dentro do escopo e do prazo disponíveis.

## Verificação das sugestões


Na revisão de 08/11/2026, o agente executou os 20 testes no Windows com Python 3.14.10, com aprovação. Em uma cópia com ambiente novo, a primeira execução apresentou timeout na inicialização do AppTest; a repetição aprovou os 20 testes sem alteração de código ou do limite de tempo. A causa da demora inicial não foi determinada.

O AppTest verifica a integração dos formulários, mas não comprova a aparência ou as interações em um navegador real.
