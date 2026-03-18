## Visión general del flujo de scraping y AI

Este documento describe, de forma clara para un jurado evaluador, **cómo funciona el scraping**, **qué filtros se aplican** y **cómo interviene la inteligencia artificial** para clasificar y puntuar las vacantes antes de convertirlas en empresas dentro de la base de datos de SCLAPP.

- **Objetivo funcional**: a partir de ofertas de trabajo remotas (Remotive, RemoteOK, etc.), identificar empresas tecnológicas relevantes para el perfil de talento de Riwi, clasificarlas y guardarlas con información estructurada (sector, país, tecnologías, score de AI, etc.).
- **Capas principales**:
  - **API y módulos de Scraping**: exponen el endpoint `POST /scraping/start` y coordinan la llamada al orquestador de scraping.
  - **Servicio de scraping** (`scrape_service.py`): orquesta fuentes, filtros, AI y persistencia a PostgreSQL.
  - **Filtros de negocio** (`job_filters.py`): reglas de texto para decidir relevancia, perfil y tecnologías.
  - **Clasificador AI con OpenAI** (`job_classifier.py`): decide relevancia, perfil, score 1–3 y tecnologías a partir de LLM.

---

## 1. API y rutas de scraping

### Archivo `backend/api/v1/scraping.py`

**Rol del archivo**: expone el router de scraping en la API versión 1.

- Reexporta el router de módulo:
  - `router` viene de `backend.modules.scraping.scraping_routes`.
- Desde FastAPI, este router se monta bajo el prefijo `/scraping`.

No define lógica nueva, solo conecta el módulo de scraping con la capa de API pública.

### Archivo `backend/modules/scraping/scraping_routes.py`

**Rol del archivo**: define las rutas HTTP relacionadas con scraping y el modelo de entrada.

- `router = APIRouter(prefix="/scraping", tags=["scraping"])`
  - Crea un grupo de rutas bajo `/scraping`.

- **Modelo `StartScrapingBody` (Pydantic)**:
  - Campos:
    - `user_id: int | None = None`
    - `parameters: dict | None = None`
  - Representa el cuerpo JSON opcional que llega en `POST /scraping/start`.

- **Endpoint `post_scraping_start`**:
  - Ruta: `POST /scraping/start`
  - Parámetro: `body: StartScrapingBody | None = None`
  - Comportamiento:
    - Si no llega body, crea `StartScrapingBody()` vacío por defecto.
    - Extrae:
      - `user_id = payload.user_id`
      - `parameters = payload.parameters`
    - Llama a `start_scraping(user_id=user_id, parameters=parameters)` del **controller**.
    - Devuelve el `data` que responde el servicio, o lanza `HTTPException(500)` si hay error.

### Archivo `backend/modules/scraping/scraping_service.py`

**Rol del archivo**: capa de servicio de módulo, **delegando** la lógica real al orquestador `run_scraping` y devolviendo una respuesta limpia a los controladores.

- Importa:
  - `from backend.services.scraping.scrape_service import run_scraping`

- **Clase `ScrapingService`**

  - Método estático `start_scraping(user_id: int, parameters: dict | None = None)`:
    - Garantiza que siempre haya un `parameters` (si es `None`, usa `{"source": "example_source"}`).
    - Llama a:
      - `result = run_scraping(parameters=parameters, user_id=user_id, debug=False)`
    - Construye y devuelve un diccionario resumido:
      - `"message": "Scraping completed"`
      - `"total_found"`: total de vacantes encontradas.
      - `"total_new"`: empresas nuevas insertadas.
      - `"total_updated"`: empresas existentes actualizadas.
      - `"total_failed"`: errores en ítems individuales.
      - `"execution_status"`: `SUCCESS`, `PARTIAL` o `FAILED`.

Esta capa **no** implementa scraping en sí misma; solo hace de puente entre el controller y el orquestador de servicios.

---

## 2. Orquestador de scraping y persistencia

