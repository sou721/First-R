import { EMOTIONS, SUBJECT_LABELS, aggregateEmotionScores } from "./emotions.js";

// CLIP（画像とテキストの対応を学習したモデル）でゼロショット分類を行う。
// ブラウザ内で動くため、画像はサーバーに送信されない。
const TRANSFORMERS_URL = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.5";
const MODEL_ID = "Xenova/clip-vit-base-patch32";
const MAX_IMAGE_SIZE = 512;

const $ = (id) => document.getElementById(id);
const els = {
  video: $("video"),
  photo: $("photo"),
  placeholder: $("placeholder"),
  cameraBtn: $("cameraBtn"),
  shutterBtn: $("shutterBtn"),
  fileInput: $("fileInput"),
  status: $("status"),
  statusText: $("statusText"),
  progressWrap: $("progressWrap"),
  progressBar: $("progressBar"),
  result: $("result"),
  resultEmoji: $("resultEmoji"),
  resultName: $("resultName"),
  resultConfidence: $("resultConfidence"),
  resultMessage: $("resultMessage"),
  resultAdvice: $("resultAdvice"),
  resultWarning: $("resultWarning"),
  bars: $("bars"),
};

let stream = null;
let classifierPromise = null;
let busy = false;

// ---------- モデル読み込み ----------

function loadClassifier() {
  if (!classifierPromise) {
    classifierPromise = (async () => {
      const { pipeline } = await import(TRANSFORMERS_URL);
      const files = new Map();
      return pipeline("zero-shot-image-classification", MODEL_ID, {
        progress_callback: (p) => {
          if (p.status === "progress" && p.total) {
            files.set(p.file, { loaded: p.loaded, total: p.total });
            let loaded = 0;
            let total = 0;
            for (const f of files.values()) {
              loaded += f.loaded;
              total += f.total;
            }
            showStatus("AI モデルを読み込み中…（初回のみ）", loaded / total);
          }
        },
      });
    })().catch((err) => {
      classifierPromise = null; // 次回やり直せるように
      throw err;
    });
  }
  return classifierPromise;
}

// ---------- UI ヘルパー ----------

function showStatus(text, progress = null) {
  els.status.hidden = false;
  els.statusText.textContent = text;
  els.progressWrap.hidden = progress === null;
  if (progress !== null) {
    els.progressBar.style.width = `${Math.round(progress * 100)}%`;
  }
}

function hideStatus() {
  els.status.hidden = true;
}

function setBusy(value) {
  busy = value;
  els.cameraBtn.disabled = value;
  els.shutterBtn.disabled = value;
  els.fileInput.disabled = value;
}

function showPhoto(url) {
  els.photo.src = url;
  els.photo.hidden = false;
  els.video.hidden = true;
  els.placeholder.hidden = true;
}

// ---------- カメラ ----------

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    alert("このブラウザではカメラを直接起動できません。「写真を選ぶ」から撮影してください。");
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 1280 } },
      audio: false,
    });
  } catch (err) {
    console.error(err);
    alert("カメラを起動できませんでした。カメラへのアクセスを許可するか、「写真を選ぶ」をお使いください。");
    return;
  }
  els.video.srcObject = stream;
  els.video.hidden = false;
  els.photo.hidden = true;
  els.placeholder.hidden = true;
  await els.video.play();
  els.cameraBtn.hidden = true;
  els.shutterBtn.hidden = false;
  // 撮影までの間にモデルを先読みしておく
  loadClassifier().catch(() => {});
}

function stopCamera() {
  stream?.getTracks().forEach((t) => t.stop());
  stream = null;
  els.video.srcObject = null;
  els.cameraBtn.hidden = false;
  els.cameraBtn.textContent = "もう一度撮る";
  els.shutterBtn.hidden = true;
}

