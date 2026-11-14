"""Respuestas OpenAI simuladas: el prompt, LCEL y parser siguen siendo reales."""
from types import SimpleNamespace

from langchain_openai import ChatOpenAI

NORMAL_TEXT = ('La API de pagos en FastAPI usa Redis como caché y PostgreSQL para persistencia. '
               'En producción se agotaron las conexiones concurrentes a PostgreSQL '
               'y la API dejó de procesar pagos.')
AMBIGUOUS_TEXT = 'El servicio responde lento desde ayer'
NORMAL = {
    'tecnologias': ['FastAPI', 'Redis', 'PostgreSQL'],
    'nivel_de_criticidad': 'alta',
    'resumen_tecnico': 'La API de pagos dejó de procesar operaciones en producción al agotarse las conexiones a PostgreSQL.',
}
AMBIGUOUS = {
    'tecnologias': [],
    'nivel_de_criticidad': 'media',
    'resumen_tecnico': 'El servicio responde lento desde ayer.',
}


class ScriptedClient:
    """Sustituye únicamente el transporte async de Chat Completions."""
    def __init__(self, responses: list[tuple[str, str]]):
        self.responses = responses
        self.calls = 0
        self.with_raw_response = self

    async def create(self, **kwargs):
        arguments, finish_reason = self.responses[self.calls]
        self.calls += 1
        payload = {
            'id': f'simulated-{self.calls}', 'object': 'chat.completion',
            'created': 0, 'model': 'simulated',
            'choices': [{'index': 0, 'finish_reason': finish_reason, 'message': {
                'role': 'assistant', 'content': None, 'tool_calls': [{
                    'id': f'call-{self.calls}', 'type': 'function',
                    'function': {'name': 'ExtraccionTecnica', 'arguments': arguments},
                }],
            }}],
        }
        return SimpleNamespace(parse=lambda: payload, headers={})


def simulated_model(client: ScriptedClient) -> ChatOpenAI:
    return ChatOpenAI(model='simulated', api_key='simulation-only', async_client=client,
                      max_retries=0, use_responses_api=False)
