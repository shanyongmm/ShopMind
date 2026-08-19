const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const configuredApiBaseUrl = window.__API_BASE_URL__;
const API_BASE_URL =
  configuredApiBaseUrl === ""
    ? ""
    : String(configuredApiBaseUrl || DEFAULT_API_BASE_URL).replace(/\/$/, "");
const STREAM_API_URL = `${API_BASE_URL}/api/chat/stream`;
const THREADS_API_URL = `${API_BASE_URL}/api/threads`;

const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const threadList = document.querySelector("#threadList");
const newThreadButton = document.querySelector("#newThreadButton");
const submitButton = form.querySelector("button");
const THREAD_ID_KEY = "customer_agent_thread_id";

let currentThreadId = getStoredThreadId();
let threads = [];

function createThreadId() {
  return crypto.randomUUID();
}

function getStoredThreadId() {
  let threadId = localStorage.getItem(THREAD_ID_KEY);
  if (!threadId) {
    threadId = createThreadId();
    localStorage.setItem(THREAD_ID_KEY, threadId);
  }
  return threadId;
}

function setCurrentThreadId(threadId) {
  currentThreadId = threadId;
  localStorage.setItem(THREAD_ID_KEY, threadId);
  renderThreadList();
}

function clearMessages() {
  messages.innerHTML = "";
}

function showWelcome() {
  clearMessages();
  appendMessage("assistant", "你好，我是智能客服 Agent，请输入你的问题。");
}

function appendMessage(role, text) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = text;
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
  return item;
}

function renderThreadList() {
  threadList.innerHTML = "";
  if (!threads.length) {
    const empty = document.createElement("div");
    empty.className = "thread-empty";
    empty.textContent = "暂无历史会话";
    threadList.appendChild(empty);
    return;
  }

  for (const thread of threads) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `thread-item${thread.thread_id === currentThreadId ? " active" : ""}`;
    item.addEventListener("click", () => loadThread(thread.thread_id));

    const title = document.createElement("div");
    title.className = "thread-title";
    title.textContent = thread.title || thread.thread_id;

    const preview = document.createElement("div");
    preview.className = "thread-preview";
    preview.textContent = thread.last_message || "无消息";

    item.append(title, preview);
    threadList.appendChild(item);
  }
}

async function loadThreads() {
  const response = await fetch(THREADS_API_URL);
  if (!response.ok) {
    throw new Error(`加载会话失败：${response.status}`);
  }
  threads = await response.json();
  renderThreadList();
}

async function loadThread(threadId) {
  setCurrentThreadId(threadId);
  const response = await fetch(`${THREADS_API_URL}/${encodeURIComponent(threadId)}`);
  if (!response.ok) {
    throw new Error(`加载会话详情失败：${response.status}`);
  }
  const detail = await response.json();
  clearMessages();
  for (const message of detail.messages || []) {
    appendMessage(message.role, message.content);
  }
  if (!detail.messages?.length) {
    showWelcome();
  }
  input.focus();
}

newThreadButton.addEventListener("click", () => {
  setCurrentThreadId(createThreadId());
  showWelcome();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendMessage("user", text);
  input.value = "";
  input.disabled = true;
  submitButton.disabled = true;
  newThreadButton.disabled = true;
  const loading = appendMessage("assistant", "思考中...");

  try {
    const response = await fetch(STREAM_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, max_retries: 2, thread_id: currentThreadId }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `请求失败：${response.status}`);
    }

    loading.textContent = "";
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        const event = parseSseEvent(part);
        if (!event) continue;

        if (event.type === "node" && !loading.textContent) {
          loading.textContent = "正在处理...";
        }

        if (event.type === "token") {
          if (loading.textContent === "正在处理...") {
            loading.textContent = "";
          }
          loading.textContent += event.data.token || "";
          messages.scrollTop = messages.scrollHeight;
        }

        if (event.type === "done" && !loading.textContent) {
          loading.textContent = event.data.answer || "没有返回内容。";
        }
      }
    }

    if (!loading.textContent) {
      loading.textContent = "没有返回内容。";
    }
    await loadThreads();
  } catch (error) {
    loading.className = "message error";
    loading.textContent = error.message;
  } finally {
    input.disabled = false;
    submitButton.disabled = false;
    newThreadButton.disabled = false;
    input.focus();
  }
});

function parseSseEvent(raw) {
  const lines = raw.split("\n");
  let type = "message";
  let data = "";

  for (const line of lines) {
    if (line.startsWith("event:")) {
      type = line.slice(6).trim();
    }
    if (line.startsWith("data:")) {
      data += line.slice(5).trim();
    }
  }

  if (!data) return null;

  try {
    return { type, data: JSON.parse(data) };
  } catch {
    return { type, data: { text: data } };
  }
}

async function initialize() {
  await loadThreads();
  const currentThread = threads.find((thread) => thread.thread_id === currentThreadId);
  if (currentThread) {
    await loadThread(currentThreadId);
  } else {
    showWelcome();
  }
}

initialize().catch((error) => {
  threadList.innerHTML = "";
  const item = document.createElement("div");
  item.className = "thread-empty";
  item.textContent = error.message;
  threadList.appendChild(item);
});
