<div align="center">

# Привет, я Drethwut | Egor 👋

**Python-разработчик · компьютерное зрение · локальные LLM и RAG · backend на FastAPI**

Делаю ИИ-системы, которые работают **полностью локально**: на своём железе, без облака и без утечки данных.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-111F68?style=flat-square&logo=yolo&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?style=flat-square&logo=qdrant&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

</div>

---

## 🧭 Коротко обо мне

- 🏭 **Промышленное CV:** оцифровываю показания стрелочных приборов камерами, без врезки в оборудование.
- 📚 **RAG с проверкой фактов:** ответы по технической документации, где каждое утверждение проверяет NLI-модель.
- 🔒 **Приватность по умолчанию:** локальный инференс, никаких исходящих запросов с данными пользователя.
- 📏 **Честные результаты:** в README проектов - метрики, условия замеров и ограничения, а не только обещания.
- 🌱 **Сейчас изучаю:** веб-разработку на Python в курсе X5 Tech - REST и OpenAPI, asyncio, интеграции.

---

## 🚀 Главные проекты

### 🎯 [GaugeVision AI](https://github.com/EGRNEGR/GaugeVisionAI) - компьютерное зрение для ТЭЦ

Сервис считывает показания аналоговых стрелочных приборов (манометры, тягомеры, уровнемеры) с обычных камер
и выводит их на пульт оператора с трендами, уставками и сигнализацией. Работает без интернета.

<a href="https://github.com/EGRNEGR/GaugeVisionAI">
  <img src="https://raw.githubusercontent.com/EGRNEGR/GaugeVisionAI/main/docs/images/dashboard_alarm.png" alt="Пульт оператора GaugeVision AI" width="100%">
</a>

| 📐 Ошибка шкалы | ⚡ Инференс YOLOv8n | 🎯 mAP₅₀ детектора | 📷 Масштаб |
|:---:|:---:|:---:|:---:|
| **0,38 %** макс., 0,11 % средн. | **7,2 мс** на GPU (FP16) | **90,1 %** | **25 камер** на ноутбучной RTX 5060 |

**Стек:** Python · FastAPI (async) · YOLOv8n · OpenCV · WebSocket · SQLite · RTSP / ONVIF / MJPEG

---

### 🔎 [FactRAG-NLI](https://github.com/EGRNEGR/FactRAG-NLI) - локальный RAG с проверкой фактов

Отвечает на вопросы по нормативной и технической документации (PDF, DOCX, TXT, MD), цитирует источники
и проверяет каждую фразу ответа NLI-моделью. Непроверенный текст не выдаётся как готовый ответ.

```text
Документы → BGE-M3 + Qdrant / BM25 → RRF → BGE reranker → Qwen (llama-server) → mDeBERTa NLI → ответ с цитатами
```

| 🎯 Hit@5 (holdout) | 📊 MRR@5 / nDCG@5 | 🚫 Отказ на вопросы вне базы |
|:---:|:---:|:---:|
| **85,7 % → 100 %** после реранкинга | **0,82 / 0,77** | **3 из 3** |

**Стек:** Python · Qdrant · BM25 · BGE-M3 · llama.cpp · Streamlit · FastAPI · CUDA

---

### 🛡️ [AIPrivacy Sentinel](https://github.com/EGRNEGR/IT_Defender) - защита данных в браузере

Расширение для Chrome, Edge и Opera (Manifest V3). Находит в полях ввода email, телефоны, API-ключи и номера карт
и маскирует их до отправки в чат с ИИ. Проверяет ссылки по VirusTotal, PhishTank, OpenPhish и AbuseIPDB
и показывает страницу-предупреждение вместо опасного сайта.

**Стек:** JavaScript · Chrome Extensions API (Manifest V3) · HTML / CSS

---

### 🐍 [backend-basics](https://github.com/EGRNEGR/backend-basics) - веб-разработка на Python (X5 Tech)

Учебные задания курса: структура Python-проекта, CLI на внешних API с ретраями, OpenAPI 3.1 контракт
сервиса «Библиотека», асинхронный загрузчик на httpx и asyncio. Каждое задание оформлено отдельным Pull Request с описанием и проверками.

**Стек:** Python · httpx · asyncio · OpenAPI 3.1 · pytest · Ruff

---

## 🧰 Технологии

| Область | Инструменты |
|---|---|
| **Языки** | Python, JavaScript, TypeScript, HTML/CSS |
| **ML и CV** | PyTorch, YOLOv8 (Ultralytics), OpenCV, CUDA |
| **LLM и RAG** | llama.cpp, Qwen, BGE-M3, BGE reranker, mDeBERTa NLI, Qdrant, BM25 |
| **Backend** | FastAPI, asyncio, httpx, WebSocket, SQLite, OpenAPI |
| **Интерфейсы** | Streamlit, Chrome Extensions (MV3), HTML/JS-дашборды |
| **Качество** | pytest, Ruff, e2e- и браузерные тесты, оценка RAG (Hit@K, MRR, nDCG) |

---

## 🗂️ Все репозитории

| Репозиторий | Что это | Статус |
|---|---|---|
| [GaugeVisionAI](https://github.com/EGRNEGR/GaugeVisionAI) | CV-сервис для стрелочных приборов ТЭЦ | 🟢 активная разработка |
| [FactRAG-NLI](https://github.com/EGRNEGR/FactRAG-NLI) | Локальный RAG с NLI-верификацией | 🟢 рабочая версия |
| [IT_Defender](https://github.com/EGRNEGR/IT_Defender) | Браузерное расширение AIPrivacy Sentinel | 🟡 прототип |
| [backend-basics](https://github.com/EGRNEGR/backend-basics) | Задания курса X5 Tech по Python | 🟢 обновляется |
| [MEDIA](https://github.com/EGRNEGR/MEDIA) | Идея проекта на стыке медицины и ИИ | ⚪ заготовка |

---

## 🤝 Как со мной связаться

Нашли ошибку или есть идея по проекту - открывайте **Issue** в нужном репозитории, я их читаю.
Если проект оказался полезен, поставьте ⭐ - так я понимаю, что развивать дальше.

<div align="center">
  <sub>Профиль обновлён в октябре 2026</sub>
</div>
