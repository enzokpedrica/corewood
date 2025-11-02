# CoreWood

Sistema de geração de documentação técnica para indústria moveleira.

## Stack
- Backend: FastAPI (Python)
- Frontend: React (JavaScript)
- Deploy: Render + Netlify

## Desenvolvimento

### Backend
\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm install
npm start
\`\`\`
EOF

echo "✅ Estrutura criada com sucesso!"
```