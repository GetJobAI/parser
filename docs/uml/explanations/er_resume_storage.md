# Пояснення до діаграми `er_resume_storage.puml`

## Що показує ця діаграма

Це ER-діаграма, яка показує:

- структуру таблиці `resumes`;
- логічну структуру JSON-поля `content`;
- вкладені сутності, які формують результат парсингу.

---

## Головна таблиця

На верхньому рівні в системі використовується таблиця:

- `resumes`

Вона містить:

- `id`
- `user_id`
- `content`
- `created_at`
- `updated_at`

Найважливіше поле — це `content`, тому що саме в ньому зберігається весь результат парсингу.

---

## Логічна сутність `ResumeContent`

Поле `content` є `JSONB`, але логічно воно має чітку структуру `ResumeContent`.

У цій структурі є:

- `meta`
- `contact`
- `summary`
- `experience[]`
- `education[]`
- `skills`
- `certifications`
- `languages`
- `projects`
- `unassigned_blocks[]`

---

## Складові `ResumeContent`

### `ResumeMeta`

Містить технічні метадані про процес парсингу:

- назва файлу;
- MIME type;
- версія парсера;
- статус;
- warnings;
- fallback;
- partial parse;
- layout;
- extraction method.

### `ContactInfo`

Містить контактні дані:

- ім’я;
- email;
- телефон;
- локацію;
- посилання;
- raw text.

### `SummarySection`

Містить summary у вигляді `raw_text`.

### `ExperienceEntry`

Містить один запис досвіду роботи:

- title;
- company;
- dates;
- location;
- bullets;
- description;
- raw text.

### `EducationEntry`

Містить один запис про освіту:

- institution;
- degree;
- field;
- dates;
- location;
- raw text.

### `GenericListSection`

Використовується для кількох спискових секцій:

- skills;
- certifications;
- languages;
- projects.

Має:

- `items[]`
- `raw_text`

---

## Що означають зв’язки

На діаграмі показано, що:

- одна таблиця `resumes` містить один `ResumeContent`;
- один `ResumeContent` містить:
  - один `ResumeMeta`;
  - один `ContactInfo`;
  - один `SummarySection`;
  - багато `ExperienceEntry`;
  - багато `EducationEntry`;
  - кілька секцій типу `GenericListSection`.

---

## Чому ця діаграма важлива

Вона пояснює, як у сервісі поєднуються:

- реляційне зберігання в PostgreSQL;
- вкладена JSON-структура результату парсингу.

Це важливо, бо фізично в БД є одна таблиця, але логічно всередині `content` зберігається ціла модель резюме.

---

## Як пояснювати на захисті

Можна казати так:

> ER-діаграма показує, що сервіс використовує одну таблицю `resumes`, у якій весь структурований результат зберігається в полі `content` типу JSONB. Усередині цього поля є логічна структура `ResumeContent`, яка складається з метаданих, контактної інформації, секцій досвіду, освіти та інших спискових секцій.
