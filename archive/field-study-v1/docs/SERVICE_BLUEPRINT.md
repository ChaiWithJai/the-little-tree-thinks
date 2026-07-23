# Nada Sadhana — Service Blueprint & UI Direction

*The question: Simply Sing, Swiftscales, and Yousician set the bar for voice-feedback UX.
Our only touchpoint is a web URL. What's the product direction that gets us that grade
of experience — and what's the demo bar?*

**The bar: stand in the West Village, demo it to a stranger, then hand them the phone.**

---

## 1. What the reference apps actually nail (mechanics, not skin)

| App | Signature mechanic | What it really does |
|---|---|---|
| **Simply Sing** | Vocal-range test → transposes every song *to your voice* | Personalization before content. You never fail for anatomical reasons |
| **Yousician** | Real-time pitch trace **against a visible target** | Feedback has a *reference*. You see the gap, not just yourself |
| **Swiftscales** | Structured micro-exercises with visible per-drill state | Progress is legible at the unit of one exercise, not one session |

The eigengate finding still governs (dominant axis: gamified-craft vs. sacred-content,
41% of variance — we refuse the either/or). So we take the **mechanics** and refuse the
**skin**: no stars, no streak-anxiety, no leagues. The mandala is the streak; the vrata
is the structure; "finding your Sa" is the range test.

## 2. The three magic moments (demo choreography)

A street demo is a sequence of under-30-second wonders, each one survivable by a stranger:

1. **"It found my note."** Open URL → "May we listen?" → hum anything → the tanpura
   *retunes itself to your Sa*. (Simply Sing's range test, reframed in the tradition's
   own vocabulary — sruti is literally this.)
2. **"It's singing with me."** First line appears (Devanagari + transliteration +
   meaning). The guru contour shows as a **ghost trace** on the lattice; your live
   trace lays over it. You see the gap close in real time. (Yousician's mechanic,
   no gamification.)
3. **"It works for them too."** Hand the phone over. The stranger hums; the drone
   meets *their* voice; their trace draws in their color. Personalization IS the
   shareable moment — and nothing they sang ever left the device.

## 3. The blueprint

```
CUSTOMER          tap URL ──► "may we   ──► hum one ──► receive line ──► call &  ──► day N
JOURNEY                        listen?"      note         by line        response     of 40
(emotions)        curiosity    safety        WONDER       absorption     flow         belonging
─────────────────────────────────────────────────────────────────────── LINE OF INTERACTION
FRONTSTAGE        instant      consent    tanpura snaps   ghost-trace   duck/lift    quiet
(what they see)   tanpura +    contract   to YOUR Sa      vs live       turns +      mandala
                  voice ribbon (1 screen) (<30s)          trace         mala         counter
─────────────────────────────────────────────────────────────────────── LINE OF VISIBILITY
BACKSTAGE         pitch worklet (on-device, metrics-only) · gapless audio-clock engine ·
(unseen, local)   learn-gate (recent voiced frames) · range→Sa estimator · SW offline shell
─────────────────────────────────────────────────────────────── LINE OF INTERNAL INTERACTION
SUPPORTING        llama-server (Bonsai, grammar-pinned JSON: key locked to user's Sa,
PROCESSES         tempo bounded) · session event log · scoring per stage · 3 privacy
                  topologies (paired laptop / hosted / self-hosted binary)
```

**The line of visibility is the product story.** Everything below it never receives raw
audio — the worklet emits numbers, the model emits JSON. "Hand the phone to a stranger"
is only a safe demo *because* of where that line sits. Privacy isn't a settings page;
it's the architecture, and the demo proves it.

## 4. What this implies we build next (ordered)

1. **Find-your-Sa onboarding** — the biggest gap vs. Simply Sing. We already pin
   `home_key` end-to-end (grammar-enforced); extend it from *chant's* key to *user's*
   Sa, chosen by a 10-second hum analysis. One new screen, one estimator function.
2. **Ghost target trace on the lattice** — author one reference contour per chant line
   (a few hours of work, one-time); render it under the live trace. Feedback gains a
   reference; "am I close?" becomes visible without a score.
3. **Per-line earned state on chant cards** — the win ladder (W1–W4) made quietly
   legible on the library screen. Swiftscales' per-drill clarity, vrata framing.
4. **The hand-off mode** — a one-tap "let a friend try" that scopes a guest session
   (no mandala writes), because the street demo ends with the phone in someone
   else's hands and their first session shouldn't overwrite yours.

## 5. Why a web URL is enough (and on-brand)

No install friction is a *feature* of the demo: the QR code on a card is the whole
distribution. The PWA shell (now with honest cache semantics, v6) makes the second
visit instant and offline-capable. The same URL is the TestFlight wrapper's content.
And every magic moment above runs on-device + on a local model — which is the
PrismML story told as an experience instead of a benchmark.
