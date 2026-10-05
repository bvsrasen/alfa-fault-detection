import numpy as np
import pytest

from alfa.zaman import son_ornek


def test_son_ornek_gelecegi_kullanmiyor():
    t = np.array([0.0, 0.25, 0.5])
    x = np.array([1.0, 2.0, 3.0])
    # 0.3'te elimizde 0.25'teki örnek var, 0.5'teki henüz gelmedi
    assert son_ornek(t, x, np.array([0.3]))[0] == 2.0
    # tam örnek anında o örnek kullanılabilir
    assert son_ornek(t, x, np.array([0.5]))[0] == 3.0


def test_son_ornek_ilk_ornekten_once():
    with pytest.raises(ValueError):
        son_ornek(np.array([1.0, 2.0]), np.array([1.0, 2.0]), np.array([0.5]))
