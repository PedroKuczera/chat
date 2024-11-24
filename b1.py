import asyncio
import twitchio
import time
from twitchio.ext import eventsub, commands

# Configurações fáceis de editar
TOKEN_BOT = "oauth:hkyhe007cpac10u2dxzdimajyb4rko"  # Token da conta da twitch
USUARIO_ESPECIFICO = "marcosdias87"  # Nome de usuário que o bot vai procurar
RESPOSTA_BOT = "Bagre"  # Mensagem que o bot vai enviar
NUMERO_PARTICIPANTES = 1  # Número de participantes necessários para ativar o comando
TEMPO_AWAIT_RESPOSTA = 4  # Tempo de espera (em segundos) antes de enviar a resposta (configurável)
TEMPO_INTERVALO_COMANDO = 2400  # Tempo (em segundos) entre o envio dos comandos
TEMPO_AWAIT_COMANDO = 4  # Tempo de espera (em segundos) antes de enviar o comando (configurável)

# Lista de canais que o bot vai monitorar
canais_twitch = [
    "Bagrezada"
]

# Nome dos bots de sorteio
bots_twitch = ["nightbot", "moobot", "bagrezada"]

# Comandos válidos para o sorteio (facilmente editáveis)
comandos_validos = [
    "!sorteio", "!garuda", "!flame", "!mc", "!mp", "!pvp", "!mega", 
    "!bora", "!ruivo", "!duuh", "!kazar", "!anonimo", "!mestre", 
    "!atazotty", "!dugaras", "!titox", "!casalx", "!mpp"]  # Adicione/Remova os comandos aqui

