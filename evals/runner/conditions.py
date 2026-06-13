from __future__ import annotations


CONDITION_SKILLS: dict[str, tuple[str, ...]] = {
    "no-skill": (),
    "with-cities2-knowledge": ("cities2-knowledge",),
    "with-cities2-modding": ("cities2-modding",),
    "with-cities2-mod-review": ("cities2-mod-review",),
    "with-cities2-mod-debugging": ("cities2-mod-debugging",),
    "with-cities2-mod-release": ("cities2-mod-release",),
}


def condition_skills(condition: str) -> tuple[str, ...]:
    try:
        return CONDITION_SKILLS[condition]
    except KeyError as error:
        raise ValueError(f"unsupported condition: {condition}") from error
