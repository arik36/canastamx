#!/usr/bin/env bash
#
# instalar-hooks.sh — CanastaMX
#
# Activa los ganchos de Git que están versionados en .githooks/
# Lo corre CADA INTEGRANTE una vez, después de clonar.
#
#   bash infra/scripts/instalar-hooks.sh
#
# Qué hacen:
#   pre-commit  · impide confirmar un .env, carpetas de dependencias o
#                 archivos de más de 10 MB
#   pre-push    · impide enviar directamente a main
#
# Por qué esto y no protección de ramas: la protección de ramas en un
# repositorio privado exige plan de pago. Estos ganchos son gratis, viven en el
# repositorio y atrapan el error honesto, que es el que de verdad ocurre.
#
# No son seguridad: quien quiera puede saltárselos con --no-verify. Son una red.

set -euo pipefail

[[ -d .git ]] || { echo "Córrelo desde la raíz del repositorio." >&2; exit 1; }
[[ -d .githooks ]] || { echo "No encuentro .githooks/. ¿Hiciste git pull?" >&2; exit 1; }

chmod +x .githooks/* 2>/dev/null || true
git config core.hooksPath .githooks

echo
echo "  ✓ Ganchos activados en este repositorio."
echo
echo "    pre-commit  · bloquea .env, node_modules, .venv, target y archivos >10 MB"
echo "    pre-push    · bloquea el envío directo a main"
echo
echo "  Para comprobarlo:  git config core.hooksPath     → debe decir .githooks"
echo
echo "  Solo aplican a este repositorio y a tu máquina. Cada integrante"
echo "  tiene que correr este guión una vez después de clonar."
echo