### Archivo `backend/services/scraping/scrape_service.py`

**Rol del archivo**: es el **núcleo del scraping**. Orquesta:

- Elección de fuente (`RemoteOK`, `Remotive`, etc.).
- Normalización y deduplicación de compañías.
- Filtros de relevancia para Riwi.
- Clasificación AI con OpenAI (si está activa).
- Inserción/actualización de:
  - `company`
  - `technologies`
  - `company_technologies`
  - `scraping_logs`

Los elementos clave:

#### 2.1. Diccionario de scrapers (`SCRAPERS`)

- `SCRAPERS = {"example_source": example_source.scrape, "remoteok": remoteok.scrape, "remotive": remotive.scrape}`
  - Mapea cada **source** a una función `scrape(...)` concreta.
  - Cada función de fuente devuelve una lista de vacantes “raw” de esa plataforma (con título, descripción, tags, etc.).

#### 2.2. Funciones de apoyo a compañías y tecnologías

- **`_safe_company_contract(raw)`**
  - Garantiza que el diccionario de compañía tenga las claves mínimas:
    - `name, nit, email, phone, url, country, sector, technologies, source, source_url`.
  - Rellena valores faltantes con strings vacíos o listas vacías donde aplique.
  - Es la base para construir el objeto compañía que luego se usará para deduplicar e insertar/actualizar en la tabla `company`.

- **`_normalize_nit(nit)`**
  - Limpia el NIT dejando solo dígitos (`re.sub(r"\D", "", ...)`).
  - Devuelve `None` si queda vacío.
  - Se usa para garantizar que la comparación de NIT sea robusta entre fuentes y DB.

- **`normalize_technology_name(name)`**
  - Normaliza nombres de tecnologías a minúsculas, colapsando espacios.
  - Se usa para `technologies.name_normalization` y poder deduplicar tecnologías.

- **`upsert_technology(name)`**
  - Inserta una tecnología en la tabla `technologies` si no existe, usando `name_normalization` para evitar duplicados.
  - Flujo:
    - Normaliza el nombre.
    - Inserta con `ON CONFLICT (name_normalization) DO NOTHING`.
    - Selecciona el `id_tech` existente o recién creado.
  - Devuelve `id_tech` o `None`.

- **`link_company_technology(id_company, id_tech)`**
  - Inserta relación en `company_technologies` entre una empresa y una tecnología.
  - Usa `ON CONFLICT (id_company, id_tech) DO NOTHING` para evitar duplicados.

- **`find_existing_company(nit, country, name_normalization)`**
  - Busca si la empresa ya existe en `company` usando dos estrategias:
    1. Si hay `nit` limpio: busca por `nit`.
    2. Si no hay `nit`: busca por `(country, name_normalization)` o por `name_normalization` con `country` vacío.
  - Devuelve el primer registro como dict o `None`.
  - Sirve para decidir entre **insertar** una empresa nueva o **actualizar** una existente.

- **`insert_company(...)`**
  - Inserta una fila en `company` con todos los campos relevantes, incluido:
    - `category` (perfil detectado)
    - `score` (score AI 1–3 o `NULL`)
  - Si `score` no está en el rango 1–3, lo fuerza a `None` por seguridad.
  - Devuelve `id_company` de la fila insertada.

- **`update_company(id_company, existing, ..., category, score)`**
  - Actualiza **solo** los campos vacíos (`NULL` o string vacío) en una empresa existente.
  - Recorre los campos `sector, email, phone, url, description, category, score`:
    - Si en DB están vacíos y en el nuevo scraping hay un valor, los actualiza.
  - Valida también que `score` esté en rango 1–3; en caso contrario, lo ignora.

- **`_get_first_user_id()`**
  - Devuelve el primer `id_user` de la tabla `users`.
  - Se usa cuando no se pasa `user_id` explícito, para poder guardar logs de scraping sin romper la FK.

