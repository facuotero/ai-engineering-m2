"""Mini-script asíncrono; sin red por defecto, --live para OpenAI."""
import argparse
import asyncio
import json
import logging
from unittest.mock import patch

from chain import process_text
from simulation import (AMBIGUOUS, AMBIGUOUS_TEXT, NORMAL, NORMAL_TEXT,
                        ScriptedClient, simulated_model)


async def main(live: bool = False):
    for name, text, expected in [('normal', NORMAL_TEXT, NORMAL),
                                 ('ambiguo', AMBIGUOUS_TEXT, AMBIGUOUS)]:
        if live:
            result = await process_text(text)
        else:
            client = ScriptedClient([(json.dumps(expected), 'stop')])
            with patch('chain._create_model', return_value=simulated_model(client)):
                result = await process_text(text)
        if name == 'ambiguo':
            assert result.tecnologias == [], 'No debe inventar tecnologías'
            assert result.nivel_de_criticidad == 'media'
        else:
            assert set(result.tecnologias) == set(NORMAL['tecnologias'])
            assert result.nivel_de_criticidad == 'alta'
        print(f'Caso {name}:')
        print(result.model_dump_json(indent=2))

    incomplete = {key: value for key, value in NORMAL.items() if key != 'resumen_tecnico'}
    client = ScriptedClient([(json.dumps(incomplete), 'stop'), (json.dumps(NORMAL), 'stop')])
    with patch('chain._create_model', return_value=simulated_model(client)):
        result = await process_text(NORMAL_TEXT)
    assert client.calls == 2
    assert result.model_dump(mode='json') == NORMAL
    print(f'Recuperación simulada verificada: {client.calls} intentos')
    print(result.model_dump_json(indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Usar OpenAI en los dos primeros casos')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
    asyncio.run(main(args.live))
