import { request, ENDPOINTS } from "./utils.js";

const MAX_CACHE_SIZE = 50;
const audioCache = new Map(); 

function cacheSet(key, value) {
  if (audioCache.size >= MAX_CACHE_SIZE && !audioCache.has(key)) {
    const oldestKey = audioCache.keys().next().value;
    const oldestValue = audioCache.get(oldestKey);

    if (typeof oldestValue === 'string') {
      URL.revokeObjectURL(oldestValue);
    } else if (oldestValue?.then) {
      oldestValue.then(url => URL.revokeObjectURL(url)).catch(() => {});
    }

    audioCache.delete(oldestKey);
  }
  audioCache.set(key, value);
}

function hashText(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i);
  }
  return (hash >>> 0).toString(36);
}

export function fetchAudio(text) {
  const key = hashText(text);
  if (audioCache.has(key)) return audioCache.get(key);
  
  const promise = fetch(ENDPOINTS.PIPER, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text }),
    })
      .then(res => res.blob())
      .then(blob => URL.createObjectURL(blob));

  cacheSet(key, promise);
  return promise;
}