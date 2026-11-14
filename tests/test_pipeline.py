import json
from unittest.mock import patch

import pytest
from pydantic import ValidationError

import chain
from schemas import ExtraccionTecnica
from simulation import NORMAL, AMBIGUOUS, ScriptedClient, simulated_model


@pytest.mark.asyncio
@pytest.mark.parametrize('payload', [NORMAL, AMBIGUOUS])
async def test_success(payload):
    client = ScriptedClient([(json.dumps(payload), 'stop')])
    with patch('chain._create_model', return_value=simulated_model(client)):
        result = await chain.process_text('Texto técnico de prueba')
    assert isinstance(result, ExtraccionTecnica)
    assert result.model_dump(mode='json') == payload
    assert client.calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('bad,reason', [
    (json.dumps({'tecnologias': ['Redis'], 'nivel_de_criticidad': 'alta'}), 'stop'),
    ('this is not JSON', 'stop'),
    (json.dumps(dict(NORMAL, nivel_de_criticidad='urgente')), 'stop'),
    (json.dumps(NORMAL), 'length'),
    ('{"tecnologias":', 'length'),
])
async def test_retry_regenerates(bad, reason, caplog):
    client = ScriptedClient([(bad, reason), (json.dumps(NORMAL), 'stop')])
    with patch('chain._create_model', return_value=simulated_model(client)):
        result = await chain.process_text('FastAPI dejó de procesar pagos')
    assert result.model_dump(mode='json') == NORMAL
    assert client.calls == 2
    assert 'Reintento' in caplog.text


@pytest.mark.asyncio
async def test_exhaustion():
    client = ScriptedClient([('{}', 'stop')] * 3)
    with patch('chain._create_model', return_value=simulated_model(client)):
        with pytest.raises(chain.ProcessingError, match='3 intentos') as error:
            await chain.process_text('Redis falló')
    assert error.value.__cause__ is not None
    assert client.calls == 3


@pytest.mark.asyncio
async def test_empty_input():
    with patch('chain._create_model') as factory:
        with pytest.raises(ValueError):
            await chain.process_text('  ')
        factory.assert_not_called()


@pytest.mark.parametrize('change', [
    {'tecnologias': [' ']}, {'resumen_tecnico': ' '},
    {'nivel_de_criticidad': 'urgente'}, {'extra': 'dato'},
])
def test_schema_rejects_invalid_values(change):
    with pytest.raises(ValidationError):
        ExtraccionTecnica.model_validate(dict(NORMAL, **change))
