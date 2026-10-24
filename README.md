# Plantilla de repositorio base — Especialización en Desarrollo con IA Generativa (Accenture)

Esta es la estructura base que vas a usar como punto de partida para tu proyecto en este programa. Es la misma estructura que vas a ir ampliando bloque a bloque, hasta llegar a la aplicación completa que entregas en el Gate 3.

## Cómo empezar

### macOS / Linux / WSL
1. Clona este repositorio utilizando el comando `git clone https://github.com/slorcadelgado/proyectoIA prueba-gate1` y entra a la carpeta con el comando `cd prueba-gate1`.
2. Crea tu entorno virtual de Python usando el comando `python3 -m venv .venv` en tu terminal y actívalo usando el comando `source .venv/bin/activate`.
3. Instala las dependencias del proyecto usando el comando `.venv/bin/pip install -r requirements.txt` para poder usarlas en la aplicación.
4. Copia `.env.example` a un archivo nuevo llamado `.env` usando el comando `cp .env.example .env` y cambia el valor de `GEMINI_API_KEY` en `.env` por tu API Key.
5. Ejectua la aplicación usando el comando `python3 src/consumir_gemini.py`, `python3 src/evaluacion_modelos.py` o `python3 src/consistencia.py`.
 
### Windows (PowerShell)
1. Clona este repositorio utilizando el comando `git clone https://github.com/slorcadelgado/proyectoIA prueba-gate1` y entra a la carpeta con el comando `cd prueba-gate1`.
2. Crea tu entorno virtual de Python usando el comando `python -m venv venv` en tu terminal y actívalo usando el comando `venv/Scripts/activate`.
Nota: Si PowerShell te da error al utilizar el comando `venv/Scripts/activate`, ejecuta el comando `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` para permitir scripts locales solo para tu usuario y vuelve a ejecutar el comando `venv/Scripts/activate`.
3. Instala las dependencias del proyecto usando el comando `pip install -r requirements.txt` para poder usarlas en la aplicación.
4. Copia `.env.example` a un archivo nuevo llamado `.env` usando el comando `Copy-Item .env.example .env` y cambia el valor de `GEMINI_API_KEY` en `.env` por tu API Key.
5. Ejectua la aplicación usando el comando `python src/consumir_gemini.py`, `python src/evaluacion_modelos.py` o `python src/consistencia.py`.

## Estructura de carpetas

- `src/` : todo el código fuente de tu proyecto va aquí.
- `docs/` : documentación técnica del proyecto (diagramas, decisiones de arquitectura, notas).
- `tests/` : pruebas de tu código (las vas a usar más adelante en el programa, cuando el proyecto lo requiera).
- `requirements.txt` : dependencias de Python de tu proyecto, para que cualquier otra persona pueda reconstruir tu entorno con un solo comando.
- `.env.example` : plantilla de las variables de entorno que tu proyecto necesita, sin valores reales. Tu archivo `.env` real (con tus credenciales) nunca se commitea.
- `.gitignore` : le dice a Git qué archivos y carpetas ignorar (entre ellos, tu entorno virtual y tu archivo `.env`).

## Reglas que se mantienen durante todo el programa

- Ningún secreto (contraseña, llave de API, token) va escrito directamente en el código ni en ningún archivo que se suba al repositorio.
- Cada proyecto nuevo tiene su propio entorno virtual: no se comparten dependencias entre proyectos distintos.
- Todo el trabajo que se entrega en este programa vive en un repositorio de GitHub, sin excepción.

## Registro del ensayo de instalación limpia
 
- Fecha: 23/10/2026
- Encontrado: La instalación en Windows falló porque PowerShell por defecto no permite ejecutar scripts.
- Corregido: Se agregó una nota con el comando que se utilizó para arreglar eso.
- Resultado tras la corrección: Se pudo realizar la ejecución de los distintos programas en Windows.