- **`insert_scraping_log(...)`**
  - Inserta un registro en `scraping_logs` con:
    - `id_user`, `source`, `parameters` (JSON), `total_found`, `total_new`, `total_updated`, `total_failed`, `execution_status`, `error_message`, `duration_second`.
  - Usa `get_db_info()` para imprimir en logs información de conexión a DB.
  - Permite auditar y rastrear cada ejecución de scraping.

#### 2.3. Función principal `run_scraping(...)`

> Nota: solo se muestra la lógica relevante al flujo; aquí lo explicamos conceptualmente.

**Firma (resumida)**:

- `run_scraping(parameters: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None, debug: bool = False) -> Dict[str, Any]`

**Parámetros de entrada** (vienen desde frontend / API):

- `parameters`:
  - `source`: plataforma (por ejemplo `"remotive"` o `"remoteok"`).
  - `query`: término opcional de búsqueda (ej. `"python"`).
  - `max_items`: límite de ítems a procesar (para demos se ajustó a 3 desde frontend).
  - `only_riwi_relevant`: booleano, si `True` solo se guardan roles tech relevantes.
  - `require_junior_focus`: si `True`, exige señales de junioridad.
- `user_id`:
  - Usuario que dispara el scraping, usado para `scraping_logs`.
  - Si es `None`, se reemplaza por `_get_first_user_id()`.

**Pasos internos principales**:

1. **Inicialización y validaciones**:
   - Se normalizan parámetros.
   - Se valida `max_items` (si existe).

2. **Selección de scraper**:
   - Usa el diccionario `SCRAPERS` para obtener la función de scraping correspondiente según `source`.
   - Llama a la función `scrape(...)` de esa fuente.

3. **Recorrido de resultados “raw”**:
   - Para cada vacante devuelta por la fuente:
     - Se construye un diccionario `raw_job` con los campos relevantes (company_name, job_title, job_description, tags, etc.).

4. **Filtro de relevancia de negocio (job_filters)**:

   - Antes de gastar AI, aplica un filtro rápido de reglas:
     - Llama a `job_filters.is_riwi_relevant_job(raw_job, only_riwi_relevant=True, require_junior_focus=require_junior_focus)`.
     - Si devuelve `False`, **omite** esa vacante (no se convierte en empresa).
   - Este filtro:
     - Detecta keywords tech (developer, engineer, data, etc.).
     - Excluye explícitamente roles no tech (marketing, sales, recruiter, HR, etc.).
     - Puede exigir una señal de junioridad si así se pide.

5. **Extracción por reglas (perfil y tecnologías)**:

   - Si pasa el filtro de relevancia:
     - `profile = job_filters.extract_profile_from_job(raw_job)`:
       - Detecta el perfil (ej. Backend Developer, Data Analyst) a partir de título, tags, etc.
     - `tech_names = job_filters.extract_technologies_from_job(raw_job)`:
       - Extrae tecnologías mencionadas (python, react, docker, etc.) usando una lista de tecnologías conocidas.

6. **Clasificación con AI (OpenAI) — `job_classifier`**

   - Se intenta enriquecer la vacante con el clasificador AI:
     - `ai_result = job_classifier.classify_job_with_ai(raw_job)`
     - Manejado en un `try/except`: si la IA falla o la API no está configurada, se recibe `None`.

   - Si `ai_result` **no es None**:
     - Si `ai_result["is_relevant"]` es `False`, la vacante se descarta.
     - El perfil puede ser sobreescrito por la IA: `profile = ai_result.get("profile") or profile`.
     - Se lee `raw_score = ai_result.get("score")`:
       - Si existe y está en el rango 1–3, se convierte a `score` entero.
       - Si no es válido, se descarta y se deja `score = None`.
     - Si `ai_result["technologies"]` trae tecnologías, se normalizan a lowercase y se usan para `tech_names`.
     - Se imprimen logs de depuración con el resultado AI.

   - Si `ai_result` es `None`:
     - Se mantiene la clasificación **solo por reglas** (profile y technologies).
     - El score quedará `None` (sin puntuar por AI).