// 画像要素の内容を縮小してキャンバスに描き、Blob URL を返す
function toScaledImageUrl(source, width, height) {
  const scale = Math.min(1, MAX_IMAGE_SIZE / Math.max(width, height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  canvas.getContext("2d").drawImage(source, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(URL.createObjectURL(blob)) : reject(new Error("画像の変換に失敗しました"))),
      "image/jpeg",
      0.92,
    );
  });
}

async function capture() {
  const { videoWidth: w, videoHeight: h } = els.video;
  if (!w || !h) return;
  const url = await toScaledImageUrl(els.video, w, h);
  stopCamera();
  showPhoto(url);
  await analyze(url);
}

async function handleFile(file) {
  if (!file) return;
  if (stream) stopCamera();
  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    alert("画像を読み込めませんでした。別の写真をお試しください。");
    return;
  }
  const url = await toScaledImageUrl(bitmap, bitmap.width, bitmap.height);
  bitmap.close?.();
  showPhoto(url);
  els.cameraBtn.textContent = "カメラを起動";
  await analyze(url);
}

// ---------- 判定 ----------

async function analyze(imageUrl) {
  if (busy) return;
  setBusy(true);
  els.result.hidden = true;
  try {
    showStatus("AI モデルを準備中…");
    const classifier = await loadClassifier();

    showStatus("表情を読み取り中…");
    const opts = { hypothesis_template: "{}" };
    const subject = await classifier(imageUrl, SUBJECT_LABELS.map((l) => l.prompt), opts);
    const dogScore = subject.find((r) => r.label === SUBJECT_LABELS[0].prompt)?.score ?? 0;

    const prompts = EMOTIONS.flatMap((e) => e.prompts);
    const raw = await classifier(imageUrl, prompts, opts);
    renderResult(aggregateEmotionScores(raw), dogScore);
  } catch (err) {
    console.error(err);
    alert("判定に失敗しました。ネットワーク接続を確認して、もう一度お試しください。\n" + (err?.message ?? ""));
  } finally {
    hideStatus();
    setBusy(false);
  }
}

function renderResult(ranked, dogScore) {
  const top = ranked[0];
  const second = ranked[1];
  const { emotion } = top;

  els.resultEmoji.textContent = emotion.emoji;
  els.resultName.textContent = emotion.name;
  els.resultName.style.color = emotion.color;

  // 1 位と 2 位の差が小さいときは「〜かも」と控えめに表示
  const margin = top.score - second.score;
  const confidenceText = margin > 0.15 ? "確信度：高め" : margin > 0.05 ? "確信度：ふつう" : "確信度：低め（複数の感情が混ざっているかも）";
  els.resultConfidence.textContent = `${Math.round(top.score * 100)}% ・ ${confidenceText}`;
  els.resultMessage.textContent = emotion.message;
  els.resultAdvice.textContent = emotion.advice;

  if (dogScore < 0.5) {
    els.resultWarning.hidden = false;
    els.resultWarning.textContent =
      "⚠️ 犬がはっきり写っていないようです。犬の顔が大きく写るように撮り直すと精度が上がります。";
  } else {
    els.resultWarning.hidden = true;
  }

  els.bars.replaceChildren(
    ...ranked.map(({ emotion: e, score }) => {
      const li = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = `${e.emoji} ${e.name}`;
      const track = document.createElement("div");
      track.className = "bar-track";
      const fill = document.createElement("div");
      fill.className = "bar-fill";
      fill.style.background = e.color;
      fill.style.width = "0%";
      track.append(fill);
      const value = document.createElement("span");
      value.className = "bar-value";
      value.textContent = `${Math.round(score * 100)}%`;
      li.append(label, track, value);
      requestAnimationFrame(() => requestAnimationFrame(() => (fill.style.width = `${score * 100}%`)));
      return li;
    }),
  );

  els.result.hidden = false;
  els.result.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------- イベント ----------

els.cameraBtn.addEventListener("click", startCamera);
els.shutterBtn.addEventListener("click", capture);
els.fileInput.addEventListener("change", (e) => {
  handleFile(e.target.files?.[0]);
  e.target.value = ""; // 同じ写真を再選択できるように
});
