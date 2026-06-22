# Inventario do projeto antigo

## Resumo

O projeto antigo existe em `C:\\Users\\DIEGO\\Documents\\PROJETO OPENCLAW\\bmo-nanobot-desktop`.
Ele ja trazia Electron, React, um backend Python local, o nanobot vendorizado, a bridge do WhatsApp e a area de runtime com vozes, Whisper e wake word.

## Confirmacao do checkpoint A

- `runtime\\piper\\bmo.onnx` encontrado
- `runtime\\piper\\bmo.onnx.json` encontrado

Isso confirma que a voz customizada `bmo` existe no acervo antigo.

## Telas encontradas no frontend

O frontend antigo concentrou tudo em um unico arquivo grande `src\\App.tsx`, mas a interface cobre as 12 telas pedidas:

1. Chat
2. Memoria
3. Historico
4. Modelos
5. Provedores
6. Voz
7. Ferramentas
8. Workspace
9. Skills
10. Canais
11. Sistema
12. Configuracoes

## Voz

### Piper TTS

Vozes encontradas no acervo antigo:

- `bmo`
- `pt_BR-faber-medium`
- `pt-BR-razo-medium`
- `miro_pt-BR`
- `pt_BR-sage_13364-medium`
- `dii_pt-BR`
- `en_GB-semaine-medium`

### Whisper.cpp

O acervo antigo tambem trazia os binarios locais do Whisper e a escolha de tres modelos:

- `tiny`
- `base`
- `small`

Tambem havia suporte a aceleracao por GPU com fallback para CPU, alem de wake word com `openwakeword`.

## Ferramentas

O nanobot ja carregava as ferramentas nativas esperadas pelo projeto:

- arquivos
- shell
- busca web
- cron
- tarefas longas
- memoria
- mensagem
- subagentes
- skills

## Subagentes

O projeto antigo ja tinha execucao em background via `AgentLoop` e persistencia do resultado em arquivo.

## Canais

O pacote `nanobot/channels` copiado do projeto antigo tem estes modulos de canal:

- Telegram
- Discord
- Slack
- WhatsApp
- Email
- Matrix
- Signal
- WebSocket
- DingTalk
- Feishu
- QQ
- Microsoft Teams
- WeCom
- Weixin
- Mochat
- Napcat

O checklist do pedido menciona 14 integracoes, mas a arvore real do nanobot exposta no projeto antigo mostra 16 modulos de canal, sendo `napcat` um modulo extra alem da lista comercial citada.

## Bridge WhatsApp

A bridge em Node.js/TypeScript usa Baileys, se liga em `127.0.0.1`, exige token e rejeita `Origin` de navegador.

## Electron

O shell Electron antigo tinha:

- instancia unica
- tray
- menu Abrir/Sair
- hotkey global configuravel
- reposicionamento da janela quando ela sai da tela
- notificacoes e popup flutuante para lembretes

## Visual

O projeto antigo trazia:

- 7 temas visuais
- sprites de rosto para idle, listening, thinking, speaking, error e warmup
- fundos e imagens do BMO

## Arquivos chave do acervo antigo

- `backend\\bmo_backend.py`
- `backend\\nanobot_runtime.py`
- `backend\\nanobot_integration.py`
- `bridge\\src\\server.ts`
- `bridge\\src\\whatsapp.ts`
- `electron\\main.cjs`
- `src\\App.tsx`
- `src\\App.css`
- `SOUL.md`
- `runtime\\piper\\`
- `runtime\\whisper.cpp\\`
- `runtime\\sounds\\`
- `runtime\\wakeword.onnx`

## Observacao tecnica

O frontend antigo estava inchado em um unico componente grande e o backend antigo tinha muitos caminhos juntos. O trabalho do BMO-V2 e separar isso por dominio sem perder as capacidades reais que ja existiam.
