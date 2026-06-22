# Runtime assets

Este arquivo lista os ativos grandes que devem ficar fora do Git e ser colocados em `runtime/` no computador do usuario final.

## Piper

Origem esperada: `C:\\Users\\DIEGO\\Documents\\PROJETO OPENCLAW\\bmo-nanobot-desktop\\runtime\\piper`

Arquivos esperados:

- `bmo.onnx`
- `bmo.onnx.json`
- `pt_BR-faber-medium.onnx`
- `pt_BR-faber-medium.onnx.json`
- `pt-BR-razo-medium.onnx`
- `pt-BR-razo-medium.onnx.json`
- `miro_pt-BR.onnx`
- `miro_pt-BR.onnx.json`
- `pt_BR-sage_13364-medium.onnx`
- `pt_BR-sage_13364-medium.onnx.json`
- `dii_pt-BR.onnx`
- `dii_pt-BR.onnx.json`
- `en_GB-semaine-medium.onnx`
- `en_GB-semaine-medium.onnx.json`

## Whisper.cpp

Origem esperada: `C:\\Users\\DIEGO\\Documents\\PROJETO OPENCLAW\\bmo-nanobot-desktop\\runtime\\whisper.cpp`

Arquivos esperados:

- `Win32\\Release\\whisper-cli.exe`
- `Win32\\Release\\whisper.dll`
- `Win32\\Release\\SDL2.dll`
- `Win32\\Release\\ggml.dll`
- `Win32\\Release\\ggml-cpu.dll`
- `Win32\\Release\\ggml-base.dll`

Os modelos `.bin` devem ser colocados na pasta de modelos do Whisper.

## Wake word

Origem esperada: `C:\\Users\\DIEGO\\Documents\\PROJETO OPENCLAW\\bmo-nanobot-desktop\\runtime\\wakeword.onnx`

## Sons

Origem esperada: `C:\\Users\\DIEGO\\Documents\\PROJETO OPENCLAW\\bmo-nanobot-desktop\\runtime\\sounds`

## Instalação do Windows

Origem esperada: `C:\\Users\\DIEGO\\Documents\\PROJETO OPENCLAW\\bmo-nanobot-desktop\\build-support\\redist`

- `vc_redist.x64.exe`
- `MicrosoftEdgeWebview2Setup.exe`

## Regra

Arquivos grandes nao devem ser commitados. Eles devem existir no disco local e ser referenciados pelo app e pelo instalador.
