#!/usr/bin/env python3
"""Verzionirani, migrirajući DNA MIDI Studio projektni format."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone


SCHEMA = "dna-midi-studio-project"
VERSION = 1


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_hash(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def create_project(state, source=None, style_manifest=None, optimizer_report=None, name="DNA MIDI Project"):
    project = {
        "schema": SCHEMA, "version": VERSION, "name": str(name)[:120],
        "createdAt": utc_now(), "updatedAt": utc_now(),
        "state": deepcopy(state), "source": deepcopy(source),
        "artifacts": {"styleManifest": deepcopy(style_manifest), "optimizerReport": deepcopy(optimizer_report)},
        "invariants": {"midiEmbedded": False, "audioEmbedded": False, "goldAffectsDynamics": False},
    }
    project["projectHash"] = canonical_hash({key: value for key, value in project.items() if key != "projectHash"})
    return project


def migrate_project(document):
    if not isinstance(document, dict):
        raise ValueError("Projekt mora biti JSON objekt")
    if document.get("schema") == SCHEMA:
        if int(document.get("version", 0)) > VERSION:
            raise ValueError("Projekt je napravljen novijom nepodržanom verzijom aplikacije")
        migrated = deepcopy(document)
    elif "optimizer" in document or "style" in document:
        migrated = create_project(document, name="Migrirani DNA projekt")
    elif isinstance(document.get("state"), dict):
        migrated = create_project(document["state"], document.get("source"), name=document.get("name", "Migrirani DNA projekt"))
    else:
        raise ValueError("JSON nije prepoznat kao DNA MIDI Studio projekt")
    migrated["schema"], migrated["version"], migrated["updatedAt"] = SCHEMA, VERSION, utc_now()
    migrated.setdefault("artifacts", {"styleManifest": None, "optimizerReport": None})
    migrated.setdefault("invariants", {"midiEmbedded": False, "audioEmbedded": False, "goldAffectsDynamics": False})
    migrated["projectHash"] = canonical_hash({key: value for key, value in migrated.items() if key != "projectHash"})
    return migrated


def validate_project(document):
    project = migrate_project(document)
    issues = []
    if project["schema"] != SCHEMA or project["version"] != VERSION:
        issues.append("Nepodržana project schema")
    if not isinstance(project.get("state"), dict):
        issues.append("Projekt nema valjani state")
    serialized = json.dumps(project, ensure_ascii=False).lower()
    if '"mididata"' in serialized or '"audiodata"' in serialized:
        issues.append("Projekt ne smije ugrađivati MIDI ili audio binarne podatke")
    if project.get("invariants", {}).get("goldAffectsDynamics") is not False:
        issues.append("Projekt krši Factory-only dinamiku")
    return project, {"passed": not issues, "issues": issues, "schema": SCHEMA, "version": VERSION}


def serialize_project(document):
    project, validation = validate_project(document)
    if not validation["passed"]:
        raise ValueError("; ".join(validation["issues"]))
    return json.dumps(project, ensure_ascii=False, indent=2) + "\n"