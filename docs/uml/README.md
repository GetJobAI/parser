# UML Diagrams For Resume Parser Service

Ця папка містить окремі PlantUML-діаграми для сервісу `resume parser service`.

Обов'язкові діаграми:
- `use_case_resume_parser.puml`
- `activity_parse_pipeline.puml`
- `state_parse_status.puml`
- `er_resume_storage.puml`

Додаткові діаграми:
- `component_resume_parser.puml`
- `deployment_resume_parser.puml`
- `sequence_parse_resume.puml`
- `activity_section_detection.puml`
- `activity_experience_parsing.puml`

Коротко про призначення:
- `Use Case` показує, хто взаємодіє із сервісом і які сценарії використання існують.
- `Activity` показує алгоритм обробки резюме від валідації до збереження результату.
- `State` показує життєвий цикл стану парсингу.
- `ER` показує структуру збереження даних у БД та логічну будову `content`.
- `Component` показує внутрішню модульну архітектуру сервісу.
- `Deployment` показує розгортання сервісу та зовнішні вузли.
- `Sequence` показує покрокову взаємодію компонентів під час `POST /resumes/parse`.
- `Activity (Section Detection)` показує алгоритм визначення секцій документа.
- `Activity (Experience Parsing)` показує алгоритм розбору секції досвіду роботи.

Рендерити можна будь-яким PlantUML viewer або через розширення IDE.
