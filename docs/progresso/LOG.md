# Progresso

## 2026-06-22

Organizei a base inicial do BMO-V2 e levantei o inventario do projeto antigo. Ja confirmei a voz customizada `bmo` no acervo original e mapeei as telas, canais, ferramentas e ativos de voz que precisam ser preservados.

Tambem deixei a estrutura principal pronta para seguir com a integracao limpa: configuracao, backend Python, interface React, Electron, bridge do WhatsApp e area de runtime. O que vale testar agora, quando a proxima base estiver ligada, e abrir o app e ver a navegacao principal sem erro.

Nesta rodada a base nova passou a compilar e o backend local ja responde em `/api/health` e `/api/bootstrap`. A tela principal abre com a navegacao lateral, o status do motor aparece na interface e a area de Provedores ja aceita chave, modelo e teste de conexao. O que vale conferir na pratica e iniciar o app, navegar pelas telas e ver se a interface carrega sem travar.

Fechamento tecnico desta etapa: o lint voltou limpo e o build de producao tambem passou. Corrigi a configuracao do ESLint para aceitar os arquivos CommonJS do Electron e do build-support, e removi efeitos de React que estavam sincronizando estado de formulario de forma desnecessaria. Agora o formulario de Provedores, Voz e Configuracoes inicializa corretamente quando o bootstrap chega pela primeira vez, sem disparar warnings do lint.

Encontrei a causa da tela preta/vazia ao abrir o app: o site gerado para producao estava apontando os arquivos internos com caminho absoluto, o que nao funciona direito quando o Electron abre a pagina local. Ajustei a geracao para usar caminhos relativos no build e reabri o BMO-V2 com essa correcao. O que vale testar agora e abrir a janela de novo e confirmar que a interface aparece completa, em vez de ficar vazia.

Nesta rodada eu liguei as telas que ainda estavam so como resumo, para o app conversar com o motor de verdade. Historico agora mostra as conversas reais, Lembretes permite criar, remover e limpar agendamentos, e Subagentes pode ser disparado pela interface. O que vale testar na pratica e abrir Historico, criar um lembrete de poucos minutos e iniciar um subagente curto para ver o painel reagir.
