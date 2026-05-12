# Resume Parser Service: Повне пояснення сервісу

## 1. Призначення сервісу

Цей сервіс реалізує MVP мікросервісу для парсингу резюме. Його головне завдання:

- прийняти файл резюме через HTTP;
- підтримати формати `PDF` і `DOCX`;
- витягнути текст;
- відновити логічну структуру документа;
- розкласти знайдені дані по секціях;
- зберегти структурований результат у PostgreSQL;
- не зберігати оригінальний файл як постійні бізнес-дані.

Ідеологічно цей сервіс побудований як **rules-first parser**, тобто він спирається не на AI, а на набір детерміністичних правил, евристик, регулярних виразів, fuzzy matching і просту структурну логіку.

Це важливо з двох причин:

1. Поведінка сервісу більш передбачувана.
2. Легше пояснити, чому конкретне поле було або не було розпізнане.

Сервіс не намагається "покращити" резюме, не переписує текст, не нормалізує навички агресивно і не вигадує відсутні дані. Якщо інформація неясна, вона або лишається у `raw_text`, або потрапляє до `unassigned_blocks`.

---

## 2. Місце сервісу в архітектурі

Цей модуль задуманий як частина мікросервісної системи, але для MVP працює як окремий HTTP-сервіс.

Перед ним стоїть gateway. Gateway:

- займається аутентифікацією;
- вже знає, хто користувач;
- додає `user_id` у header запиту.

Сам parser-service довіряє gateway і не перевіряє автентифікацію самостійно. Тобто сервіс припускає, що trusted header уже правильний.

З боку БД сервіс працює з уже існуючою таблицею:

