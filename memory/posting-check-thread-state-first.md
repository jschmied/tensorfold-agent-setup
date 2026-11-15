---
name: posting-check-thread-state-first
description: "Vor JEDEM Posten in einen fremden Thread dessen aktuellen Stand neu abrufen — zweimal Duplikate erzeugt, weil auf veralteten Abrufen gepostet wurde"
metadata:
  type: feedback
---

Zweimal an einem Tag Duplikate in fremde Threads gepostet:
- 2026-08-21 auf vllm #51581 und #53122 (identischer Text zweimal, gelöscht)
- 2026-08-22 auf HF `unsloth/Qwen3.8-27B-NVFP4#20` — **der Nutzer hatte den Entwurf
  bereits selbst gepostet** (21:41), mein Abruf war von ~21:2x und damit älter.
  Zurückgezogen per `hide_discussion_comment`.

**Why:** Ein Abruf von vor Minuten ist kein Beleg für den jetzigen Stand. Threads bewegen
sich, und der Nutzer selbst ist einer der Beteiligten — er postet Entwürfe oft direkt.

**How to apply:**
- **Unmittelbar vor dem Posten** den Thread neu abrufen und auf denselben Inhalt prüfen,
  nicht auf einen Abruf von vorher vertrauen. Danach die eigene Kommentarzahl gegenprüfen.
- Wenn ein Entwurf an den Nutzer ging, **damit rechnen, dass er ihn selbst gepostet hat**.
  Bei „wo ist X" ist die naheliegende Lesart eine **Ortsfrage**, keine Aufforderung.
- Ein knappes „ok" auf „Soll ich?" ist schwach. Bei outward-facing Aktionen in fremden
  Repos lieber einmal rückfragen, als einen Kommentar zurückziehen zu müssen.
- **HF: `hide_discussion_comment` ist IRREVERSIBEL**, der Inhalt ist danach nicht mehr
  abrufbar. Es gibt kein Löschen und kein Wiederherstellen.


## 2026-08-23 — dritter Fall, neue Variante: Autoren geprüft, Inhalt nicht
Auf vllm #52897 einen Kommentar abgesetzt, nachdem ich die **Autorenliste** des Threads geprüft
hatte — aber nicht gelesen, **was** der letzte Beitrag sagte. kamb-code hatte 70 Minuten vorher
genau den Mechanismus geliefert, der die eine offene Frage aus meinem eigenen vorherigen Kommentar
beantwortet („warum erst die dritte Anfrage"). Mein Text stand daneben, statt darauf zu antworten;
der User hat ihn gelöscht, ich habe beides zu **einem** Kommentar zusammengeführt
(`issuecomment-5387959211`) — der ist deutlich stärker, weil er unsere Laufzeitdaten als Bestätigung
seines CPU-Harness-Modells liest.

**Die Prüfung muss den letzten Beitrag LESEN, nicht zählen.** „Wer hat kommentiert" ist keine
Zustandsprüfung. Konkret vor jedem Post: den letzten fremden Beitrag im Volltext lesen und fragen,
ob mein Text darauf antwortet oder daran vorbeiredet.

## vLLM verlangt AGENTS.md-Konformität bei KI-gestützten Beiträgen (24.08.)
Der Begrüßungsbot auf jedem PR verweist darauf und **droht mit Sperre**. Pflicht im PR-Text:
(1) warum kein Duplikat — mit den drei `gh pr list --search`-Läufen, die sie vorgeben;
(2) Testbefehle **und Ergebnisse**; (3) Modell-Evaluation, falls Ausgabe/Genauigkeit/Serving
betroffen (sonst ausdrücklich „not applicable"); (4) **klare Aussage, dass KI-Unterstützung
verwendet wurde**. Im Commit zusätzlich ein Attributions-Trailer (`Assisted-by:`/`Co-authored-by:`).
Weiter: **keine Kleinst-PRs** („single typo, isolated style change, one mutable default"), minimale
Kommentare, 88 Zeichen, Google-Docstrings — und **ein Mensch muss den Beitrag verteidigen können**.

Unser #53596 war auf allen vier Punkten unvollständig; nachgezogen. Die vorgeschriebene
Duplikatsprüfung förderte **#52527** zutage, das dieselbe Unsichtbarkeit von der Metrik-Seite
angeht — im Text benannt, Unterschied begründet, Rückzug angeboten. **Die Prüfung vor dem Öffnen
machen, nicht danach.**

`gh pr edit --body-file` scheitert an einer GitHub-Deprecation (Projects classic);
`gh api -X PATCH repos/OWNER/REPO/pulls/N --input body.json` funktioniert.

## 2026-09-06 — vierter Fall, andere Richtung: lokal committet ≠ auf dem PR
Die CodeRabbit-Runde zu vllm#55122 wurde am 03.09. lokal committet (`cbd0642a`) und im
Upstream-Log als „commit on the branch" verbucht — **gepusht wurde sie nie**. Der PR trug
drei Tage lang den alten Code (geteilter statischer Device-Property-Cache, keine k=1024-Zeile),
sichtbar erst beim nächsten Push, weil der Fork-Branch bereits drei Main-Merges voraus war.

**How to apply:** Nach jedem „erledigt" an einem PR den **Fernstand** prüfen, nicht den lokalen:
`gh pr view N --json commits -q '.commits[].messageHeadline'`. Und beim Weiterarbeiten an einem
PR-Branch grundsätzlich erst `git fetch fork <branch>` — der Branch kann über die GitHub-Oberfläche
(„Update branch") vorausgelaufen sein, dann ist der lokale HEAD kein Rebase-Ziel.

## Second gate, added 2026-09-20: "is it TRUE" is not "is it NEEDED"

Re-reading the thread stops false claims. It does not stop **unnecessary** ones, and those are a
separate failure.

On vllm#56026 the re-read worked: it caught that my result was not the non-reproduction I thought,
because their replay is chained and my probe shared a fixed prefix. So I reframed and posted an A/B
isolating the chain shape. The user then asked whether that post was necessary — and it largely was
not. Their PR body **already stated** the first-extender miss and its mechanism, and **already
disclosed** that their "after" numbers used `disable_eagle_block_drop` as a stand-in. My headline
review question pointed at something the author had volunteered, which reads as catching an omission
that was never there. The A/B demonstrated in numbers what they had written in prose.

**Before posting, answer in one line: what does this thread not already have?** If the answer is
"our numbers for a point the author already made", that is corroboration — worth a sentence at most,
usually worth nothing. A clean measurement is not by itself a reason to post.

Same day, for contrast, the posts that did earn it: vllm#54076 (the author asked for that exact cell
and we owed it since 09-16) and vllm#56757 (the unified-memory argument, which no one in four open
efforts had made). vllm#55390 was middling — the A/B was new to the thread, its conclusion was "no
measured change".