7. **Normalización de tecnologías y deduplicación**:
   - `tech_names = list(dict.fromkeys(tech_names))` para quitar duplicados.

8. **Normalización / deduplicación de compañía y persistencia**:

   - Se construye `safe = _safe_company_contract(raw)` con datos de la empresa.
   - Se calcula `name_normalization` y `dedupe_key`.
   - Se normaliza NIT, país, etc.
   - Se busca si ya existe compañía con:
     - `find_existing_company(nit_clean, country_val, name_norm)`.

   - Si **ya existe**:
     - Se llama a `update_company(...)` pasando el `score` y el `profile` (category).
     - Se incrementa `total_updated`.

   - Si **no existe**:
     - Se llama a `insert_company(...)` con todos los campos:
       - Incluyendo `category=profile` y `score=score`.
     - Si inserta bien: `total_new += 1`.
     - Si falla: `total_failed += 1` y se registra error.

9. **Guardado de tecnologías asociadas**:

   - Por cada `tech_name` en `tech_names`:
     - Se normaliza (`normalize_technology_name`).
     - Se obtiene `id_tech = upsert_technology(tech_name)`.
     - Se guarda la relación `link_company_technology(id_company, id_tech)`.

10. **Cálculo de estado de ejecución y log**:

    - Con los totales:
      - `total_found`, `total_new`, `total_updated`, `total_failed`.
    - Determina:
      - `execution_status` = `SUCCESS` (sin fallos), `PARTIAL` (algunos fallos) o `FAILED` (todos fallan).
    - Calcula la duración con `time.perf_counter()`.
    - Llama a `insert_scraping_log(...)` para registrar la ejecución.

11. **Resultado devuelto**:

    - Devuelve un diccionario con al menos:
      - `total_found`, `total_new`, `total_updated`, `total_failed`, `execution_status`.
    - Este es el resultado que acaba viendo el frontend.

---

## 3. Filtros de negocio sobre las vacantes

### Archivo `backend/services/scraping/job_filters.py`

**Rol del archivo**: define la lógica de **filtro de relevancia**, **detección de perfil** y **extracción de tecnologías** usando reglas basadas en texto.

Elementos clave:

- Listas de constantes:
  - `RIWI_ACCEPT_SIGNALS`: palabras/frases que indican roles tech (developer, engineer, data, devops, QA, etc.).
  - `RIWI_EXCLUDE_SIGNALS`: roles a excluir (marketing, sales, recruiter, HR, finance, etc.).
  - `RIWI_JUNIOR_SIGNALS`: señales de roles junior/entry (junior, trainee, internship, entry level, etc.).
  - `PROFILE_OPTIONS` y `PROFILE_KEYWORDS`: mapeo entre palabras clave y perfiles (Backend Developer, Data Analyst, etc.).
  - `KNOWN_TECHNOLOGIES`: listado de tecnologías conocidas para extracción (python, react, docker, postgres, etc.).

#### 3.1. Función `_text_from(raw_job, *keys)`

- Une en un solo string en minúsculas los valores de `raw_job` para las claves indicadas.
- Acepta tanto strings como listas.
- Se usa como preparación para los filtros de relevancia y extracción.

#### 3.2. Función `_has_any_signal(text, signals)`

- Dado un texto y una lista de señales:
  - Devuelve `True` si el texto contiene alguna de las señales como palabra completa (usa regex con bordes de palabra).
- Evita falsos positivos (por ejemplo, no confundir `"go"` con `"google"`).

#### 3.3. Función `is_riwi_relevant_job(raw_job, only_riwi_relevant=True, require_junior_focus=False)`