```sql
CREATE TABLE public.resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT current_setting('auth.user_id', TRUE),
    content JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Важливе обмеження: нові колонки не додаються. Усе, що стосується стану парсингу, помилок, warning-ів і результату, зберігається **всередині `content JSONB`**.

---

## 3. Загальна логіка роботи

На високому рівні сервіс працює так:

1. Клієнт надсилає файл на `POST /resumes/parse`.
2. Сервіс перевіряє header із `user_id`.
3. Сервіс перевіряє тип файлу.
4. У БД одразу створюється рядок `resume` зі статусом `processing`.
5. Далі запускається парсинг:
   - extraction;
   - preprocess;
   - layout analysis;
   - section detection;
   - section parsing;
   - fallback;
   - quality checking.
6. Фінальний результат записується в `content`.
7. API повертає короткий summary про парсинг.

Ця схема дозволяє:

- відслідковувати статус обробки;
- навіть при помилці зберігати частковий результат;
- не губити дані;
- відділити HTTP-шар від бізнес-логіки.

---

## 4. Структура проєкту

### Кореневі файли

#### `pyproject.toml`

Описує пакет, залежності, dev-залежності та конфігурацію тестів.

Основні залежності:

- `fastapi` — HTTP API;
- `asyncpg` — робота з PostgreSQL;
- `pydantic`, `pydantic-settings` — моделі даних і конфіг;
- `PyMuPDF` — extraction для PDF;
- `python-docx` — extraction для DOCX;
- `rapidfuzz` — fuzzy matching section headers;
- `uvicorn` — запуск FastAPI;
- `pytest` — тести.

#### `Makefile`

Містить зручні локальні команди. Зараз головна команда:

```bash
make parse-pdf FILE=../some_cv.pdf
```

Вона запускає локальний парсер без БД через `scripts/parse_pdf.py`.

#### `LICENSE`

Файл ліцензії проєкту.

---

## 5. Точка входу та конфігурація

### `app/main.py`

Це точка входу FastAPI.

Вона:

- створює `FastAPI` application;
- під час `lifespan` ініціалізує:
  - `Settings`;
  - `Database`;
  - `ResumeRepository`;
  - `ResumePipeline`;
- кладе об'єкти у `app.state`;
- підключає router із `app/api/resumes.py`.

Ідея `lifespan` тут правильна для сервісу:

- БД відкривається один раз при старті;
- пул підключень живе разом із застосунком;
- при shutdown ресурс акуратно закривається.

### `app/config.py`

Описує конфігураційні параметри через `pydantic-settings`.

Основні поля:

- `database_url`
- `user_id_header`, дефолтно `X-User-Id`
- `parser_version`, дефолтно `v1`

Чому це добре:

- сервіс легко переноситься між середовищами;
- немає хардкоду секретів чи адреси БД;
- версію парсера можна фіксувати у збереженому результаті.

---

## 6. HTTP-рівень

### `app/api/resumes.py`

Це основний API endpoint:

```http
POST /resumes/parse
```

#### Що він приймає

- `multipart/form-data`
- файл у полі `file`
- trusted header із `user_id`

#### Що він робить

1. Читає `user_id` з header.
2. Перевіряє наявність файлу.
3. Перевіряє розширення:
   - `.pdf`
   - `.docx`
4. Перевіряє MIME type.
5. Створює початковий `ResumeContent` зі статусом `processing`.
6. Одразу вставляє запис у БД.
7. Зчитує байти файлу в пам'ять.
8. Якщо файл порожній:
   - ставить `failed`;
   - записує помилку в `content.meta`;
   - оновлює рядок у БД;
   - повертає `400`.
9. Якщо файл непорожній:
   - запускає `ResumePipeline.parse(...)`;
   - отримує фінальний `content` і `quality_report`;
   - оновлює БД;
   - повертає `ParseResumeResponse`.

#### Чому це хороше рішення

- Рядок у БД створюється до парсингу, тобто процес можна трасувати.
- Якщо щось падає, у БД все одно залишається інформація про спробу обробки.
- API-шар не містить логіки самого парсингу, а тільки orchestration.

---

## 7. Шар роботи з базою

### `app/db/client.py`

Має клас `Database`, який інкапсулює створення і закриття `asyncpg.Pool`.

Його роль:

- відкрити пул з'єднань;
- дати доступ до pool через property;
- контролювати lifecycle.

Це не repository і не ORM. Це саме низькорівнева інфраструктурна обгортка.

### `app/db/repository.py`

Містить `ResumeRepository`, який працює з таблицею `public.resumes`.

Методи:

- `create_resume(user_id, content)` — створює новий рядок;
- `update_content(resume_id, content)` — оновлює `content` і `updated_at`.

Чому repository корисний:

- SQL ізольований від API і pipeline;
- легше тестувати логіку окремо;
- при зміні persistence-шару не доведеться чіпати parser pipeline.

---

## 8. Контракти даних

### `app/schemas/content.py`

Це один із найважливіших файлів у проєкті.

Він задає весь внутрішній контракт даних.

#### `TextBlock`

Базова внутрішня одиниця тексту:

- `text`
- `page`
- `order`
- координати `x0`, `y0`, `x1`, `y1`

Це дуже важливе архітектурне рішення. Сервіс працює не з одним giant string, а з набором блоків. Саме завдяки цьому можна:

- аналізувати layout;
- відновлювати порядок читання;
- будувати секції;
- не втрачати зв'язок між порядком і текстом.

#### `ResumeMeta`

Містить технічну інформацію про процес:

- `original_filename`
- `mime_type`
- `parser_version`
- `parse_status`
- `parse_error`
- `warnings`
- `fallback_used`
- `ocr_used`
- `partial_parse`
- `layout_detected`
- `extraction_method`

Це допомагає не тільки зберегти результат, а й пояснити, **як саме** він був отриманий.

#### `ResumeContent`

Це фінальний JSON-контракт, який записується в БД.

Секції:

- `meta`
- `contact`
- `summary`
- `experience`
- `education`
- `skills`
- `certifications`
- `languages`
- `projects`
- `unassigned_blocks`

#### Інші моделі

- `ContactInfo`
- `SummarySection`
- `ExperienceEntry`
- `EducationEntry`
- `GenericListSection`
- `ExtractionResult`
- `SectionMatch`

Тобто файл одночасно задає:

- формат проміжних даних;
- формат фінального результату;
- формат деяких службових структур.

### `app/schemas/response.py`

Описує компактну модель HTTP-відповіді:

- `resume_id`
- `partial_parse`
- `warnings`
- `major_sections_found`

Тобто API не повертає весь `content`, а повертає summary. Це нормально для сервісної архітектури.

---

## 9. Extractors

### Теорія

Початковий промпт вимагав окремі шляхи для PDF і DOCX.

Чому це важливо:

- `PDF` і `DOCX` мають різну природу;
- `DOCX` вже логічно структурований, а `PDF` частіше є layout-документом;
- конвертація DOCX в PDF могла б зламати структуру;
- extraction краще робити native-інструментами для кожного формату.

### `app/extractors/pdf_extractor.py`

Використовує `fitz` (`PyMuPDF`).

#### Алгоритм

1. Відкриває PDF з `file_bytes`.
2. Ітерується по сторінках.
3. Для кожної сторінки бере `page.get_text("blocks")`.
4. Сортує блоки по координатах:
   - спочатку `y`
   - потім `x`
5. Для кожного блоку:
   - чистить whitespace;
   - відкидає порожні;
   - створює `TextBlock` з координатами та порядком.
6. Підраховує кількість корисних символів.
7. Якщо тексту мало, ставить warning, що може знадобитися OCR.

#### Чому це корисно

- зберігаються координати;
- можна відновлювати layout;
- є hook для майбутнього OCR.

### `app/extractors/docx_extractor.py`

Використовує `python-docx`.

#### Алгоритм

1. Відкриває документ через `Document(BytesIO(file_bytes))`.
2. Читає всі `paragraphs`.
3. Читає всі `tables`.
4. Для кожного непорожнього тексту створює `TextBlock`.
5. Повертає `ExtractionResult`.

#### Обмеження

- координат як у PDF тут немає;
- layout detection для DOCX не такий сильний;
- але сам формат зазвичай уже краще структурований.

---

## 10. Preprocess

### Навіщо preprocess потрібен

Після extraction текст ще не готовий до логічного парсингу. У реальних CV часто є:

- зайві пробіли;
- повтори;
- bullets у дивному вигляді;
- злиті заголовки;
- шматки header/footer;
- broken lines;
- змішані шматки різних секцій в одному block.

Саме тому потрібен окремий preprocess-шар.

### `app/preprocess/cleaner.py`

Це один із найважливіших технічних файлів.

#### Основна функція

`preprocess_blocks(blocks)` приймає список `TextBlock` і повертає очищені блоки.

#### Що робить cleaner

1. Нормалізує whitespace.
2. Нормалізує bullets.
3. Викидає порожні фрагменти.
4. Видаляє consecutive duplicates.
5. Видаляє повторювані header/footer блоки між сторінками.
6. Акуратно склеює очевидно розірвані рядки.
7. Розбиває великі merged blocks:
   - embedded section headers;
   - inline bullets;
   - змішані bullet/job-entry рядки.

#### Деталі алгоритмів

##### `_clean_block`

Бере один `TextBlock`, чистить текст і може повернути **не один**, а кілька нових block-ів.

Це важливий момент: після покращень cleaner став не просто "очищувачем", а ще й "block splitter".

##### `_split_embedded_section_headers`

Якщо в одному extracted block сидять кілька логічних заголовків, наприклад:

`SUMMARY ... EXPERIENCE ... EDUCATION ...`

то cleaner намагається розділити це на окремі шматки.

##### `_split_leading_section_headers`

Якщо block починається зі слова-секції:

`SUMMARY Master carpenter ...`

він розбивається на:

- `SUMMARY`
- `Master carpenter ...`

Це сильно допомагає `section_detector`.

##### `_split_inline_bullets`

Якщо всередині блоку є `•`, cleaner розбиває його на окремі bullet-елементи.

##### `_split_mixed_bullet_and_entry_lines`

Це спеціальна евристика для проблемного PDF-кейсу, коли в одному рядку зшиті:

- кінець bullet-пункту;
- дата;
- початок наступної job entry.

##### `_remove_repeated_headers_footers`

Для багатосторінкових документів дивиться повтори верхніх і нижніх блоків між сторінками і безпечно їх прибирає.

##### `_join_obvious_wraps`

Склеює тільки ті рядки, які з великою ймовірністю є продовженням попереднього.

Cleaner спеціально написаний обережно: краще недосклеїти, ніж зруйнувати структуру документа.

### `app/preprocess/layout.py`

Цей модуль аналізує layout документа.

#### Навіщо це потрібно

У PDF можливі двоколонкові макети. Якщо читати їх просто зверху вниз, текст секцій переплутається.

#### Алгоритм

1. Групує блоки по сторінках.
2. Якщо координат нема — одразу повертає `single_column`.
3. Якщо координати є:
   - аналізує center points блоків;
   - оцінює, чи є лівий і правий стовпці;
   - якщо layout схожий на two-column, ділить сторінку на дві зони;
   - інакше читає як single-column.
4. Після reorder переприсвоює `order`.

#### Перевага

Навіть проста двоколонкова евристика вже значно краща, ніж сліпий linear read.

---

## 11. Detection: секції документа

### `app/detectors/section_detector.py`

Це модуль, який відповідає за знаходження заголовків секцій.

#### Підтримувані секції

- contact
- summary
- experience
- education
- skills
- certifications
- languages
- projects

#### Підхід

1. Для кожного `TextBlock` перевіряється, чи він схожий на header-кандидат.
2. Якщо схожий:
   - текст нормалізується;
   - порівнюється зі словником section synonyms;
   - використовується fuzzy matching.
3. Якщо score високий, створюється `SectionMatch`.

#### `_is_candidate_header`

Блок вважається кандидатом на header, якщо:

- він короткий;
- не надто довгий за кількістю слів;
- не містить URL чи email;
- не містить цифр;
- виглядає як standalone line.

#### Fuzzy matching

Для match використовується `RapidFuzz`.

Це дозволяє ловити typo:

- `Experiance`
- `Ekucation`
- `Skils`

#### Значення для системи

Section detection — це міст між "просто текстом" і "структурованим резюме".

### `app/detectors/boundaries.py`

Після того, як заголовки знайдені, треба зрозуміти, які блоки належать якій секції.

#### Алгоритм

1. Сортує знайдені секції по `block_order`.
2. Усе до першого заголовка вважає header area.
3. Вміст секції — це всі block-и між поточним header і наступним.
4. Повертає `SectionedDocument`:
   - `header_blocks`
   - `sections`
   - `unassigned_blocks`

#### Значення

Без цього модуля не було б із чого годувати конкретні section parsers.

---

## 12. Parsers секцій

### Загальна ідея

Після того, як document уже розбитий на секції, кожну секцію треба парсити своїм окремим алгоритмом.

Це правильне архітектурне рішення, бо:

- логіка contact сильно відрізняється від experience;
- summary простий, experience складний;
- skills list-like, а education напівструктурована.

### `app/parsers/contact_parser.py`

#### Завдання

Розпізнати:

- `full_name`
- `email`
- `phone`
- `location`
- `linkedin`
- `github`
- `website`

#### Алгоритм

1. Береться текст header area.
2. Шукається:
   - email regex-ом;
   - phone regex-ом;
   - URLs;
3. URL-адреси класифікуються як:
   - linkedin
   - github
   - website
4. `full_name` шукається по верхніх рядках:
   - 2-4 слова;
   - без цифр;
   - без URL/email;
   - схоже на ім'я.
5. `location` шукається евристично.

#### Особливість

Parser добре працює навіть для "іконкових" контактних рядків, бо він дивиться на самі значення, а не на лейбли.

### `app/parsers/summary_parser.py`

Це найпростіший parser.

Він просто:

- збирає section blocks у рядок;
- кладе його у `SummarySection.raw_text`.

І це правильний вибір для MVP, бо summary рідко потребує глибокого структурного розбору.

### `app/parsers/experience_parser.py`

Це найскладніший parser у проєкті.

#### Завдання

Для секції experience треба:

- поділити її на окремі job entries;
- для кожної entry спробувати витягнути:
  - `title`
  - `company`
  - `start_date`
  - `end_date`
  - `date_range_raw`
  - `location`
  - `bullets`
  - `description_raw`
  - `raw_text`

#### Етап 1. Перетворення section blocks у lines

Беруться тексти всіх непорожніх блоків.

#### Етап 2. `_split_entries`

Секція ділиться на записи.

Для старту нової job entry використовуються сигнали:

- знайдений date range;
- поточна група вже має dates;
- або вже має bullets;
- або рядок виглядає як новий short header.

Це евристика, а не строгий парсер.

#### Етап 3. `_parse_entry`

Для кожного entry:

1. Збирається `raw_text`.
2. Виділяються `header_lines`.
3. Шукається `date_range_raw`.
4. Діапазон дат ділиться на `start_date` і `end_date`.
5. `header_lines` аналізуються на:
   - title
   - company
   - location
6. Bullet-пункти збираються окремо.
7. Все, що не header і не bullet, іде в `description_raw`.

#### `_classify_header_lines`

Це ключова евристика:

- якщо є датований рядок виду `Company 03.2018 – present Role, Location`, parser намагається розділити company/title/location;
- якщо рядок один, застосовується `_split_combined_header`;
- якщо рядків кілька, алгоритм оцінює, який більше схожий на title.

#### `_split_combined_header`

Підтримує patterns:

- `Title at Company`
- `Title @ Company`
- `Title | Company`
- `Title - Company`

#### Чесність алгоритму

Parser не вдає ідеальність. Якщо структура неясна, він краще залишить `raw_text`, ніж вигадає красивий, але неправильний результат.

### `app/parsers/education_parser.py`

Схожий за духом на experience parser, але простіший.

#### Завдання

Розпізнати:

- institution
- degree
- field
- start_date
- end_date
- date_range_raw
- location
- raw_text

#### Алгоритм

1. Ділить секцію на entries.
2. Шукає рядки, схожі на institution.
3. Шукає рядки з degree markers.
4. Витягує date range.
5. Визначає location.

#### Обмеження

Реальні educational записи бувають дуже різні, тому parser робить лише базову структуризацію.

### `app/parsers/generic_list_parser.py`

Універсальний parser для list-like секцій.

#### Алгоритм

1. Збирає секцію в `raw_text`.
2. Визначає, чи текст list-like:
   - є коми;
   - є `;`
   - є `|`
   - є `•`
   - є bullet-переноси.
3. Якщо list-like:
   - ділить текст по separator-ах;
   - чистить items;
   - дедуплікує.
4. Якщо ні:
   - лишає порожній `items`;
   - зберігає `raw_text`.

### `app/parsers/skills_parser.py`

Просто спеціалізація `GenericListParser` для skills.

Це відповідає вимозі промпту: навички не треба агресивно стандартизувати. Тобто сервіс тільки ділить список, але не перетворює "JS" у "JavaScript", не кластеризує і не нормалізує семантично.

---

## 13. Quality checker і fallback

### Навіщо вони потрібні

Реальне резюме майже ніколи не буває "ідеально парсибельним".

Тому сервісу недостатньо просто спробувати один раз щось розпізнати. Потрібно:

- зрозуміти, наскільки результат якісний;
- мати запасний deterministic plan;
- позначити, якщо парсинг був частковим.

### `app/quality/checker.py`

#### `QualityReport`

Містить:

- `warnings`
- `partial_parse`
- `major_sections_found`

#### Алгоритм оцінки

1. Перевіряє наявність контакту.
2. Дивиться, які великі секції взагалі знайдені.
3. Перевіряє співвідношення `unassigned_blocks`.
4. Оцінює, чи не вийшов результат майже пустим при значному обсязі extracted text.

#### Рішення на основі цього

- формує warnings;
- виставляє `partial_parse`;
- повертає список знайдених major sections.

### `app/quality/fallback.py`

Fallback manager — це друга лінія захисту.

#### Ідея

Якщо main path парсингу слабкий, fallback робить прості deterministic спроби врятувати результат.

#### Що робить зараз

- якщо contact слабкий — перепарсує header area;
- якщо немає experience — шукає experience-like blocks;
- якщо немає education — шукає education-like blocks;
- якщо немає skills — шукає skills-like blocks;
- додає warnings;
- ставить `fallback_used = true`.

#### Чому це важливо

Це не AI і не “магія”, а контрольований rescue path. Саме тут у майбутньому можна акуратно вставити:

- OCR fallback;
- alternate regrouping;
- selective AI parse only for ambiguous blocks.

---

## 14. Центральний оркестратор

### `app/pipeline/resume_pipeline.py`

Це серце всієї системи.

Весь сервіс фактично обертається навколо `ResumePipeline.parse(...)`.

#### Що створюється в `__init__`

Pipeline ініціалізує:

- `PDFExtractor`
- `DOCXExtractor`
- `ContactParser`
- `SummaryParser`
- `ExperienceParser`
- `EducationParser`
- `SkillsParser`
- `GenericListParser`
- `FallbackManager`
- `QualityChecker`

Тобто pipeline збирає всі модулі в один coordinated flow.

#### Алгоритм `parse(...)`

##### Крок 1. Створення processing content

Створюється `ResumeContent.build_processing(...)`, де одразу фіксується:

- filename
- mime_type
- parser_version
- `parse_status = "processing"`

##### Крок 2. Extraction

Через `_extract(...)` обирається потрібний extractor:

- `.pdf` -> `PDFExtractor`
- `.docx` -> `DOCXExtractor`

##### Крок 3. Preprocess

Запускається `preprocess_blocks(...)`, щоб привести raw blocks до чистішого вигляду.

##### Крок 4. Layout analysis

`detect_layout_and_reorder(...)` визначає layout і оновлює reading order.

##### Крок 5. Section detection

`detect_section_headers(...)` знаходить логічні секції.

##### Крок 6. Section boundaries

`build_section_map(...)` будує розбиття документа на логічні області.

##### Крок 7. Parsing секцій

Pipeline передає кожну секцію в потрібний parser:

- contact
- summary
- experience
- education
- skills
- certifications
- languages
- projects

##### Крок 8. Fallback

`FallbackManager.apply(...)` намагається підсилити слабкий результат.

##### Крок 9. Collect leftovers

Те, що не вдалося віднести до секцій, потрапляє до `unassigned_blocks`.

##### Крок 10. Quality check

`QualityChecker.evaluate(...)` оцінює підсумковий parse.

##### Крок 11. Final meta

Оновлюються:

- `partial_parse`
- `warnings`
- `ocr_used`
- `parse_status = "completed"`

##### Крок 12. Обробка помилки

Якщо будь-який етап падає:

- `parse_status = "failed"`
- `parse_error = str(exc)`
- `partial_parse = true`
- в `warnings` додається `"Resume parsing failed."`

Це дуже правильне рішення для production-style сервісу: помилка не знищує повністю контекст спроби.

---

## 15. Utility-модулі

### `app/utils/regexes.py`

Містить регулярні вирази та helper-и для:

- email
- phone
- URL
- date range

Функції:

- `extract_first_email`
- `extract_first_phone`
- `extract_urls`
- `detect_profile_links`
- `extract_date_range`
- `split_date_range`

Тут зосереджена вся низькорівнева pattern-логіка.

### `app/utils/text.py`

Містить текстові helper-и:

- `collapse_whitespace`
- `normalize_bullet_prefix`
- `blocks_to_text`
- `split_lines`
- `compact_lines`
- `merge_text`
- `is_likely_bullet`
- `is_short_line`

Це маленькі утиліти, але вони використовуються майже у всіх шарах.

### `app/utils/fuzzy.py`

Містить `best_fuzzy_match(...)`, який обгортає `rapidfuzz.fuzz.WRatio`.

Він потрібен, щоб section detector не працював тільки по strict equality.

---

## 16. Локальний інструмент для розробки

### `scripts/parse_pdf.py`

Це не частина HTTP runtime, а локальний CLI-інструмент для швидкого тестування pipeline без БД.

#### Що робить

1. Приймає шлях до PDF.
2. Читає файл.
3. Викликає `ResumePipeline.parse(...)`.
4. Друкує `Parsed Content` і `Quality Report`.
5. Зберігає Markdown-файл `*.parsed.md`.

#### Навіщо він корисний

- дозволяє дебажити парсер без запуску всього FastAPI;
- не потребує БД;
- дає швидкий цикл покращень.

---

## 17. Тести

### `tests/test_section_detector.py`

Перевіряє, що fuzzy detection працює навіть для typo в заголовках.

### `tests/test_experience_parser.py`

Перевіряє базовий сценарій experience parser:

- title
- company
- start/end dates
- bullets

### `tests/test_quality_checker.py`

Перевіряє, що quality checker:

- бачить відсутність strong contact info;
- ставить warnings;
- правильно виставляє `partial_parse`.

### `tests/test_preprocess_cleaner.py`

Це тест на реальний болючий кейс:

- merged section headers;
- inline bullets;
- PDF-like broken structure.

Він особливо важливий, бо перевіряє саме ті місця, де сервіс уже реально покращувався.

---

## 18. Сильні сторони поточної реалізації

### 1. Модульна архітектура

У проєкті добре відділені:

- HTTP API
- DB layer
- extraction
- preprocess
- detection
- parsing
- quality
- fallback

Це робить код зрозумілішим і розширюваним.

### 2. Shared internal representation

Перехід обох форматів до `TextBlock` — дуже вдале рішення. Воно дає єдину мову для всього пайплайну.

### 3. Чесний парсинг

Сервіс не намагається виглядати "розумнішим", ніж є насправді.

Він:

- лишає `raw_text`;
- збирає `warnings`;
- виставляє `partial_parse`;
- зберігає `unassigned_blocks`.

Це сильний інженерний плюс.

### 4. Збереження всього в `content JSONB`

Повністю відповідає обмеженню задачі. Немає змін до таблиці, але водночас зберігається багатий результат.

### 5. Є шлях до розвитку

Архітектура вже підготовлена до:

- OCR fallback;
- кращої layout analysis;
- додаткових parser-ів;
- selective AI integration.

---

## 19. Поточні обмеження і чесна оцінка

Щоб пояснення було професійним, важливо не тільки хвалити систему, а й чесно сказати, де межі MVP.

### 1. Experience parsing ще не ідеальний

Секція `experience` у резюме найскладніша:

- job entries бувають дуже різними;
- company і title можуть мінятись місцями;
- dates можуть стояти де завгодно;
- bullets інколи зливаються з наступною позицією.

Поточний parser уже працює помітно краще, ніж початковий варіант, але ще не є "enterprise-perfect".

### 2. Contact location ще не завжди точний

Особливо коли location сидить в одному рядку з email/phone/linkedin.

### 3. OCR поки лише як hook

Система вміє сказати "тут потрібен OCR", але сам OCR-процес ще не реалізований.

### 4. DOCX extraction поки простий

Параграфи і таблиці читаються, але без глибокої аналізу стилів, heading levels чи складнішої структури документа.

### 5. Quality checker базовий

Він уже корисний, але може бути розширений більш тонкими метриками.

---

## 20. Чому цей сервіс є хорошим MVP

MVP не має бути ідеальним. Він має:

- вирішувати основну задачу;
- бути технічно чесним;
- бути розширюваним;
- давати відчутний результат;
- мати правильну архітектурну основу.

Цей сервіс цьому відповідає, бо:

- приймає реальні файли;
- підтримує два формати;
- зберігає результат у БД;
- має зрозумілий pipeline;
- не приховує непевність;
- уже має базові тести;
- має модульність, придатну до розвитку.

---

## 21. Як коротко пояснювати це викладачу

Якщо пояснювати одним зв'язним текстом:

> Це rules-based мікросервіс для парсингу резюме. Він приймає PDF або DOCX через FastAPI endpoint, одразу створює запис у PostgreSQL, після чого запускає пайплайн обробки. Спочатку файл переводиться у внутрішній формат `TextBlock`, потім проходить preprocess і layout analysis, далі через fuzzy matching знаходяться секції документа, після чого кожна секція розбирається окремим parser-ом. Після основного парсингу працює fallback manager, а в кінці quality checker оцінює повноту та якість результату. Усе зберігається в `content JSONB`, включаючи дані, warnings, parse status і технічну meta-інформацію. Якщо структура документа неочевидна, сервіс не вигадує дані, а зберігає сирий текст або залишки в `unassigned_blocks`. Тобто система побудована не як магічний AI, а як прозорий, керований і розширюваний parser pipeline.

---

## 22. Висновок

На поточному етапі сервіс є добре організованим MVP parser-service з правильною архітектурною основою.

Його головні переваги:

- модульність;
- прозорість логіки;
- чесне поводження з невизначеністю;
- збереження результатів у stable JSON contract;
- готовність до майбутнього розширення.

Його головна цінність не тільки в тому, що він "парсить резюме", а й у тому, що він робить це **інженерно правильно**:

- з чітким поділом відповідальностей;
- зі збереженням стану;
- з можливістю дебагу;
- з можливістю покращення окремих модулів без переписування всього сервісу.
