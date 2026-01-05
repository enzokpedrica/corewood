### Iniciar

Instalar WSL no Windows

rodar um sudo apt update + sudo apt upgrade

ls para verificar o diretorio presente

git clone https://github.com/enzokpedrica/corewood.git

ls para verificar se criou a pasta corewood



### Postgre

Instale: sudo apt install postgresql postgresql-contrib -y

Verifique o serviço: sudo service postgresql status

Acesse o usuário padrão (postgres): sudo -i -u postgres

Rode: psql

Crie um banco de dados e um usuário (opcional):
CREATE DATABASE corewood\_db;
CREATE USER kp\_user WITH ENCRYPTED PASSWORD 'kp\_pass';

 	GRANT ALL PRIVILEGES ON DATABASE corewood\_db TO kp\_user;

Com a criação do passo anterior, será necessário sair do psql: quit

Para acessar o psql e o banco: psql -U kp\_user -d corewood\_db



### Backend

Instalar Uvicorn: sudo apt install uvicorn

Instalar Pip: sudo apt install python3-pip -y

Instalar o requirements: python3 -m pip install --break-system-packages -r requirements.txt

Abra o VS Code: code .

Alterar o arquivo **database.py**, deixar a url ativa: "postgresql://kp\_user:kp\_pass@localhost/corewood\_db"...*Não esquecer de alterar o usuário, senha e nome do database. Deixar a url ativa somente comentada*

Rodar o backend: uvicorn app.main:app --reload



### Frontend

Abrir um novo terminal

Entrar dentro da pasta do frontend

Instalar o Node: sudo apt install nodejs npm

Alterar o arquivo .env para o ativo ser: REACT\_APP\_API\_URL=http://localhost:8000

Instalar o npm: npm install

Rodar o npm: npm start



### Observações

Após rodar o Frontend, será necessário descomentar o código do Registre-se para criar um usuário



senha core por postgree: kp\_user

senha core por kp\_user: kp\_pass



User Corewood: ekp

Pass Corewood: enzoeric



User Corewood: enzo.pedrica

Pass Corewood: enzoeric

