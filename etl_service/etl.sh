#!/bin/sh

set -e


echo "⏳ Ожидаем доступность баз данных..."
echo "$MAIN_DB_HOST" "$MAIN_DB_PORT" 
echo 

# Ждём main-db
until pg_isready -h "$MAIN_DB_HOST" -p "$MAIN_DB_PORT"; do
  echo "🔁 main-db ($MAIN_DB_HOST:$MAIN_DB_PORT) ещё не готов..."
  sleep 2
done
echo "✅ main-db доступна."

# Ждём analytic-db
until pg_isready -h "$ANALYTIC_DB_HOST" -p "$ANALYTIC_DB_PORT"; do
  echo "🔁 analytic-db ($ANALYTIC_DB_HOST:$ANALYTIC_DB_PORT) ещё не готов..."
  sleep 2
done
echo "✅ analytic-db доступна."

echo "🚀 Запускаем ETL..."
exec python main.py