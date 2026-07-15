"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Le os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PUBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descricao, tecnicas utilizadas)
"""

import os
import re
import sys
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

V2_PATH = "prompts/bug_to_user_story_v2.yml"
REPO_NAME = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura basica de um prompt otimizado.

    Args:
        prompt_data: Dados do prompt (secao interna do YAML)

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    user_prompt = (prompt_data.get("user_prompt") or "").strip()

    if not system_prompt:
        errors.append("system_prompt vazio")
    if not user_prompt:
        errors.append("user_prompt vazio")
    if re.search(r"\bTODO\b", system_prompt) or re.search(r"\bTODO\b", user_prompt):
        errors.append("prompt ainda contem TODOs")
    if "{bug_report}" not in user_prompt and "{bug_report}" not in system_prompt:
        errors.append("prompt nao referencia a variavel {bug_report}")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(f"minimo de 2 tecnicas requeridas, encontradas: {len(techniques)}")

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PUBLICO).

    Args:
        prompt_name: Identificador do repo no Hub (ex.: username/bug_to_user_story_v2)
        prompt_data: Dados do prompt (secao interna do YAML)

    Returns:
        True se sucesso, False caso contrario.
    """
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data["user_prompt"]

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data.get(
        "description", "Prompt otimizado para converter bugs em User Stories"
    )
    tags = list(prompt_data.get("tags", [])) + [f"tecnica:{t}" for t in techniques]

    readme = (
        f"# {prompt_name}\n\n"
        f"{description}\n\n"
        f"## Tecnicas aplicadas\n"
        + "\n".join(f"- {t}" for t in techniques)
    )

    client = Client()

    try:
        url = client.push_prompt(
            prompt_name,
            object=chat_prompt,
            is_public=True,
            description=description,
            readme=readme,
            tags=tags,
        )
        print(f"   ✓ Push publico concluido: {url}")
        return True
    except TypeError:
        # Fallback para versoes que nao aceitam todos os kwargs.
        from langchain import hub

        url = hub.push(prompt_name, chat_prompt, new_repo_is_public=True)
        print(f"   ✓ Push publico concluido (fallback hub.push): {url}")
        return True
    except Exception as e:
        print(f"❌ Erro ao fazer push de '{prompt_name}': {e}")
        return False


def main() -> int:
    """Funcao principal."""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS AO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/{REPO_NAME}"

    data = load_yaml(V2_PATH)
    if not data:
        print(f"❌ Nao foi possivel carregar {V2_PATH}")
        return 1

    # A secao interna do YAML tem a mesma chave do nome do prompt v2.
    prompt_data = data.get("bug_to_user_story_v2", data)

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt invalido:")
        for err in errors:
            print(f"   - {err}")
        return 1

    print(f"Publicando prompt: {prompt_name}")
    ok = push_prompt_to_langsmith(prompt_name, prompt_data)

    if ok:
        print("\n✅ Push concluido. Rode a avaliacao: python src/evaluate.py")
        print("   Confira no dashboard: https://smith.langchain.com/prompts")
        return 0

    print("\n❌ Push falhou. Veja as mensagens acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
