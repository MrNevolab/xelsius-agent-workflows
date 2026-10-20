"""xelsius Agent-Team: Ein Workflow, mehrere geplante Aufgaben.

Architektur:
- Recherche/Text: Mistral Conversation mit built-in web_search (laeuft unter Worker-Identitaet)
- E-Mail-Entwurf: Outlook-Connector-Slot (run_as="deployment")
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import mistralai.workflows as workflows
from mistralai.workflows import Depends
from mistralai.workflows.plugins.mistralai.connectors import (
    ToolCallClient,
    connector,
    uses_connectors,
)

RECIPIENT = "schildwaechter@nevolab.de"
TZ = ZoneInfo("Europe/Berlin")

outlook_connector = connector("outlook", auto_auth=False)

CI_BLOCK = """PERSÖNLICHKEITS-PROFIL (höchste Priorität): Daniel Schildwächter ist ein direkter, präziser Typ – nicht lange um das Thema herumreden, ehrlich, kurz, prägnant, informativ. Keine Füllwörter, keine rhetorischen Einschübe, keine diplomatischen Weichmacher, keine überflüssigen Höflichkeitsfloskeln. Klare Aussagen, auch wenn unbequem.
CI-REGELN LINKEDIN: (1) Tonalität meinungsstark (Thought Leadership): klare Kante, These → Begründung → Conclusio, KEINE Marketing-Superlative. (2) Deutsch, DACH-Fokus. (3) Autorenperspektive: Personal Brand Daniel Schildwächter (Praktiker-Perspektive vom Hersteller), xelsius nur als Erfahrungskontext, nicht als Werbung. (4) Struktur je Post: Hook in Zeile 1 (max. 1–2 Sätze, hart und direkt), dann 3–5 KURZE Absätze mit EINER Kernidee, dann eine direkte Abschlussfrage, optional weicher xelsius-Bezug nur wenn gerechtfertigt, 100–200 Wörter, eher kürzer. (5) Wettbewerber (EasyMax, Integrity, Mya) niemals herabsetzen; nur objektive, faktenbasierte Vergleiche; Positionierungslinie 'Wo kleinere Volumen reichen, reicht ein kompaktes System'. (6) Hashtags: 3–5 am Ende, gemischt aus Kern-Set (#Laborautomatisierung #Chemie), Themen-Set (#Prozessentwicklung #DoE #Synthese #Reaktionsoptimierung), KI-Set (#KIinDerChemie #SelfDrivingLabs) und Branchen-Set je Thema (#Lacke #Beschichtungen #Klebstoffe #Elektrochemie #Photochemie). (7) Je Post eine konkrete Bildidee: Labor-/Geräte-Realität (Nahbereich Reaktorzellen, Schnittstellen, Dashboard) oder Diagramm-Idee (DoE-Heatmap, Parallelreaktor-Schema), keine Stock-Fotos."""

PRODUCT_BLOCK = """PRODUKT-KONTEXT: xelsius LabWorkStation (nevoLAB), 10 unabhängig geregelte Reaktorzellen (0,5–30 ml, −20 bis +150 °C), Module für Druck (15/200 bar), Photochemie (LumiSynth), Elektrochemie (ElectroSynth), Dosierung; Schnittstellen REST API, OPC-UA, RS232. Kernmärkte: Early Drug Discovery, frühe chemisch-pharmazeutische Entwicklung. Priorität: Einsatzgebiete außerhalb der Pharmafrühphase erschließen (Lacke, Beschichtungen, Klebstoffe, Polymere, Elektrochemie, Photochemie, Energie). Zielgruppe: Chemiker, Prozessentwickler, Lab-Automation-Entscheider im DACH-Raum. Wettbewerber: Mettler Toledo EasyMax (größere Volumina), Cole-Parmer Integrity (v. a. UK), Radleys Mya 4/6 — NUR objektiv vergleichen, NIE herabsetzen."""

OUTPUT_RULE = "ABGABE: Gib am Ende deine Antwort NUR als vollständigen HTML-E-Mail-Body aus (inline CSS, klar getrennte Blöcke, gut lesbar, auf Deutsch). Beginne mit '<!DOCTYPE html>' und endet mit '</html>'. Keine Einleitung, keine Erklärung, kein Markdown-Codefence – NUR das HTML. Nutze die Kalenderwoche KW {kw} im Inhalt."

TASKS = {}

TASKS["trend_report"] = {
    "subject": "Themen-Report KI & Automatisierung in der Chemie – KW {kw}",
    "prompt": (
        "Du bist der Trend-Agent für nevoLAB/xelsius. Rechtiere aktuelle Themen der LETZTEN 7 Tage: Laborautomatisierung, KI in der Chemie, self-driving labs, Kleinvolumen-Synthese, Photo-/Elektrochemie, DoE, neue Anwendungsfelder außerhalb der Pharma. Nutze die Websuche mehrfach (deutsch und englisch). "
        + PRODUCT_BLOCK
        + " Erstelle einen Themen-Report als HTML-E-Mail: 5–7 Top-Themen mit je 2–3 Sätzen und xelsius-Relevanz, Abschnitt 'Trends & mittelfristige Entwicklung', Abschnitt 'Querschnitts-Industrien' (z. B. Lacke, Klebstoffe, Polymere, Elektrochemie, Photochemie, Energie). "
        + OUTPUT_RULE
    ),
}

TASKS["content_posts"] = {
    "subject": "LinkedIn-Content xelsius – KW {kw}",
    "prompt": (
        "Du bist der Content-Agent für Daniel Schildwächter / nevoLAB xelsius. Rechtiere KURZ aktuelle Themen der letzten 14 Tage (Websuche, deutsch+englisch): Laborautomatisierung, KI in der Chemie, self-driving labs, Kleinvolumen-Synthese, Photo-/Elektrochemie, DoE, neue Anwendungsfelder außerhalb der Pharma. "
        + CI_BLOCK
        + " "
        + PRODUCT_BLOCK
        + " Erstelle 3 fertige LinkedIn-Posts: (1) Trend/News-Kommentar mit xelsius-Bezug, (2) Anwendungs-/How-to-Content, (3) Denkanstoß zur Zukunft der Lab-Automatisierung. Mindestens einer greift ein Einsatzgebiet außerhalb der Pharmafrühphase auf. Je Post: 3–5 Hashtags, eine konkrete Bildidee, ein Satz 'Warum dieser Post die Zielgruppe erreicht'. Alles als klar getrennte HTML-Blöcke. "
        + OUTPUT_RULE
    ),
}

TASKS["research_radar"] = {
    "subject": "Forschungs-Radar xelsius – KW {kw}",
    "prompt": (
        "Du bist der Forschungs-Agent für nevoLAB/xelsius. Suche aktuelle Paper, Preprints und Konferenzbeiträge der letzten 7–14 Tage zu: automatisierte Synthese, Kleinvolumen-/Parallelreaktoren, KI/ML in der Reaktionsoptimierung, DoE, Photochemie, Elektrochemie, self-driving labs, Anwendungsfelder außerhalb der Pharma. "
        + PRODUCT_BLOCK
        + " Liefere 5–8 Einträge mit Titel/Quelle, 2–3 Sätzen Inhalt und einer konkreten xelsius-Relevanz-Bewertung je Eintrag, als HTML-E-Mail. "
        + OUTPUT_RULE
    ),
}

TASKS["product_report"] = {
    "subject": "Produkt-Report xelsius – KW {kw}",
    "prompt": (
        "Du bist der Produkt-Agent für nevoLAB/xelsius (monatlicher Wettbewerbs- und Technologie-Scan). Nutze die Websuche für aktuelle Entwicklungen. "
        + PRODUCT_BLOCK
        + " Erstelle als HTML-E-Mail: (1) Wettbewerbs-Scan: aktuelle News/Produktupdates zu Mettler Toledo EasyMax, Cole-Parmer Integrity, Radleys Mya – NUR objektiv, nie herabsetzen; (2) Kundenbedarfs-Signale aus öffentlichen Quellen; (3) Technologie-Radar (Sensorik, Automation, KI, Schnittstellen) mit Zeithorizont; (4) 3–5 konkrete Empfehlungen für Positionierung und Produkt. "
        + OUTPUT_RULE
    ),
}

TASKS["sales_intel"] = {
    "subject": "Sales-Intelligenz xelsius – KW {kw}",
    "prompt": (
        "Du bist der Sales-Intelligenz-Agent für nevoLAB/xelsius. KEIN automatisches LinkedIn-Messaging – nur E-Mail-Entwürfe, Daniel macht Kontakte persönlich. Bekannter Lead (Priorität A): Sai Life Sciences (nutzt Cole-Parmer Integrity + AmigoChem, Ansprechpartner Associate Principal Scientist). Nutze die Websuche für aktuelle Anlässe. "
        + PRODUCT_BLOCK
        + " Erstelle als HTML-E-Mail: (1) 5–8 Zielfirmen-Liste (DACH + Non-Pharma-Branchen wie Lacke, Klebstoffe, Polymere, Elektrochemie) mit je einem konkreten Erstkontakt-Anlass aus recherchierten News; (2) je 1 Sales-Navigator-Filterrezept für die wichtigsten Segmente; (3) 2 kurze Outreach-Templates (nur als Text in der E-Mail, nirgendwo senden); (4) 3 Warm-up-Tipps. "
        + OUTPUT_RULE
    ),
}

TASKS["refinement_reminder"] = {
    "subject": "Verfeinerungs-Erinnerung xelsius – KW {kw}",
    "prompt": (
        "Du bist die Verfeinerungs-Erinnerung für Daniel Schildwächter. Erstelle eine KURZE Erinnerungs-E-Mail als HTML: Daniel soll Feedback geben zu (a) den Agenten-Ausgaben der letzten Wochen (Trend-Report, Content-Posts, Forschungs-Radar, Produkt-Report, Sales-Intelligenz), (b) der LinkedIn-CI, (c) neuen Marktbeobachtungen. Kompakte Checkliste. Kein Rechercheaufwand nötig. "
        + OUTPUT_RULE
    ),
}

TASKS["performance_analysis"] = {
    "subject": "Performance-Analyse xelsius – KW {kw}",
    "prompt": (
        "Du bist der Performance-Analyse-Agent für Daniel Schildwächter (LinkedIn-Personal-Brand nevoLAB/xelsius). Du hast KEINEN Live-Zugriff auf LinkedIn-Kennzahlen. Rechtiere mit der Websuche allgemeine Benchmarks für B2B-LinkedIn-Engagement im Chemie-/LabTech-Bereich, erstelle dann als HTML-E-Mail: (1) eine Kennzahlen-Checkliste mit Aufforderung an Daniel, seine letzten Zahlen einzutragen (Impressions, Engagement-Rate, Follower-Wachstum, Profilaufrufe, Klicks, Tops und Flops der letzten Posts); (2) typische Muster/Gegenmuster für Thought-Leadership-Content im DACH-B2B; (3) Platzhalter für 3–5 abgeleitete Learnings; (4) einen Vorschlag für 1 A/B-Experiment für die kommenden Wochen. "
        + OUTPUT_RULE
    ),
}

TASKS["smoke_test"] = {
    "subject": "xelsius-Workflow: Testlauf erfolgreich",
    "prompt": (
        "Du bist der Test-Agent des xelsius-Workflows. Erstelle als HTML-E-Mail (mit <!DOCTYPE html>): 'Der wöchentliche xelsius-Agent-Workflow läuft. Nächste geplante Läufe: Themen-Report Montag 07:00, LinkedIn-Content Mittwoch 07:00, Forschungs-Radar Freitag 07:00 (Europe/Berlin).' Keine Websuche nötig. "
        + OUTPUT_RULE
    ),
}


def _token() -> str:
    import os
    from pathlib import Path

    sa_path = os.environ.get("MISTRAL_SA_TOKEN_PATH")
    if sa_path and Path(sa_path).exists():
        return Path(sa_path).read_text(encoding="utf-8").strip()
    key = os.environ.get("MISTRAL_API_KEY")
    if key:
        return key
    raise RuntimeError("Weder MISTRAL_SA_TOKEN_PATH noch MISTRAL_API_KEY sind gesetzt.")


@workflows.activity()
async def run_agent_task(task: str, iso_week: int, outlook: ToolCallClient = Depends(outlook_connector)) -> str:
    spec = TASKS.get(task)
    if spec is None:
        raise ValueError(f"Unbekannter Task: {task!r}. Erlaubt: {sorted(TASKS) + ['auth_setup']}")

    if not iso_week:
        iso_week = datetime.now(TZ).isocalendar()[1]

    import os

    from mistralai.client import Mistral

    client = Mistral(api_key=_token())

    if task == "auth_setup":
        try:
            auth = await client.beta.connectors.get_auth_url_async(
                connector_id_or_name="outlook",
            )
            return "AUTH_URL: " + str(getattr(auth, "auth_url", auth))
        except Exception as e:
            return "AUTH_FEHLER: " + str(e)
    model = os.environ.get("XELSIUS_MODEL", "mistral-small-latest")
    prompt = spec["prompt"].format(kw=iso_week)

    response = await client.beta.conversations.start_async(
        model=model,
        inputs=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search"}],
    )

    parts = []
    for output in response.outputs:
        if getattr(output, "type", None) == "message.output":
            parts.append(output.content)
    html = "\n".join(parts)
    if "<html" not in html.lower():
        html = "<!DOCTYPE html><html><body>" + html + "</body></html>"

    subject = spec["subject"].format(kw=iso_week)

    await outlook.call_tool(
        tool_name="draft_outlook_email",
        arguments={
            "message_subject": subject,
            "message_to": RECIPIENT,
            "message_body": html,
            "_confirmationReason": "Automatisierter wöchentlicher xelsius-Agent-Entwurf",
        },
    )
    return "OK: Entwurf erstellt – " + subject


@workflows.workflow.define(
    name="xelsius-agent",
    workflow_display_name="xelsius Agent-Team",
    workflow_description=(
        "Wöchentliche/monatliche xelsius-Aufgaben: Themen-Report, LinkedIn-Content, "
        "Forschungs-Radar, Produkt-Report, Sales-Intelligenz, Erinnerung, Performance-Analyse."
    ),
)
@uses_connectors(outlook_connector)
class XelsiusAgentWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, task: str, iso_week: int = 0) -> str:
        return await run_agent_task(task, iso_week)
