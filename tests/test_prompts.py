"""
Testes automatizados para validação de prompts.

Valida o prompt otimizado em prompts/bug_to_user_story_v2.yml quanto a:
- presença de system prompt
- definição de persona (Role Prompting)
- exigência de formato (Markdown / User Story padrão)
- exemplos few-shot
- ausência de TODOs
- mínimo de 2 técnicas declaradas nos metadados
"""
import re
import sys
import yaml
import pytest
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure  # noqa: F401 (disponível para uso)

V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_prompt_data():
    """
    Retorna a seção interna do prompt v2, tolerando tanto o formato aninhado
    (chave 'bug_to_user_story_v2') quanto um YAML plano.
    """
    data = load_prompts(str(V2_PATH))
    assert data, "YAML do prompt v2 vazio ou inválido"
    return data.get("bug_to_user_story_v2", data)


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = get_prompt_data()
        assert "system_prompt" in prompt, "Campo 'system_prompt' ausente"
        assert prompt["system_prompt"].strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = get_prompt_data()["system_prompt"].lower()
        assert re.search(r"você é um", system_prompt), (
            "O prompt não define uma persona (esperado algo como 'Você é um ...')"
        )
        assert "product manager" in system_prompt, (
            "A persona esperada (Product Manager) não foi encontrada"
        )

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = get_prompt_data()["system_prompt"].lower()
        mentions_markdown = "markdown" in system_prompt
        mentions_user_story_template = (
            "como um" in system_prompt
            and "eu quero" in system_prompt
            and "para que" in system_prompt
        )
        assert mentions_markdown or mentions_user_story_template, (
            "O prompt não exige formato Markdown nem o template padrão de User Story"
        )

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = get_prompt_data()["system_prompt"].lower()
        assert "exemplo" in system_prompt, "Nenhum 'Exemplo' encontrado no prompt"
        # Exemplos few-shot exigem par entrada/saída explícito.
        assert "bug report" in system_prompt, "Faltam entradas de exemplo (BUG REPORT)"
        assert "user story" in system_prompt, "Faltam saídas de exemplo (USER STORY)"
        # Pelo menos 2 exemplos para caracterizar few-shot.
        assert system_prompt.count("bug report") >= 2, (
            "Few-shot requer ao menos 2 exemplos de entrada/saída"
        )

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt = get_prompt_data()
        blob = yaml.dump(prompt, allow_unicode=True)
        # Placeholder real é o marcador TODO em caixa alta (ex.: [TODO]).
        # \bTODO\b case-sensitive evita falso positivo com a palavra "TODOS"/"todos".
        assert not re.search(r"\bTODO\b", blob), "Ainda há [TODO] pendente no prompt v2"
        assert "[TODO]" not in blob, "Ainda há placeholder [TODO] no prompt v2"

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = get_prompt_data().get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
