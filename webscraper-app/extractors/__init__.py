"""extractors/__init__.py — Roteamento slug → extractor"""

from extractors.base import get_entry, get_all_slugs, get_categories  # noqa: re-export

_CATEGORY_TO_MODULE: dict[str, str] = {
    "Produtos e Serviços Geral":     "extractors.produtos-servicos-geral",
    "Para Casa — Internet":          "extractors.para-casa-internet",
    "Para Casa — Inteligente":       "extractors.para-casa-inteligente",
    "Para Casa — TV":                "extractors.para-casa-tv",
    "Combos":                        "extractors.combos",
    "Serviços Digitais":             "extractors.servicos-digitais",
    "HUBs de Marcas e Categorias":   "extractors.hubs-marcas-categorias",
    "Ativação de Serviços Digitais": "extractors.ativacao-servicos-digitais",
    "Ajuda e Autoatendimento":       "extractors.ajuda-e-autoatendimento",
    "Dúvidas — Internet":            "extractors.duvidas-internet-tv",
    "Dúvidas — TV":                  "extractors.duvidas-internet-tv",
    "Fatura":                        "extractors.fatura",
    "Vivo Explica":                  "extractors.vivo-explica",
    "Por que Vivo":                  "extractors.por-que-vivo",
    "Conteúdos Complementares":      "extractors.conteudos-complementares",
}

_FALLBACK_CATEGORIES: set[str] = set()  # todas as categorias têm extractor


def _load_module(module_name: str):
    import importlib, importlib.util, sys
    from pathlib import Path
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        pass
    parts = module_name.split(".")
    abs_path = Path(__file__).parent.parent / Path(*parts).with_suffix(".py")
    if not abs_path.exists():
        raise FileNotFoundError(f"Extractor não encontrado: {abs_path}")
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def get_extractor(slug: str):
    entry = get_entry(slug)
    category = entry["category"]
    module_name = _CATEGORY_TO_MODULE.get(category)
    if module_name is None:
        if category in _FALLBACK_CATEGORIES:
            raise NotImplementedError(f"Categoria '{category}' ainda não tem extractor especializado.")
        raise ValueError(f"Categoria desconhecida: '{category}'")
    return _load_module(module_name)