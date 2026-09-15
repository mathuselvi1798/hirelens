"""Turn a flat blob of extracted text into structure.

This is the layer most resume tools skip, and it is why their AI prompts are
vague. Giving a model labelled sections and a clean bullet list produces
noticeably more consistent analysis than pasting raw text and hoping.

Everything here is deterministic - no AI, no network, fully unit-testable.
"""
import re

from app.schemas.document import ContactInfo, DocumentSection

# Canonical section name -> phrases that commonly introduce it.
SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "profile", "objective", "about me", "about"),
    "experience": (
        "experience", "work experience", "professional experience", "employment",
        "employment history", "work history", "career history",
    ),
    "education": ("education", "academic background", "academics", "qualifications"),
    "skills": ("skills", "technical skills", "core skills", "competencies", "core competencies", "skills & tools"),
    "projects": ("projects", "personal projects", "selected projects", "portfolio"),
    "certifications": ("certifications", "certificates", "licenses", "licences"),
    "awards": ("awards", "honors", "honours", "achievements", "accomplishments"),
    "publications": ("publications", "papers", "research"),
    "languages": ("languages",),
    "volunteering": ("volunteering", "volunteer experience", "community involvement"),
    "interests": ("interests", "hobbies", "activities"),
    "references": ("references",),
}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}")
# Resumes usually write links bare ("linkedin.com/in/name"), not as full URLs,
# so both forms are matched. The lookbehind stops the domain half of an email
# address ("name@example.com") from being picked up as a link.
_TLDS = "com|org|net|io|dev|ai|me|co|in|uk|edu|gov|xyz|tech|app"
URL_RE = re.compile(
    r"(?<![\w@.])(?:https?://|www\.)[^\s,;)\]]+"
    r"|(?<![\w@.])(?:[a-z0-9-]+\.)+(?:" + _TLDS + r")(?:/[^\s,;)\]]*)?",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*[-•‣◦⁃∙*·o]\s+(.{3,})$")


def _normalize_heading(line: str) -> str | None:
    """Return the canonical section name if this line looks like a heading."""
    cleaned = line.strip().strip(":").strip()
    if not cleaned or len(cleaned) > 50:
        return None
    # A heading is short, has few words, and is not a sentence.
    if len(cleaned.split()) > 5 or cleaned.endswith("."):
        return None

    lowered = re.sub(r"[^a-z& ]", "", cleaned.lower()).strip()
    for canonical, aliases in SECTION_ALIASES.items():
        if lowered in aliases:
            return canonical
    return None


def split_lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.splitlines()]


def detect_sections(text: str) -> list[DocumentSection]:
    lines = split_lines(text)
    found: list[DocumentSection] = []

    for idx, line in enumerate(lines):
        canonical = _normalize_heading(line)
        if canonical and not any(s.name == canonical for s in found):
            found.append(
                DocumentSection(
                    name=canonical, heading=line.strip(), content="", line_start=idx
                )
            )

    # Each section's content runs until the next detected heading.
    for i, section in enumerate(found):
        start = section.line_start + 1
        end = found[i + 1].line_start if i + 1 < len(found) else len(lines)
        section.content = "\n".join(lines[start:end]).strip()

    return found


def extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in split_lines(text):
        match = BULLET_RE.match(line)
        if match:
            bullet = match.group(1).strip()
            if bullet:
                bullets.append(bullet)
    return bullets


def extract_contact(text: str) -> ContactInfo:
    email_match = EMAIL_RE.search(text)

    phone = None
    # Only look in the first 15 lines - a "phone-like" number deeper in a
    # resume is far more likely to be a date range or a metric.
    header = "\n".join(split_lines(text)[:15])
    for candidate in PHONE_RE.finditer(header):
        digits = re.sub(r"\D", "", candidate.group(0))
        if 7 <= len(digits) <= 15:
            phone = candidate.group(0).strip()
            break

    links = []
    for match in URL_RE.finditer(text):
        url = match.group(0).rstrip(".,")
        if url not in links:
            links.append(url)

    return ContactInfo(
        email=email_match.group(0) if email_match else None,
        phone=phone,
        links=links[:10],
    )


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))
