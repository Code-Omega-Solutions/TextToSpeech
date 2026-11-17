from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class EngineDescriptor:
    identifier: str
    languages: tuple[str, ...]
    voices_by_language: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if not self.identifier or self.identifier.strip() != self.identifier:
            raise ValueError("engine identifier must be nonempty and trimmed")
        if not self.languages or len(set(self.languages)) != len(self.languages):
            raise ValueError("engine languages must be nonempty and unique")
        if not set(self.voices_by_language).issubset(self.languages):
            raise ValueError("engine voices must belong to a supported language")
        for language, voices in self.voices_by_language.items():
            if len(set(voices)) != len(voices) or any(not voice for voice in voices):
                raise ValueError(f"engine voices for {language} must be nonempty and unique")
        object.__setattr__(
            self,
            "voices_by_language",
            MappingProxyType(
                {language: tuple(voices) for language, voices in self.voices_by_language.items()}
            ),
        )


@dataclass(frozen=True)
class EngineRegistration:
    descriptor: EngineDescriptor
    enabled: Callable[[], bool]
    ready: Callable[[], bool]
    synthesize: Callable[..., Any]
    voice_catalog: Callable[[], Mapping[str, tuple[str, ...]]] | None = None

    def is_available(self) -> bool:
        return bool(self.enabled() and self.ready())

    def public_info(self) -> dict[str, object]:
        if self.voice_catalog is None:
            voices_by_language = self.descriptor.voices_by_language
            languages = self.descriptor.languages
        else:
            voices_by_language = self.voice_catalog()
            languages = tuple(
                language
                for language in self.descriptor.languages
                if language in voices_by_language
            )
        available = self.is_available()
        if self.voice_catalog is not None and not languages:
            # A dynamically qualified engine must not advertise availability
            # before its approved voice catalog has been loaded.
            available = False
        return {
            "id": self.descriptor.identifier,
            "available": available,
            "languages": list(languages),
            "voices": {
                language: list(voices)
                for language, voices in voices_by_language.items()
                if language in languages
            },
        }


class EngineRegistry:
    def __init__(self, engines: Iterable[EngineRegistration]) -> None:
        registered: dict[str, EngineRegistration] = {}
        for engine in engines:
            identifier = engine.descriptor.identifier
            if identifier in registered:
                raise ValueError(f"duplicate speech engine identifier: {identifier}")
            registered[identifier] = engine
        self._engines = MappingProxyType(registered)

    def resolve(self, identifier: str) -> EngineRegistration | None:
        return self._engines.get(identifier)

    def catalog(self) -> list[dict[str, object]]:
        return [self._engines[key].public_info() for key in sorted(self._engines)]