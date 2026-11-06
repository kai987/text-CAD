"""Validate the shared input contract for dependency-free landmark models."""
from __future__ import annotations

from math import isfinite
import re


_MODEL_IDENTITIES = {
    'tokyo-tower': ('tokyo_tower', 'square_half_width'),
    'tokyo-skytree': ('tokyo_skytree', 'triangle_circle_tangent_arcs'),
}


def _number(value, label, *, minimum=0):
    if type(value) not in (int, float) or not isfinite(value) or value <= minimum:
        raise ValueError(f'{label} must be a finite number greater than {minimum}.')
    return value


def _finite_values(value, label):
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f'{label} must use string keys.')
            _finite_values(item, f'{label}.{key}')
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite_values(item, f'{label}[{index}]')
    elif type(value) in (int, float):
        if not isfinite(value):
            raise ValueError(f'{label} must be finite.')
    elif value is not None and not isinstance(value, (str, bool)):
        raise ValueError(f'{label} contains an unsupported parameter value.')


def _levels(values, label, height):
    if not isinstance(values, list) or not values:
        raise ValueError(f'{label} must contain ordered heights.')
    previous = 0
    for value in values:
        _number(value, label, minimum=previous)
        if value >= height:
            raise ValueError(f'{label} must be below the tower height.')
        previous = value


def validate_tower_parameters(tower_id, parameters):
    """Check shared dimensions and metadata; retain all original values and types.

    Detail modules continue validating their own section and connection controls.
    Historical replay fixtures retain their separate recorded parameter sets.
    """
    if tower_id not in _MODEL_IDENTITIES:
        raise ValueError(f'Unknown landmark: {tower_id!r}')
    if not isinstance(parameters, dict):
        raise ValueError('Tower parameters must be a dictionary.')
    _finite_values(parameters, tower_id)
    stem, profile_kind = _MODEL_IDENTITIES[tower_id]
    if parameters.get('file_stem') != stem or parameters.get('profile_kind') != profile_kind:
        raise ValueError(f'Parameter identity differs from {tower_id}.')
    if not re.fullmatch(r'LANDMARK-R0*[1-9]\d*', str(parameters.get('revision', ''))):
        raise ValueError('Tower revision must use LANDMARK-R followed by a positive integer.')
    names = parameters.get('names')
    if not isinstance(names, dict) or any(not isinstance(names.get(locale), str)
                                          or not names[locale].strip() for locale in ('zh', 'ja', 'en')):
        raise ValueError('Tower names must include Chinese, Japanese and English.')
    height = _number(parameters.get('height_mm'), 'height_mm')
    for field in ('base_width_mm', 'base_slab_thickness_mm', 'antenna_start_mm'):
        _number(parameters.get(field), field)
    if parameters['antenna_start_mm'] >= height:
        raise ValueError('antenna_start_mm must be below the tower height.')
    _levels(parameters.get('deck_levels_mm'), 'deck_levels_mm', height)
    if 'nominal_deck_levels_mm' in parameters:
        _levels(parameters['nominal_deck_levels_mm'], 'nominal_deck_levels_mm', height)
    profile = parameters.get('profile')
    if not isinstance(profile, list) or len(profile) < 2:
        raise ValueError('profile must contain at least two height/radius controls.')
    previous = -1
    for row in profile:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError('profile controls must be [height, radius] pairs.')
        z, radius = row
        _number(z, 'profile height', minimum=previous)
        _number(radius, 'profile radius')
        if z >= height:
            raise ValueError('profile controls must be below the tower height.')
        previous = z
    if profile[0][0] != 0:
        raise ValueError('profile must begin at the ground datum.')
    decks = parameters.get('deck_specs')
    if not isinstance(decks, list) or not decks:
        raise ValueError('deck_specs must contain deck envelopes.')
    for deck in decks:
        if not isinstance(deck, dict) or not isinstance(deck.get('id'), str) or not deck['id']:
            raise ValueError('Each deck needs an identifier.')
        levels = [deck.get(field) for field in ('bottom_mm', 'glass_bottom_mm', 'top_mm')]
        _levels(levels, f"deck_specs.{deck['id']}", height)
    if not isinstance(parameters.get('detail'), dict):
        raise ValueError('detail must be a dictionary.')
    references = parameters.get('source_references')
    if not isinstance(references, list) or not references:
        raise ValueError('source_references must record the parameter provenance.')
    if any(not isinstance(reference, dict) or not isinstance(reference.get('url'), str)
           or not reference['url'].startswith('https://') for reference in references):
        raise ValueError('Each source reference needs an HTTPS URL.')
    return parameters
