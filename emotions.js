// 判定する感情の定義。
// prompts は CLIP によるゼロショット分類に使う英語の説明文。
// 1 つの感情に複数の言い回しを用意し、スコアを合算して精度のブレを抑える。
export const EMOTIONS = [
  {
    id: "happy",
    emoji: "😊",
    name: "うれしい",
    color: "#f2a93b",
    message: "ご機嫌です！口元がゆるみ、表情がやわらかく見えます。",
    advice: "たくさん褒めて、この時間を一緒に楽しみましょう。",
    prompts: [
      "a photo of a happy dog with an open mouth and relaxed tongue",
      "a photo of a smiling dog",
      "a photo of a joyful cheerful dog",
    ],
  },
  {
    id: "relaxed",
    emoji: "😌",
    name: "リラックス",
    color: "#5bb38a",
    message: "落ち着いて安心している様子です。",
    advice: "そっと見守ってあげましょう。静かな環境がおすすめです。",
    prompts: [
      "a photo of a calm relaxed dog",
      "a photo of a peaceful content dog with soft eyes",
      "a photo of a dog lying down comfortably",
    ],
  },
  {
    id: "excited",
    emoji: "🤩",
    name: "わくわく",
    color: "#e4663d",
    message: "テンションが上がっていて、遊びたい気分のようです。",
    advice: "おもちゃや散歩でエネルギーを発散させてあげましょう。",
    prompts: [
      "a photo of an excited playful dog",
      "a photo of a dog eager to play",
      "a photo of an energetic dog running and jumping",
    ],
  },
  {
    id: "angry",
    emoji: "😠",
    name: "怒り・警戒",
    color: "#c8413a",
    message: "警戒したり、怒っている可能性があります。",
    advice: "無理に近づかず、刺激の原因を取り除いて距離をとりましょう。",
    prompts: [
      "a photo of an angry dog showing its teeth",
      "a photo of an aggressive growling dog",
      "a photo of a snarling dog with wrinkled nose",
    ],
  },
  {
    id: "fear",
    emoji: "😨",
    name: "不安・こわい",
    color: "#7c6bc4",
    message: "不安や怖さを感じているかもしれません。",
    advice: "大きな音や見知らぬものから離し、安心できる場所を用意しましょう。",
    prompts: [
      "a photo of a scared dog with ears pinned back",
      "a photo of a fearful anxious dog",
      "a photo of a nervous dog showing the whites of its eyes",
    ],
  },
  {
    id: "sad",
    emoji: "😢",
    name: "しょんぼり",
    color: "#4a86c5",
    message: "元気がなく、さみしそうに見えます。",
    advice: "声をかけたり、なでたりしてスキンシップをとってみましょう。続く場合は体調も確認を。",
    prompts: [
      "a photo of a sad dog",
      "a photo of a lonely dog with droopy eyes",
      "a photo of a dog with sad puppy eyes looking up",
    ],
  },
  {
    id: "sleepy",
    emoji: "😴",
    name: "ねむい",
    color: "#8a95a5",
    message: "眠そう、または休んでいるところのようです。",
    advice: "ゆっくり休ませてあげましょう。",
    prompts: [
      "a photo of a sleepy dog",
      "a photo of a dog sleeping with eyes closed",
      "a photo of a tired yawning dog",
    ],
  },
];

// 写真に犬が写っているかを確認するためのラベル。
export const SUBJECT_LABELS = [
  { id: "dog", prompt: "a photo of a dog" },
  { id: "cat", prompt: "a photo of a cat" },
  { id: "person", prompt: "a photo of a person" },
  { id: "other", prompt: "a photo of an object, food, or scenery" },
];

/**
 * ゼロショット分類の結果（{label, score}[]）を感情ごとのスコアに集計する。
 * 戻り値は確率の高い順に並んだ配列。
 */
export function aggregateEmotionScores(results) {
  const byPrompt = new Map(results.map((r) => [r.label, r.score]));
  const totals = EMOTIONS.map((emotion) => ({
    emotion,
    score: emotion.prompts.reduce((sum, p) => sum + (byPrompt.get(p) ?? 0), 0),
  }));
  const sum = totals.reduce((s, t) => s + t.score, 0) || 1;
  return totals
    .map((t) => ({ ...t, score: t.score / sum }))
    .sort((a, b) => b.score - a.score);
}
