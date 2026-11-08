"""Regras de estoque independentes da interface gráfica."""

from dataclasses import dataclass, replace
from uuid import uuid4


class ErroEstoque(ValueError):
    """Uma operação foi rejeitada pelas regras do estoque."""


@dataclass(frozen=True)
class SituacaoEstoque:
    produto: str
    total: int
    reservado: int = 0
    bloqueado: int = 0

    @property
    def disponivel(self) -> int:
        return self.total - self.reservado - self.bloqueado


@dataclass(frozen=True)
class Registro:
    id: str
    produto: str
    tipo: str
    quantidade: int
    referencia: str
    ativo: bool = True


class ControleEstoque:
    def __init__(self) -> None:
        self._totais: dict[str, int] = {}
        self._registros: dict[str, Registro] = {}

    @staticmethod
    def _normalizar_produto(produto: str) -> str:
        if not isinstance(produto, str) or not produto.strip():
            raise ErroEstoque("Informe um código de produto não vazio.")
        return produto.strip().upper()

    @staticmethod
    def _validar_quantidade(quantidade: int) -> None:
        # bool é uma subclasse de int, mas não representa unidades de estoque.
        if type(quantidade) is not int or quantidade <= 0:
            raise ErroEstoque("A quantidade deve ser um número inteiro maior que zero.")

    def entrada(self, produto: str, quantidade: int) -> None:
        codigo = self._normalizar_produto(produto)
        self._validar_quantidade(quantidade)
        novo_total = self._totais.get(codigo, 0) + quantidade
        self._totais[codigo] = novo_total

    def consultar_produto(self, produto: str) -> SituacaoEstoque:
        codigo = self._normalizar_produto(produto)
        if codigo not in self._totais:
            raise ErroEstoque(f"Produto não encontrado: {codigo}.")
        ativos = [r for r in self._registros.values() if r.produto == codigo and r.ativo]
        return SituacaoEstoque(
            produto=codigo,
            total=self._totais[codigo],
            reservado=sum(r.quantidade for r in ativos if r.tipo == "reserva"),
            bloqueado=sum(r.quantidade for r in ativos if r.tipo == "bloqueio"),
        )

    def listar_produtos(self) -> tuple[str, ...]:
        return tuple(sorted(self._totais))

    def listar_registros(self, produto: str) -> tuple[Registro, ...]:
        saldo = self.consultar_produto(produto)
        return tuple(r for r in self._registros.values() if r.produto == saldo.produto)

    def _validar_disponibilidade(self, produto: str, quantidade: int) -> SituacaoEstoque:
        self._validar_quantidade(quantidade)
        saldo = self.consultar_produto(produto)
        if quantidade > saldo.disponivel:
            raise ErroEstoque(
                f"Saldo insuficiente: disponível {saldo.disponivel}, solicitado {quantidade}."
            )
        return saldo

    def saida(self, produto: str, quantidade: int, referencia: str = "") -> Registro:
        saldo = self._validar_disponibilidade(produto, quantidade)
        if not isinstance(referencia, str):
            raise ErroEstoque("A referência deve ser um texto.")
        referencia = referencia.strip()
        identificador = f"SAI-{uuid4()}"
        while identificador in self._registros:
            identificador = f"SAI-{uuid4()}"
        registro = Registro(identificador, saldo.produto, "saida", quantidade, referencia, False)
        # Preparar as duas estruturas antes de publicar a alteração.
        totais = {**self._totais, saldo.produto: saldo.total - quantidade}
        registros = {**self._registros, identificador: registro}
        self._totais, self._registros = totais, registros
        return registro

    def reservar(self, produto: str, quantidade: int, referencia: str) -> Registro:
        return self._criar_registro(produto, quantidade, referencia, "reserva")

    def bloquear(self, produto: str, quantidade: int, referencia: str = "") -> Registro:
        return self._criar_registro(produto, quantidade, referencia, "bloqueio")

    def _criar_registro(
        self, produto: str, quantidade: int, referencia: str, tipo: str
    ) -> Registro:
        saldo = self._validar_disponibilidade(produto, quantidade)
        if not isinstance(referencia, str):
            raise ErroEstoque("A referência deve ser um texto.")
        referencia = referencia.strip()
        if tipo == "reserva" and not referencia:
            raise ErroEstoque("Informe a solicitação ou pedido da reserva.")
        prefixo = "RES" if tipo == "reserva" else "BLQ"
        identificador = f"{prefixo}-{uuid4()}"
        while identificador in self._registros:
            identificador = f"{prefixo}-{uuid4()}"
        registro = Registro(identificador, saldo.produto, tipo, quantidade, referencia)
        self._registros[identificador] = registro
        return registro

    def consultar_registro(self, identificador: str) -> Registro:
        if not isinstance(identificador, str) or not identificador.strip():
            raise ErroEstoque("Informe um ID não vazio.")
        identificador = identificador.strip()
        if identificador not in self._registros:
            raise ErroEstoque(f"Registro não encontrado: {identificador}.")
        return self._registros[identificador]

    def liberar(self, identificador: str) -> Registro:
        registro = self.consultar_registro(identificador)
        if registro.tipo == "saida":
            raise ErroEstoque("Saídas não podem ser liberadas. Estorno não está implementado.")
        if not registro.ativo:
            raise ErroEstoque(f"Registro já liberado: {registro.id}.")
        liberado = replace(registro, ativo=False)
        self._registros[registro.id] = liberado
        return liberado