- Decide si una vacante es **relevante para Riwi** antes de gastar AI:
  - Si `only_riwi_relevant` es `False`, devuelve `True` directamente (no filtra).
  - Si el texto combinado de título/categoría/tags/descr. está vacío, por defecto **acepta** (devuelve `True`).
  - Si encuentra cualquier señal de `RIWI_EXCLUDE_SIGNALS`, devuelve `False`.
  - Si **no** encuentra ninguna señal de `RIWI_ACCEPT_SIGNALS`, devuelve `False`.
  - Si `require_junior_focus` es `True` y no encuentra señales de `RIWI_JUNIOR_SIGNALS`, devuelve `False`.
  - En los demás casos, devuelve `True`.

Este filtro es la **primera barrera** para centrarse en vacantes tech y descartar roles claramente no técnicos.

#### 3.4. Función `extract_profile_from_job(raw_job)`

- Devuelve el perfil principal para `company.category`:
  - Usa `PROFILE_KEYWORDS` para mapear:
    - Palabras como `backend`, `api developer` → `"Backend Developer"`.
    - `data analyst`, `power bi` → `"Data Analyst"`, etc.
  - Si no encuentra nada, por defecto devuelve `"Software Developer"`.

#### 3.5. Función `extract_technologies_from_job(raw_job)`

- Extrae un listado de tecnologías desde:
  - `job_title`, `position`, `title`, `job_category`, `category`, `tags`, `technologies`, `job_description`, `description`.
- Recorre `KNOWN_TECHNOLOGIES` y busca coincidencias en el texto.
- Devuelve:
  - Lista de strings en minúsculas, sin duplicados, con nombres de tecnología limpios.

Estas funciones de `job_filters` garantizan que, incluso sin AI, el sistema tenga una clasificación razonable de perfil y stack tecnológico.

---

## 4. Clasificador de AI con OpenAI

### Archivo `backend/services/ai/job_classifier.py`

**Rol del archivo**: encapsula toda la interacción con OpenAI para clasificar cada vacante:

- Determinar si es relevante o no (`is_relevant`).
- Asignar un perfil (`profile`).
- Calcular un **score 1–3** (`score`) según afinidad con talento junior.
- Extraer tecnologías adicionales (`technologies`).
- Dar una breve justificación (`reason`).

Elementos principales:

#### 4.1. Constantes y utilidades

- `PROFILE_OPTIONS`:
  - Lista de perfiles válidos que la IA puede devolver (`Backend Developer`, `Frontend Developer`, `Full Stack Developer`, `Data Analyst`, `QA Engineer`, `DevOps Engineer`, `Software Developer`).

- `CLASSIFIER_MODEL = "gpt-4o-mini"`:
  - Modelo usado para clasificar (se fuerza a este, independientemente de la config general).

- **`_build_prompt(raw_job)`**
  - Construye un texto compacto con:
    - Company: nombre de empresa.
    - Job title / position / title.
    - Categoría.
    - Tags / tecnologías.
    - Descripción (recortada a 1200 caracteres).
    - Source.
  - Este texto se pasa como contenido de usuario al LLM.

- **`_validate_ai_response(data)`**
  - Toma el JSON devuelto por la IA y asegura:
    - `profile` ∈ `PROFILE_OPTIONS` (si no, fuerza `"Software Developer"`).
    - `score` ∈ `{1, 2, 3}` (si no, lo pone en `None`).
    - `technologies` es lista; la normaliza a strings en minúsculas y máximo 15 elementos.
    - `is_relevant` es booleano.
    - `reason` se corta a 200 caracteres.
  - Devuelve un dict normalizado con:
    - `is_relevant, profile, score, technologies, reason`.

#### 4.2. Función principal `classify_job_with_ai(raw_job)`

- Lee configuración:
  - `settings = get_settings()`
  - `api_key = settings.get("openai_api_key")`
  - Si no hay API key → devuelve `None` (no se usa AI).

