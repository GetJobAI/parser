# Пояснення до діаграми `component_resume_parser.puml`

## Що показує ця діаграма

Це component diagram, яка показує модульну архітектуру сервісу.

Вона відповідає на питання:

- з яких великих частин складається сервіс;
- які підсистеми є всередині;
- як вони взаємодіють між собою.

---

## Основні шари

На діаграмі виділено чотири основні шари:

- `API Layer`
- `Core Layer`
- `Persistence Layer`
- `Contracts Layer`

Окремо показана база даних `PostgreSQL`.

---

## API Layer

У цей шар входять:

- `FastAPI App`
- `Resumes API`
- `Settings`

### Їх роль

- `FastAPI App` запускає сервіс і ініціалізує залежності;
- `Resumes API` містить HTTP-endpoint-и;
- `Settings` зчитує конфігурацію.

Це зовнішня точка входу в систему.

---

## Core Layer

Це центральний шар бізнес-логіки.

У ньому є:

- `ResumePipeline`
- `Extraction`
- `Preprocess and Detection`
- `Section Parsers`
- `Quality Control`

### Роль `ResumePipeline`

`ResumePipeline` є оркестратором.  
Він координує:

- extraction;
- preprocess;
- detection;
- parsing;
- quality checking.

### Інші підсистеми

- `Extraction` відповідає за витяг тексту;
- `Preprocess and Detection` готує текст і знаходить секції;
- `Section Parsers` розбирає зміст окремих секцій;
- `Quality Control` виконує fallback і контроль якості.

---

## Persistence Layer

Тут знаходяться:

- `ResumeRepository`
- `Database Client`

### Їх роль

- `ResumeRepository` працює з таблицею `resumes`;
- `Database Client` керує підключенням до PostgreSQL.

---

## Contracts Layer

У цьому шарі зібрані моделі даних:

- `ResumeContent`
- `ParseResumeResponse`
- `ContentContractResponse`

### Для чого вони потрібні

- `ResumeContent` описує, що саме зберігається;
- `ParseResumeResponse` описує HTTP-відповідь;
- `ContentContractResponse` описує контракт для фронтенду.

---

## Як читати зв’язки

### Зв’язки від `Main`

`FastAPI App`:

- завантажує конфігурацію;
- ініціалізує pipeline;
- за наявності БД ініціалізує repository.

### Зв’язки від `API`

API:

- звертається до repository для створення й оновлення запису;
- викликає pipeline для парсингу;
- повертає або parse summary, або contract response.

### Зв’язки від `Pipeline`

Pipeline:

- викликає extraction;
- викликає preprocess and detection;
- передає дані в section parsers;
- запускає quality subsystem;
- формує `ResumeContent`.

### Зв’язки persistence layer

Repository:

- використовує database client;
- записує `ResumeContent` у PostgreSQL.

---

## Як пояснювати цю діаграму на захисті

Можна сказати так:

> Компонентна діаграма показує модульну архітектуру сервісу. Сервіс поділено на чотири шари: API, ядро бізнес-логіки, persistence і контракти даних. Центральним компонентом є `ResumePipeline`, який координує extraction, обробку тексту, парсинг секцій і оцінку якості результату.
