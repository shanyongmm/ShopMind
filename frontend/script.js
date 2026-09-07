const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const configuredApiBaseUrl = window.__API_BASE_URL__;
const API_BASE_URL =
  configuredApiBaseUrl === ""
    ? ""
    : String(configuredApiBaseUrl || DEFAULT_API_BASE_URL).replace(/\/$/, "");
const STREAM_API_URL = `${API_BASE_URL}/api/chat/stream`;
const THREADS_API_URL = `${API_BASE_URL}/api/threads`;

const THREAD_ID_KEY = "customer_agent_thread_id";
const INITIAL_MESSAGE = "你好，我是 ShopMind 智能客服，请输入你的问题。";
const THINKING_MESSAGE = "正在处理...";
const EMPTY_ANSWER_MESSAGE = "没有返回内容。";
const MAX_THREAD_TITLE_LENGTH = 34;

const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const threadList = document.querySelector("#threadList");
const threadSearchInput = document.querySelector("#threadSearchInput");
const newThreadButton = document.querySelector("#newThreadButton");
const javaTriggerButton = document.querySelector("#javaTriggerButton");
const submitButton = document.querySelector("#submitButton");
const connectionStatus = document.querySelector("#connectionStatus");
const connectionStatusText = connectionStatus.querySelector(".status-text");

let currentThreadId = getStoredThreadId();
let threads = [];
let isBusy = false;

function createThreadId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `thread_${Date.now()}_${Math.random().toString(16).slice(2)}`;
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

function setConnectionStatus(state, text) {
  connectionStatus.dataset.state = state;
  connectionStatusText.textContent = text;
}

function setBusy(nextBusy) {
  isBusy = nextBusy;
  input.disabled = nextBusy;
  newThreadButton.disabled = nextBusy;
  javaTriggerButton.disabled = nextBusy;
  updateSubmitState();
}

function updateSubmitState() {
  submitButton.disabled = isBusy || input.value.trim().length === 0;
}

function autoResizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 168)}px`;
}

function clearMessages() {
  messages.innerHTML = "";
}

function showWelcome() {
  clearMessages();
  appendMessage("assistant", INITIAL_MESSAGE);
}

function getRoleMark(role) {
  if (role === "user") return "我";
  if (role === "error") return "!";
  if (role === "system") return "i";
  return "S";
}

function normalizeRole(role) {
  return ["assistant", "user", "system", "error"].includes(role) ? role : "assistant";
}

function appendMessage(role, text, options = {}) {
  const normalizedRole = normalizeRole(role);
  const item = document.createElement("article");
  item.className = `message ${normalizedRole}`;
  if (options.loading) {
    item.classList.add("loading");
  }

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = getRoleMark(normalizedRole);

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  const content = document.createElement("div");
  content.className = "message-content";
  content.textContent = text || "";

  bubble.appendChild(content);
  item.append(avatar, bubble);
  messages.appendChild(item);
  scrollMessagesToBottom();
  return item;
}

function setMessageText(messageElement, text) {
  const content = messageElement.querySelector(".message-content");
  content.textContent = text || "";
  scrollMessagesToBottom();
}

function setMessageRole(messageElement, role) {
  const normalizedRole = normalizeRole(role);
  messageElement.className = `message ${normalizedRole}`;
  const avatar = messageElement.querySelector(".message-avatar");
  avatar.textContent = getRoleMark(normalizedRole);
}

function scrollMessagesToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function compactText(value, fallback = "") {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  return text || fallback;
}

function trimTitle(value) {
  const text = compactText(value);
  if (text.length <= MAX_THREAD_TITLE_LENGTH) {
    return text;
  }
  return `${text.slice(0, MAX_THREAD_TITLE_LENGTH)}...`;
}

function trimPreview(value) {
  const text = compactText(value, "无消息");
  if (text.length <= 72) {
    return text;
  }
  return `${text.slice(0, 72)}...`;
}

function formatTime(value) {
  if (!value) {
    return "本地会话";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "本地会话";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function getVisibleThreads() {
  const query = threadSearchInput.value.trim().toLowerCase();
  if (!query) {
    return threads;
  }

  return threads.filter((thread) => {
    const searchable = [
      thread.title,
      thread.last_message,
      thread.thread_id,
      thread.created_at,
      thread.updated_at,
    ]
      .map((value) => String(value || "").toLowerCase())
      .join(" ");
    return searchable.includes(query);
  });
}

function renderThreadNotice(text, type = "empty") {
  threadList.innerHTML = "";
  const item = document.createElement("div");
  item.className = type === "error" ? "thread-error" : "thread-empty";
  item.textContent = text;
  threadList.appendChild(item);
}

function renderThreadList() {
  threadList.innerHTML = "";
  const visibleThreads = getVisibleThreads();

  if (!threads.length) {
    renderThreadNotice("暂无历史会话");
    return;
  }

  if (!visibleThreads.length) {
    renderThreadNotice("没有匹配的会话");
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const thread of visibleThreads) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `thread-item${thread.thread_id === currentThreadId ? " active" : ""}`;
    item.addEventListener("click", () => loadThread(thread.thread_id));

    const title = document.createElement("div");
    title.className = "thread-title";
    title.textContent = trimTitle(thread.title || thread.last_message || thread.thread_id);

    const meta = document.createElement("div");
    meta.className = "thread-meta";
    meta.textContent = `${formatTime(thread.updated_at)} · ${trimPreview(thread.last_message)}`;

    item.append(title, meta);
    fragment.appendChild(item);
  }
  threadList.appendChild(fragment);
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `请求失败：${response.status}`);
  }
  return response.json();
}

async function loadThreads(options = {}) {
  if (!options.silent) {
    renderThreadNotice("正在加载...");
  }
  threads = await fetchJson(THREADS_API_URL);
  renderThreadList();
  setConnectionStatus("ok", "已连接");
}

async function loadThread(threadId) {
  setCurrentThreadId(threadId);
  clearMessages();
  const loading = appendMessage("system", "正在加载...");
  setConnectionStatus("busy", "加载中");

  try {
    const detail = await fetchJson(`${THREADS_API_URL}/${encodeURIComponent(threadId)}`);
    clearMessages();
    for (const message of detail.messages || []) {
      appendMessage(message.role, message.content);
    }
    if (!detail.messages?.length) {
      showWelcome();
    }
    setConnectionStatus("ok", "已连接");
  } catch (error) {
    setMessageRole(loading, "error");
    setMessageText(loading, error.message);
    setConnectionStatus("error", "连接异常");
  } finally {
    input.focus();
  }
}

function parseSseEvent(raw) {
  const lines = raw.split(/\r?\n/);
  let type = "message";
  const dataLines = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      type = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).replace(/^ /, ""));
    }
  }

  const data = dataLines.join("\n");
  if (!data) return null;

  try {
    return { type, data: JSON.parse(data) };
  } catch {
    return { type, data: { text: data } };
  }
}

function updateStreamingMessage(messageElement, event, state) {
  if (event.type === "error") {
    const message = event.data.message || event.data.error || "服务异常，请稍后重试。";
    state.hasContent = true;
    state.error = true;
    messageElement.classList.remove("loading");
    setMessageRole(messageElement, "error");
    setMessageText(messageElement, message);
    return;
  }

  if (event.type === "node" && !state.hasContent) {
    setMessageText(messageElement, THINKING_MESSAGE);
    return;
  }

  if (event.type === "token") {
    const token = event.data.token || event.data.text || "";
    if (!token) return;
    state.hasContent = true;
    state.answer += token;
    messageElement.classList.remove("loading");
    setMessageText(messageElement, state.answer);
    return;
  }

  if (event.type === "done") {
    if (state.error) {
      return;
    }
    const answer = event.data.answer || state.answer || EMPTY_ANSWER_MESSAGE;
    state.hasContent = true;
    messageElement.classList.remove("loading");
    setMessageText(messageElement, answer);
  }
}

async function sendMessage(text) {
  appendMessage("user", text);
  input.value = "";
  autoResizeInput();
  setBusy(true);
  setConnectionStatus("busy", "处理中");

  const assistantMessage = appendMessage("assistant", THINKING_MESSAGE, { loading: true });
  const streamState = { answer: "", hasContent: false };

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

    if (!response.body) {
      throw new Error("当前浏览器不支持流式响应。");
    }

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
        if (event) {
          updateStreamingMessage(assistantMessage, event, streamState);
        }
      }
    }

    buffer += decoder.decode();
    const finalEvent = parseSseEvent(buffer);
    if (finalEvent) {
      updateStreamingMessage(assistantMessage, finalEvent, streamState);
    }

    assistantMessage.classList.remove("loading");
    if (!streamState.hasContent) {
      setMessageText(assistantMessage, EMPTY_ANSWER_MESSAGE);
    }

    if (streamState.error) {
      await loadThreads({ silent: true }).catch(() => {});
      setConnectionStatus("error", "服务异常");
    } else {
      try {
        await loadThreads({ silent: true });
        setConnectionStatus("ok", "已连接");
      } catch {
        setConnectionStatus("error", "连接异常");
      }
    }
  } catch (error) {
    setMessageRole(assistantMessage, "error");
    assistantMessage.classList.remove("loading");
    setMessageText(assistantMessage, error.message);
    setConnectionStatus("error", "连接异常");
  } finally {
    setBusy(false);
    input.focus();
  }
}

newThreadButton.addEventListener("click", () => {
  setCurrentThreadId(createThreadId());
  showWelcome();
  setConnectionStatus("ok", "已连接");
  input.focus();
});

javaTriggerButton.addEventListener("click", async () => {
  const text = javaTriggerButton.dataset.message || "最近热门的商品有什么？";
  if (isBusy) return;
  input.value = text;
  autoResizeInput();
  updateSubmitState();
  await sendMessage(text);
});

threadSearchInput.addEventListener("input", renderThreadList);

input.addEventListener("input", () => {
  autoResizeInput();
  updateSubmitState();
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || isBusy) return;
  await sendMessage(text);
});

async function initialize() {
  setConnectionStatus("busy", "连接中");
  updateSubmitState();
  autoResizeInput();

  try {
    await loadThreads();
    const currentThread = threads.find((thread) => thread.thread_id === currentThreadId);
    if (currentThread) {
      await loadThread(currentThreadId);
    } else {
      showWelcome();
    }
  } catch (error) {
    renderThreadNotice(error.message, "error");
    showWelcome();
    setConnectionStatus("error", "连接异常");
  }
}

initialize();
