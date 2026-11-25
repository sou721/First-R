"""暗記カードを、サーバーなしで開ける1つの HTML ファイルに書き出す。

    python build_static.py            → docs/index.html（GitHub Pages やファイル直接開き用）
    python build_static.py out.html --fragment
                                      → <html>/<head> を含まない本文だけ（埋め込み公開用）
"""

import sys
from pathlib import Path

from flask import render_template

from koppen_quiz.app import create_app, deck_context

ROOT = Path(__file__).parent


def build(full=True):
    app = create_app({"SECRET_KEY": "static-build"})
    css = (ROOT / "koppen_quiz" / "static" / "style.css").read_text(encoding="utf-8")
    with app.test_request_context():
        return render_template("standalone.html", css=css, full=full, **deck_context())


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else ROOT / "docs" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(full="--fragment" not in sys.argv), encoding="utf-8")
    print(f"wrote {out}")
