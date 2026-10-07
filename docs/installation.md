# Instalação

```bash
pip install audivra
```

Em desenvolvimento, a partir da raiz do repositório:

```bash
pip install -e ".[dev]"
```

Requisitos: Python >= 3.10 e Django >= 5.2, < 6.2.

Adicione `audivra` em `INSTALLED_APPS` e rode `python manage.py migrate`. Uso no Django: [django.md](django.md).
