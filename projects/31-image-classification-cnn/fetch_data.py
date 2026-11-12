"""Download Fashion-MNIST (Xiao, Rasul & Vollgraf, 2017; MIT licence) into data/ if not present."""
import gzip, pathlib, urllib.request
import numpy as np

URL = "https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/"
FILES = ["train-images-idx3-ubyte", "train-labels-idx1-ubyte", "t10k-images-idx3-ubyte", "t10k-labels-idx1-ubyte"]
DATA = pathlib.Path(__file__).resolve().parent / "data"


def load():
    DATA.mkdir(exist_ok=True)
    out = []
    for f in FILES:
        p = DATA / f"{f}.gz"
        if not p.exists():
            urllib.request.urlretrieve(URL + f + ".gz", p)
        with gzip.open(p, "rb") as fh:
            raw = fh.read()
        out.append(np.frombuffer(raw, np.uint8, offset=16 if "images" in f else 8))
    xtr, ytr, xte, yte = out
    return xtr.reshape(-1, 28, 28), ytr, xte.reshape(-1, 28, 28), yte


if __name__ == "__main__":
    print([a.shape for a in load()])
