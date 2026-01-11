#!/bin/bash

# Configurações
DB_NAME="corewood_db"
DB_USER="kp_user"
BACKUP_FILE="backup.sql"

# 1. Derruba o banco se já existir
echo "Removendo banco existente..."
psql -U postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

# 2. Cria novamente o banco com o dono correto
echo "Criando banco ${DB_NAME}..."
psql -U postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

# 3. Restaura o backup no banco recém-criado
echo "Restaurando backup..."
psql -U ${DB_USER} -d ${DB_NAME} < ${BACKUP_FILE}

echo "✅ Restauração concluída com sucesso!"
