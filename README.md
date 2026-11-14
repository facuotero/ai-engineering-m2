# Pre-entrega 2 — Extracción de entidades técnicas

Pipeline Python asíncrono que convierte texto libre en una instancia validada de
`ExtraccionTecnica`. Usa Pydantic 2, ChatOpenAI y LCEL. No requiere servidor ni base de datos.

## Instalación

Python 3.11 o superior (verificado con Python 3.14.6). Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` fija las versiones directas y transitivas verificadas.

## Prueba sin credenciales

```bash
python demo.py
python -m pytest -q
```

El mini-script usa `asyncio.run()` y llama a `process_text()` en tres escenarios:
caso normal, texto ambiguo y recuperación después de una respuesta sin
`resumen_tecnico`. En el tercero exige exactamente dos consultas e imprime
`Recuperación simulada verificada: 2 intentos`.

La simulación reemplaza únicamente el transporte de ChatOpenAI. Ejecuta el prompt,
la cadena LCEL, el parser Pydantic de LangChain y los reintentos reales, sin red.
Demuestra validación y recuperación, no la calidad semántica de un modelo real.

## Ejecución real con OpenAI

Configurá ambas variables en tu terminal (no publiques la clave):

```bash
export OPENAI_API_KEY='tu-clave'
export OPENAI_MODEL='modelo-disponible-en-tu-cuenta'
python demo.py --live
```

Elegí un modelo compatible con Chat Completions y llamadas a herramientas.
`OPENAI_MODEL` no tiene valor predeterminado. `.env.example` enumera las variables;
los archivos `.env` no se cargan automáticamente. El modo real consume la API de
OpenAI para los dos primeros casos; la recuperación se sigue simulando para que
sea reproducible. Sin configuración, la ejecución real falla con un mensaje claro.

Uso desde una aplicación asíncrona:

```python
from chain import process_text

async def extraer(texto: str):
    resultado = await process_text(texto)
    print(resultado.model_dump_json(indent=2))
    return resultado
```

## Contrato y criterio de extracción

Los tres campos son obligatorios. `tecnologias` admite una lista vacía: no se deben
inventar tecnologías para satisfacer el esquema. Sus elementos y el resumen no
pueden estar vacíos ni contener solo espacios. Se rechazan campos adicionales.

La criticidad se asigna por el impacto explícito:

- `alta`: interrupción de operaciones críticas, pérdida de datos o incidente grave.
- `media`: degradación del servicio, como lentitud, sin interrupción crítica explícita.
- `baja`: descripción sin impacto adverso.

«El servicio responde lento desde ayer» debe devolver `tecnologias: []`, criticidad
`media` y un resumen que conserve esa información sin inferir causas.
Pydantic valida la estructura; la fidelidad semántica depende del modelo y del prompt.

## Cadena y resiliencia

`chain.py` compone `prompt | model.with_structured_output(...) | validador`.
El template recibe `text` y `format_instructions` mediante placeholders; las
instrucciones incluyen el JSON Schema generado por Pydantic.

Se usa `method="function_calling"` e `include_raw=True`: LangChain devuelve
`raw`, `parsed` y `parsing_error`. La etapa final inspecciona primero
`raw.response_metadata["finish_reason"]`: si es `length`, rechaza la respuesta,
incluso si el parser produjo un objeto. Después eleva cualquier error de parseo
o validación y comprueba el tipo del resultado.

Un runnable asíncrono envuelve la cadena completa con `.with_retry()`:
hasta **tres intentos totales**, sin espera artificial, repitiendo la consulta al
modelo. Los reintentos internos del cliente están desactivados. Se reintentan
errores de JSON, esquema y respuesta ausente/truncada. Al agotarse se lanza
`ProcessingError`, preservando la causa en `__cause__`. Un texto vacío falla antes
de llamar al modelo. Errores de configuración, autenticación o transporte se
propagan sin estos reintentos de contenido; cada consulta tiene timeout de 60 segundos.

Los logs distinguen inicio, intento, clase de error, reintento, validación exitosa
y fallo final, asociados a un identificador de procesamiento. No imprimen texto
original ni credenciales. La respuesta original está disponible en la etapa
`_validate_response` para inspección; no se persiste ni se registra automáticamente.

## Ejemplo

Entrada:

> La API de pagos en FastAPI usa Redis como caché y PostgreSQL para persistencia. En producción se agotaron las conexiones concurrentes a PostgreSQL y la API dejó de procesar pagos.

Salida esperada (la redacción del resumen puede variar con el modelo real):

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "La API de pagos dejó de procesar operaciones en producción al agotarse las conexiones a PostgreSQL."
}
```

## Archivos y verificación

- `schemas.py`: contrato Pydantic y enum.
- `chain.py`: prompt, cliente, inspección de respuesta y función pública asíncrona.
- `demo.py`: mini-script de los tres escenarios.
- `simulation.py`: transporte simulado y datos de ejemplo.
- `tests/test_pipeline.py`: casos válidos, JSON inválido, campos ausentes, enum
  inválido, truncamiento, agotamiento de intentos, entrada vacía y restricciones.

La suite no necesita claves. La ejecución real debe comprobarse con las variables
configuradas; no se considera validada por el éxito de las simulaciones.
