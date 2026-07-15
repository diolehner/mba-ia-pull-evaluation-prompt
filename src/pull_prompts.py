"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

Usa a serializacao nativa do LangChain para extrair o conteudo do prompt.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Prompt de baixa qualidade publicado pelo instrutor (ponto de partida).
SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def _extract_messages(prompt) -> dict:
    """
    Extrai os templates de mensagens (system/user) de um objeto retornado
    pelo hub.pull, que normalmente e um ChatPromptTemplate.

    Retorna um dicionario com system_prompt e user_prompt (quando existirem).
    """
    result = {"system_prompt": "", "user_prompt": ""}

    messages = getattr(prompt, "messages", None)
    if not messages:
        # Fallback: PromptTemplate simples (nao-chat)
        template = getattr(prompt, "template", None)
        if template:
            result["system_prompt"] = template
        return result

    for message in messages:
        # Cada item costuma ser um *MessagePromptTemplate com .prompt.template
        inner = getattr(message, "prompt", None)
        template_text = getattr(inner, "template", None)
        if template_text is None:
            continue

        role = type(message).__name__.lower()
        if "system" in role:
            result["system_prompt"] = template_text
        elif "human" in role or "user" in role:
            result["user_prompt"] = template_text
        elif not result["system_prompt"]:
            result["system_prompt"] = template_text

    return result


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt inicial do LangSmith Hub e salva localmente em YAML.

    Returns:
        True se sucesso, False caso contrario.
    """
    print(f"Puxando prompt do LangSmith Hub: {SOURCE_PROMPT}")

    try:
        prompt = hub.pull(SOURCE_PROMPT)
    except Exception as e:
        print(f"❌ Erro ao fazer pull de '{SOURCE_PROMPT}': {e}")
        print("\nVerifique:")
        print("  - LANGSMITH_API_KEY configurada no .env")
        print("  - Conexao com a internet")
        print(f"  - O prompt '{SOURCE_PROMPT}' existe e esta publico")
        return False

    print("   ✓ Prompt carregado com sucesso")

    messages = _extract_messages(prompt)

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": messages["system_prompt"],
            "user_prompt": messages["user_prompt"],
            "version": "v1",
            "source": SOURCE_PROMPT,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if save_yaml(prompt_data, OUTPUT_PATH):
        print(f"   ✓ Prompt salvo em: {OUTPUT_PATH}")
        return True

    print(f"❌ Falha ao salvar prompt em {OUTPUT_PATH}")
    return False


def main() -> int:
    """Funcao principal."""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    Path("prompts").mkdir(parents=True, exist_ok=True)

    ok = pull_prompts_from_langsmith()

    if ok:
        print("\n✅ Pull concluido. Analise o prompt v1 e crie a versao otimizada v2.")
        return 0

    print("\n❌ Pull falhou. Veja as mensagens acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
