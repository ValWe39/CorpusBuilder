"""Fixtures d'intégration (décision D9 de research.md).

Les exemples réels (Examples/) sont utilisés en lecture seule ; les jeux
de données d'erreur et le compteur sont isolés dans des répertoires
temporaires — le compteur réel du développeur n'est jamais consommé.
"""

import json
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
EXAMPLES_1 = REPO / "Examples" / "Exemple1"
EXAMPLES_2 = REPO / "Examples" / "Exemple2"


def exemples_disponibles() -> bool:
    return EXAMPLES_1.is_dir() and EXAMPLES_2.is_dir()


@pytest.fixture
def counter_file(tmp_path):
    """Compteur isolé, absent au départ (première exécution -> 0001)."""
    return tmp_path / "counter.txt"


@pytest.fixture
def make_couple(tmp_path):
    """Fabrique un couple document synthétique dans un dossier temporaire."""

    def _make(
        stem: str,
        n_chunks: int = 3,
        dim: int = 4,
        dtype=np.float64,
        n_vectors: int | None = None,
        npy_suffix: str = "0001",
        subfolder: str = "in",
    ) -> Path:
        folder = tmp_path / subfolder
        folder.mkdir(parents=True, exist_ok=True)
        doc = {
            "schema_version": "1.0",
            "document": {
                "path": f"synthetic://{stem}.md",
                "title": f"Doc {stem}",
                "structure": "sections",
                "typologie": "documentation",
            },
            "params": {"chunk_min": 10},
            "chunks": [
                {
                    "ref": i + 1,
                    "text": f"chunk {i + 1} de {stem}",
                    "part": f"Partie {i + 1}",
                }
                for i in range(n_chunks)
            ],
        }
        json_path = folder / f"{stem}.json"
        json_path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        rows = n_chunks if n_vectors is None else n_vectors
        matrix = np.zeros((rows, dim), dtype=dtype)
        np.save(folder / f"{stem}-{npy_suffix}.npy", matrix)
        return folder

    return _make


def read_corpus(out_folder: Path) -> tuple[list[dict], np.ndarray, str]:
    """Charge le couple produit dans un dossier de sortie."""
    json_files = [p for p in out_folder.iterdir() if p.suffix == ".json"]
    npy_files = [p for p in out_folder.iterdir() if p.suffix == ".npy"]
    assert len(json_files) == 1, f"attendu 1 json, trouvé {len(json_files)}"
    assert len(npy_files) == 1, f"attendu 1 npy, trouvé {len(npy_files)}"
    rows = json.loads(json_files[0].read_text(encoding="utf-8"))
    matrix = np.load(npy_files[0])
    return rows, matrix, json_files[0].stem