class Bot(commands.Bot):
    def __init__(self):
        """
        Carregamento do token de acesso e parametrização do BOT
        """
        token = TOKEN_BOT
        super().__init__(token=token, prefix="!", initial_channels=canais_twitch)
        self.comandos_participantes_por_canal = {}  # Dicionário por canal para contar comandos
        self.comandos_enviados_por_canal = {}  # Lista para armazenar comandos enviados por canal
        self.last_command_time_por_canal = {}  # Dicionário para armazenar o tempo do último comando de cada canal
        self.usuarios_participantes = {}  # Dicionário para armazenar participantes únicos por canal
        self.intervalo_ativo_por_canal = {}  # Dicionário para controlar o estado de intervalo de cada canal

    async def event_ready(self):
        """
        Evento quando o bot é carregado
        """
        print(f"Login como | {self.nick}")
        print(f"User id é | {self.user_id}")
        self._setup_channels()

    def _setup_channels(self):
        """
        Configura os objetos dos canais e verifica se estão disponíveis
        """
        for channel_name in canais_twitch:
            channel = self.get_channel(channel_name)
            if channel:
                print(f"Canal {channel.name} encontrado")
            else:
                print(f"Canal {channel_name} não encontrado")

    async def event_message(self, message):
        """
        Evento ao digitar uma mensagem qualquer no chat
        """
        if message.echo:
            return

        print(f"Mensagem recebida: {message.content} de {message.author.name} no canal {message.channel.name}")

        # Verifica se o autor da mensagem é o usuário específico
        if message.author.name.lower() in [bot.lower() for bot in bots_twitch]:
        # Verifica se o nome do usuário específico aparece em qualquer parte da mensagem, independentemente do contexto
            if USUARIO_ESPECIFICO.lower() in message.content.lower():
                await asyncio.sleep(TEMPO_AWAIT_RESPOSTA)
                await message.channel.send(RESPOSTA_BOT)  # Envia a resposta configurada

        # Chama a função para gerenciar comandos
        await self.handle_comandos(message)


    async def handle_comandos(self, message):
        """
        Gerencia os comandos enviados pelos participantes por canal
        """
        # Verifica se a mensagem é um comando
        if message.content.startswith('!'):
            canal_nome = message.channel.name  # Obtém o nome do canal

            # Inicializa as estruturas de dados para o canal se ainda não existirem
            if canal_nome not in self.comandos_participantes_por_canal:
                self.comandos_participantes_por_canal[canal_nome] = {}
                self.comandos_enviados_por_canal[canal_nome] = []
                self.usuarios_participantes[canal_nome] = set()  # Inicializa o conjunto de participantes únicos por canal
                self.intervalo_ativo_por_canal[canal_nome] = False  # Define que o intervalo não está ativo inicialmente
            
            # Ignora comandos de bots
            #if message.author.name.lower() in [bot.lower() for bot in bots_twitch]:
                #return

            # Verifica se o intervalo está ativo
            if self.intervalo_ativo_por_canal[canal_nome]:
                print(f"Comando '{message.content}' ignorado no canal {canal_nome} (intervalo ativo).")
                return  # Ignora comandos durante o intervalo

            # Ignora comandos com letras maiúsculas
            if any(char.isupper() for char in message.content):
                print(f"Comando '{message.content}' ignorado (contém letras maiúsculas).")
                return  # Ignora comandos com letras maiúsculas

            # Normaliza o comando (minúsculas e sem espaços extras)
            comando_normalizado = message.content.strip().lower()

            # Verifica se o comando enviado está na lista de comandos válidos
            if comando_normalizado not in [comando.lower() for comando in comandos_validos]:
                print(f"Comando '{message.content}' ignorado (não está na lista de comandos válidos).")
                return  # Ignora o comando se não for válido

            # Verifica se o comando é de sorteio (você pode ajustar essa parte conforme necessário)
            if comando_normalizado in comandos_validos:
                # Ignora usuários que já participaram
                if message.author.name in self.usuarios_participantes[canal_nome]:
                    print(f"Usuário {message.author.name} já participou do sorteio no canal {canal_nome}.")
                    return

                # Marca o usuário como participante
                self.usuarios_participantes[canal_nome].add(message.author.name)

                # Conta os comandos dos participantes no canal
                if message.author.name not in self.comandos_participantes_por_canal[canal_nome]:
                    self.comandos_participantes_por_canal[canal_nome][message.author.name] = 0

                self.comandos_participantes_por_canal[canal_nome][message.author.name] += 1
                self.comandos_enviados_por_canal[canal_nome].append(message.content)  # Adiciona o comando à lista
                print(f"Comando contado para {message.author.name} no canal {canal_nome}: {self.comandos_participantes_por_canal[canal_nome][message.author.name]}")

                # Checa se temos o número configurado de participantes com comandos no canal
                if len(self.usuarios_participantes[canal_nome]) >= NUMERO_PARTICIPANTES:
                    current_time = time.time()  # Usando time.time() para pegar o tempo real

                    # Verifica se já passou o tempo necessário desde o último comando para o canal
                    last_command_time = self.last_command_time_por_canal.get(canal_nome, None)
                    if last_command_time is None or (current_time - last_command_time) >= TEMPO_INTERVALO_COMANDO:
                        # Inicia o intervalo de espera
                        self.intervalo_ativo_por_canal[canal_nome] = True
                        
                        # Escolhe um comando aleatório enviado
                        command_to_send = self.comandos_enviados_por_canal[canal_nome][-1]  # Último comando enviado
                        await asyncio.sleep(TEMPO_AWAIT_COMANDO)
                        await message.channel.send(command_to_send)  # Envia o comando
                        self.last_command_time_por_canal[canal_nome] = current_time  # Atualiza o tempo do último envio
                        print(f"Mensagem enviada: {command_to_send}")

                        # Limpa a lista de participantes após o sorteio
                        self.usuarios_participantes[canal_nome].clear()  # Limpa os participantes após o sorteio
                        print(f"Lista de participantes no canal {canal_nome} limpa.")

                        # Aguarda o intervalo de tempo antes de permitir novos comandos
                        await asyncio.sleep(TEMPO_INTERVALO_COMANDO)
                        self.intervalo_ativo_por_canal[canal_nome] = False  # Desativa o intervalo

                    # Limpa a lista para a próxima contagem
                    self.comandos_participantes_por_canal[canal_nome].clear()  
                    self.comandos_enviados_por_canal[canal_nome].clear()  # Limpa os comandos enviados
                    print(f"Lista de participantes e comandos no canal {canal_nome} limpos.")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
