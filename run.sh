#!/bin/bash

# Run BookmarkerDjango app in Linux with this script

# Turvalised, aga mitte liiga ranged seaded
set -Euo pipefail

# Funktsioon veateadete jaoks
error() {
    local exit_code=$?
    echo "❌ Viga reas $BASH_LINENO: $BASH_COMMAND (kood: $exit_code)" >&2
}

# Püüame vead kinni, aga ei tapa skripti kohe
trap error ERR

# --- Mitmekeelne väljund: seadistus ---
# Keele määramine: --lang=xx > RUN_LANG > LANG > et
LANG_CODE=""
for arg in "$@"; do
  case "$arg" in
    --lang=*) LANG_CODE="${arg#*=}";;
  esac
done
if [[ -z "$LANG_CODE" ]]; then
  if [[ -n "${RUN_LANG:-}" ]]; then
    LANG_CODE="$RUN_LANG"
  else
    LANG_CODE="${LANG%%_*}"   # nt en_US.UTF-8 -> en
  fi
fi
case "$LANG_CODE" in et|en|fr) ;; *) LANG_CODE="en";; esac

# --- Tõlked ---
# Kasutame võtmeid (nt start_django, wait_react_url) ja lühikesi lauseid.
declare -A T_et=(
  [start_django]="🚀 Käivitan Django serveri..."
  [waited]="..oodatud"
  [seconds]="sekundit"
  [start_react]="🚀 Käivitan React serveri..."
  [wait_react_url]="⏳ Ootan, kuni React vastab aadressil %s ..."
  [react_ready]="🌐 React on valmis! Avan brauseri..."
  [servers_running]="💡 Serverid töötavad. Logid:"
  [log_django]="   Django logi: %s"
  [log_react]="   React logi:  %s"
  [stop_hint]="Sulge aken või vajuta Ctrl+C, et peatada."
  [waiting_all]="💤 Ootan serverite lõppemist..."
)
declare -A T_en=(
  [start_django]="🚀 Starting Django server..."
  [waited]="..waited"
  [seconds]="seconds"
  [start_react]="🚀 Starting React server..."
  [wait_react_url]="⏳ Waiting for React at %s ..."
  [react_ready]="🌐 React is ready! Opening browser..."
  [servers_running]="💡 Servers running. Logs:"
  [log_django]="   Django log: %s"
  [log_react]="   React log:  %s"
  [stop_hint]="Close the window or press Ctrl+C to stop."
  [waiting_all]="💤 Waiting for processes to exit..."
)
declare -A T_fr=(
  [start_django]="🚀 Démarrage du serveur Django..."
  [waited]="..attendu"
  [seconds]="secondes"
  [start_react]="🚀 Démarrage du serveur React..."
  [wait_react_url]="⏳ En attente de React sur %s ..."
  [react_ready]="🌐 React est prêt ! Ouverture du navigateur..."
  [servers_running]="💡 Serveurs en cours d’exécution. Journaux :"
  [log_django]="   Journal Django : %s"
  [log_react]="   Journal React :  %s"
  [stop_hint]="Fermez la fenêtre ou appuyez sur Ctrl+C pour arrêter."
  [waiting_all]="💤 En attente de la fin des processus..."
)

# --- Tõlkefunktsioonid ---
t() {  # t KEY -> tekst
  local key="$1"
  declare -n map="T_${LANG_CODE}"
  local val="${map[$key]}"
  if [[ -z "$val" ]]; then
    declare -n fallback="T_en"
    val="${fallback[$key]}"
  fi
  printf "%s" "$val"
}
tf() { # tf KEY args... -> vormindatud tekst (printf-stiilis)
  local key="$1"; shift
  printf "$(t "$key")" "$@"
}

# --- Seaded ---
PROJECT_DIR="/home/rk/projektid/BookmarkerDjango"
DJANGO_LOG="$PROJECT_DIR/django.log"
REACT_LOG="$PROJECT_DIR/react.log"
REACT_URL="http://192.168.0.103:3000"

# === Värvid ===
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
BLUE="\033[34m"
RESET="\033[0m"

