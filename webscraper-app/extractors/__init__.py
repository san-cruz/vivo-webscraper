"""
extractors/__init__.py — Roteamento slug → extractor
------------------------------------------------------
Mapeia cada categoria para seu módulo extractor especializado.
O scrapertxt.py importa get_extractor(slug) daqui.
"""

from extractors.base import get_entry, get_all_slugs, get_categories  # noqa: re-export

# Mapa categoria → módulo extractor
# Adicione uma entrada aqui sempre que criar um novo extractor.
_CATEGORY_TO_MODULE: dict[str, str] = {
    "Ativação de Serviços Digitais": "extractors.ativacao-servicos-digitais",
    "Ajuda e Autoatendimento":       "extractors.ajuda-e-autoatendimento",
    "Dúvidas — Internet":            "extractors.duvidas-internet-tv",
    "Dúvidas — TV":                  "extractors.duvidas-internet-tv",
    "Fatura":                        "extractors.fatura",   

}

# Categorias ainda sem extractor especializado
_FALLBACK_CATEGORIES = {
    "Vivo Explica",
    "Por que Vivo",
    "Conteúdos Complementares",
}


def _load_module(module_name: str):
    """Carrega um módulo pelo nome, suportando nomes com hífen."""
    import importlib
    import importlib.util
    import sys
    from pathlib import Path

    # Tenta import normal primeiro (módulos sem hífen)
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        pass

    # Fallback: carrega o arquivo .py diretamente pelo caminho
    # (necessário para nomes de módulo com hífen, ex: ativacao-servicos-digitais)
    parts = module_name.split(".")          # ["extractors", "ativacao-servicos-digitais"]
    rel_path = Path(*parts).with_suffix(".py")   # extractors/ativacao-servicos-digitais.py
    abs_path = Path(__file__).parent.parent / rel_path

    if not abs_path.exists():
        raise FileNotFoundError(f"Extractor não encontrado: {abs_path}")

    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def get_extractor(slug: str):
    """
    Retorna o módulo extractor correto para o slug dado.
    Lança NotImplementedError se a categoria ainda não tem extractor.
    """
    entry = get_entry(slug)
    category = entry["category"]

    module_name = _CATEGORY_TO_MODULE.get(category)
    if module_name is None:
        if category in _FALLBACK_CATEGORIES:
            raise NotImplementedError(
                f"Categoria '{category}' ainda não tem extractor especializado.\n"
                f"Crie extractors/<slug-da-categoria>.py e registre em _CATEGORY_TO_MODULE."
            )
        raise ValueError(f"Categoria desconhecida: '{category}'")

    return _load_module(module_name)