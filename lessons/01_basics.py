# レッスン1: Pythonの基本（変数・リスト・if・for・関数）
# 実行方法: python3 lessons/01_basics.py

# --- 1. 変数: 値に名前をつけて保存する ---
name = "AI"          # 文字列 (str)
age = 3              # 整数 (int)
score = 0.95         # 小数 (float)
print(name, age, score)

# --- 2. リスト: 複数の値をまとめる（AIのデータはほぼリスト/配列）---
temperatures = [22.5, 25.0, 19.8, 30.1]
print("最初の値:", temperatures[0])      # 番号は0から始まる
print("データ数:", len(temperatures))

# --- 3. for文: リストの中身を1つずつ処理する ---
total = 0
for t in temperatures:
    total = total + t
average = total / len(temperatures)
print("平均気温:", average)

# --- 4. if文: 条件で分岐する（AIの「判断」の一番素朴な形）---
for t in temperatures:
    if t >= 25:
        print(t, "→ 暑い")
    else:
        print(t, "→ 快適")

# --- 5. 関数: 処理に名前をつけて再利用する ---
def predict(x, weight, bias):
    """とても小さな『AIモデル』: 入力xに重みを掛けて足すだけ"""
    return x * weight + bias

print("予測値:", predict(10, 2.0, 1.0))  # 10*2+1 = 21

# 練習問題:
#  (1) temperatures の最大値を for と if だけで求めてみよう（max()は使わずに）
#  (2) predict の weight と bias を変えて、x=10 のとき 50 を出す組み合わせを探そう