# kui terminal ei toeta värve siis lülitab välja
if [[ ! -t 1 ]]; then
    GREEN=""; YELLOW=""; RED=""; BLUE=""; RESET=""
fi

# Kontrollime kas paketid on olemas, et skript ja rakendus töötaks
for cmd in python3 npm curl xdg-open; do
    command -v "$cmd" >/dev/null 2>&1 || {
        printf "${RED}❌ Viga: Käsk '%s' puudub PATH-ist.${RESET}\n" "$cmd"
        exit 1
    }
done

# ---Protsessigrupi ID ja Cleanup: tapame kogu protsessigrupi, kui terminal sulgub ---
PGID="$$"
CLEANED=0
cleanup() {
  echo "⚠️ cleanup käivitati, põhjus: $reason"
  jobs -l
  local reason="${1:-EXIT}"
  if (( CLEANED )); then exit 0; fi
  CLEANED=1
  # Väldi rekursiooni
  trap - HUP INT TERM EXIT

  echo -e "\n⏹ Peatan serverid (põhjus: $reason)..."
    echo "   Django PID: $DJANGO_PID"
    echo "   React  PID: $REACT_PID"

  # Saada esmalt viisakas lõpetamine
  kill -TERM -"$PGID" 2>/dev/null || true
  # Oota veidi, siis vajadusel jõuliselt
  sleep 2
  kill -KILL -"$PGID" 2>/dev/null || true
  exit 0
}

# Püüa terminali sulgemine (SIGHUP), Ctrl+C (SIGINT), lõpetamine (SIGTERM) ja ka tavaline EXIT
trap 'cleanup HUP' HUP
trap 'cleanup INT' INT
trap 'cleanup TERM' TERM
trap 'cleanup EXIT' EXIT

# --- Django käivitamine ---
printf "${BLUE} %s\n" "$(t start_django)"
cd "$PROJECT_DIR" || exit
source .venv/bin/activate

# Django serveri logi ainult faili salvestatuna
python3 manage.py runserver > "$DJANGO_LOG" 2>&1 &

# Django serveri logi faili salvestatuna ja terminalis reaalajas
#python3 manage.py runserver 2>&1 \
#  | tee "$DJANGO_LOG" \
#  | grep -v "Watching for file changes with StatReloader" &

DJANGO_PID=$!

# --- React käivitamine ---
printf "${BLUE} %s\n" "$(t start_react)"
cd "$PROJECT_DIR/frontend" || exit
npm start > "$REACT_LOG" 2>&1 &
REACT_PID=$!

# --- Ootame Reacti valmimist ---
printf "${YELLOW} %s\n" "$(tf wait_react_url "$REACT_URL")"

set +e  # lubame mitte-null koodid ilma skripti peatamata
timeout=60
elapsed=0

until curl -s -o /dev/null -w "%{http_code}" "$REACT_URL" | grep -qE "200|30[0-9]"; do
    sleep 1
    ((++elapsed))  # pre-increment, ei anna esimesel korral exit code 1
    printf "${BLUE} %s %s %s\n" "$(t waited)" "$elapsed" "$(t seconds)"

    if (( elapsed >= timeout )); then
        printf "${RED}❌ React ei käivitunud %s sekundi jooksul.${RESET}\n" "$timeout"
        set -e  # taastame range režiimi enne cleanup'i
        cleanup "React timeout"
    fi
done
set -e  # taastame range režiimi

# --- Ava brauser ---
printf "${GREEN} %s\n" "$(t react_ready)"
xdg-open "$REACT_URL" >/dev/null 2>&1 &

# --- Hoiame skripti elus ---
printf "${GREEN} %s\n" "$(t servers_running)"
printf "%s\n" "$(tf log_django "$DJANGO_LOG")"
printf "%s\n" "$(tf log_react "$REACT_LOG")"
printf "${YELLOW} %s\n" "$(t stop_hint)"

# Hoia skript elus kuni mõni protsess lõpeb; trap hoolitseb sulgemise eest
printf "${BLUE} %s\n" "$(t waiting_all)"
while true; do
    wait -n || break
done