- Construye el prompt:
  - `system`: instrucciones muy detalladas para:
    - Responder **solo JSON** (sin markdown).
    - Incluir claves: `is_relevant`, `profile`, `score`, `technologies`, `reason`.
    - Definir reglas de interpretación de `score`:
      - 3 → Altamente alineado con talento junior/trainee/apprentice.
      - 2 → Rol técnico útil para Riwi pero no necesariamente junior.
      - 1 → Rol técnico pero con baja afinidad al pipeline junior.
    - Filtrar roles no técnicos (marketing, sales, HR, etc.).
    - Limitar `technologies` a tecnologías reales (python, react, docker, etc.).
  - `user`: texto con `Classify this job:\n{prompt_text}`.

- Llamada a la API de OpenAI:
  - Crea `OpenAI(api_key=api_key)`.
  - Llama a `client.chat.completions.create(...)` con:
    - `model=CLASSIFIER_MODEL`.
    - Mensajes `system` y `user`.
    - `max_completion_tokens=400`.

- Procesamiento de la respuesta:
  - Extrae el contenido de `response.choices[0].message`:
    - Soporta tanto contenido string como listado de partes.
  - Imprime logs de diagnóstico (`[OPENAI RESPONSE ...]`).
  - Limpia posibles fences markdown (```).
  - Hace `json.loads(content)` para obtener un dict.
  - Llama a `_validate_ai_response(data)` para asegurar el formato.
  - Imprime `[OPENAI VALIDATED SCORE]`.
  - Devuelve el dict normalizado.

- Manejo de errores:
  - Cualquier excepción se captura y se imprime como `[OPENAI CLASSIFIER ERROR]`.
  - En caso de error, devuelve `None`.

#### 4.3. Relación con el flujo de scraping

- `run_scraping` usa `classify_job_with_ai` **por cada vacante**:
  - Si la IA responde:
    - Puede sobreescribir `profile`.
    - Asigna `score` 1–3.
    - Sugiere tecnologías adicionales.
    - Permite filtrar también por `is_relevant`.
  - Si la IA falla o no hay API key:
    - El flujo sigue con **solo reglas** (`job_filters`) y `score=None`.

---

## 5. Resumen para sustentar ante el jurado

- El **front** dispara el scraping con un `POST /scraping/start` indicando:
  - Fuente (ej. `remotive`), query opcional, flags de relevancia y límite de ítems (`max_items`).
- La **API de scraping** delega en el módulo y este en el **servicio de scraping**.
- El **orquestador `run_scraping`**:
  1. Llama al scraper adecuado (Remotive/RemoteOK).
  2. Filtra las vacantes mediante reglas de negocio (`is_riwi_relevant_job`).
  3. Extrae un perfil y tecnologías base por reglas.
  4. Enriquecen la clasificación con **IA (OpenAI)**:
     - Decide si la vacante es relevante.
     - Ajusta el perfil.
     - Calcula un **score de 1 a 3** según afinidad con talento junior.
     - Refina la lista de tecnologías.
  5. Deduplica compañías y guarda en PostgreSQL:
     - Nuevas (`insert_company`) o actualizadas (`update_company`).
     - Tecnologías (`upsert_technology`, `link_company_technology`).
  6. Registra los resultados en `scraping_logs` para trazabilidad.

- En ausencia de IA (sin `OPENAI_API_KEY` o error de API), el sistema **no se cae**:
  - Sigue guardando empresas basadas solo en reglas (texto), pero sin `score`.

Esta arquitectura separa claramente:

- **Rutas y API** (controladores y routers).
- **Orquestación de negocio** (servicio de scraping).
- **Reglas determinísticas** (`job_filters`).
- **Clasificación probabilística con LLM** (`job_classifier`).

De esta forma, puede explicarse ante el jurado que:

- El sistema tiene una **capa de filtrado sólido y explicable** (reglas).
- La IA se usa como **capa adicional de inteligencia** para:
  - Afinar relevancia.
  - Asignar un score “junior-fit” 1–3.
  - Enriquecer tecnologías.
- Todo queda persistido y **auditado** vía `scraping_logs`, lo que facilita trazabilidad y evaluación posterior.

