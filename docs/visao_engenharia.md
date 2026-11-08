# Visão de engenharia

Para este projeto, considero importantes os cinco pontos abaixo. Eles ajudam a manter o estoque correto, facilitar a manutenção e entender o que precisaria mudar se a solução fosse usada em um ambiente real.

1. **Manter os saldos corretos:** o sistema precisa mostrar com clareza o que está disponível, reservado e bloqueado. Por isso, considero essencial conferir as condições de uma operação antes de alterar o estoque. Se uma saída for maior que o disponível, por exemplo, ela deve ser recusada sem mudar os saldos nem os registros.

2. **Testar também o que pode dar errado:** conferir apenas se uma entrada ou reserva funciona não é suficiente. É importante testar saldo insuficiente, quantidade inválida e tentativa de liberar a mesma reserva duas vezes. Esses testes ajudam a perceber se uma mudança no código prejudicou algo que já funcionava e dão mais segurança para continuar o desenvolvimento.

3. **Deixar o código fácil de entender:** separar as regras de estoque da interface facilita encontrar onde cada comportamento foi definido. Assim, posso ajustar uma regra sem precisar mexer na apresentação e testar essa regra separadamente. Também considero importante usar nomes claros, para que outra pessoa consiga acompanhar o funcionamento do projeto.

4. **Facilitar a execução do projeto:** quem recebe o código precisa conseguir instalar as dependências, abrir a aplicação e rodar os testes seguindo o README. Para o tamanho deste case, uma estrutura simples e o uso de memória atendem à demonstração. Ao mesmo tempo, essa escolha precisa ficar clara, porque os dados não são mantidos quando a aplicação é encerrada.

5. **Preparar a solução para crescer conforme a necessidade:** em um uso real, eu priorizaria salvar os dados em um banco e garantir que duas pessoas não consigam reservar as mesmas últimas unidades. Também seria importante registrar quem fez cada movimentação. Se o volume aumentasse, avaliaria o tempo das consultas antes de decidir o que otimizar, para resolver os problemas observados sem complicar o projeto antes da hora.
