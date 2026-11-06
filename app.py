"""NumberScope — local mobile-number OSINT lab (Streamlit UI).

Runs entirely on your machine against offline libphonenumber metadata. It does
not contact a phone, a carrier, a GPS service, or any lookup API, and it stores
nothing. See the "Ethics & limits" tab for the boundaries this lab keeps.
"""

from __future__ import annotations

import io
import json
import math

import pandas as pd
import streamlit as st

from numberscope import analyse_number, metadata_version
from numberscope.analysis import FIELD_NOTES, NumberReport
from numberscope.trilateration import DEMO_TOWERS, solve

# Validated categorical palette (dataviz skill, light mode). Fixed order,
# never cycled — assigned to categories by first appearance.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#008300", "#e34948"]

REGIONS = ["IN", "US", "GB", "CA", "AU", "DE", "FR", "SG", "AE", "JP", "BR", "ZA"]
EXAMPLES = {
    "— pick an example —": "",
    "India mobile (valid)": "+919876543210",
    "US number (valid)": "+14155552671",
    "UK London (valid)": "+442071838750",
    "Too short (invalid)": "+9112345",
    "Bad country code": "+9991234567",
}

st.set_page_config(
    page_title="NumberScope | Mobile Number OSINT Lab",
    page_icon="🔎",
    layout="wide",
)

# ---- Header ---------------------------------------------------------------
st.title("🔎 NumberScope")
st.caption(
    "Mobile Number OSINT Analyser · 100% local processing · "
    f"libphonenumber metadata `{metadata_version()}`"
)
st.info(
    "This tool reads **public numbering-plan metadata only**. It cannot identify a "
    "subscriber, confirm a SIM is active, or reveal a phone's live location. "
    "Use it only with numbers you own or are authorised to assess.",
    icon="🛡️",
)

tab_analyse, tab_batch, tab_learn, tab_demo, tab_ethics = st.tabs(
    ["🔬 Analyse", "📑 Batch", "🎓 Learn", "📐 Trilateration demo", "⚖️ Ethics & limits"]
)


# ---- Rendering helpers ----------------------------------------------------
def count_by(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return a tidy value-count frame sorted high→low for charting."""
    counts = frame[column].value_counts().reset_index()
    counts.columns = ["category", "Count"]
    return counts


def render_bar(data: pd.DataFrame, field: str, value: str, title: str) -> None:
    """Horizontal categorical bar chart with direct value labels.

    Thin marks, rounded data-ends, fixed-order palette, direct labels (so the
    sub-3:1 fill contrast is backed by visible text), recessive axes.
    """
    categories = list(data[field])
    base = {
        "data": {"values": data.to_dict("records")},
        "encoding": {
            "y": {"field": field, "type": "nominal", "sort": "-x", "title": None,
                  "axis": {"labelLimit": 160}},
            "x": {"field": value, "type": "quantitative", "title": None,
                  "axis": {"grid": False, "tickMinStep": 1}},
        },
    }
    st.vega_lite_chart(
        {
            "title": {"text": title, "fontSize": 14, "anchor": "start"},
            "layer": [
                {
                    "mark": {"type": "bar", "cornerRadiusEnd": 4, "height": {"band": 0.62}},
                    "encoding": {
                        **base["encoding"],
                        "color": {
                            "field": field, "type": "nominal", "legend": None,
                            "scale": {"domain": categories, "range": PALETTE[: len(categories)]},
                        },
                        "tooltip": [
                            {"field": field, "type": "nominal", "title": "Category"},
                            {"field": value, "type": "quantitative"},
                        ],
                    },
                },
                {
                    "mark": {"type": "text", "align": "left", "dx": 4, "fontSize": 12},
                    "encoding": {
                        **base["encoding"],
                        "text": {"field": value, "type": "quantitative"},
                    },
                },
            ],
            "data": base["data"],
            "height": max(120, 34 * len(categories)),
        },
        use_container_width=True,
    )


def render_report(report: NumberReport) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Valid numbering range", "Yes" if report.valid_range else "No")
    c2.metric("Possible length", "Yes" if report.possible else "No")
    c3.metric("Number type", report.number_type)

    st.markdown("#### Formats")
    fmt = st.columns(2)
    fmt[0].write(f"**International:** `{report.international}`")
    fmt[0].write(f"**National:** `{report.national}`")
    fmt[0].write(f"**E.164:** `{report.e164}`")
    fmt[1].write(f"**RFC 3966:** `{report.rfc3966}`")
    fmt[1].write(f"**Country code:** `{report.country_calling_code}`")
    fmt[1].write(f"**Region:** `{report.region_code}`")
    st.write(f"**Length assessment:** {report.possible_reason}")

    st.markdown("#### Public numbering metadata")
    st.write(f"**Carrier-range metadata:** {report.carrier_metadata}")
    st.caption("ℹ️ " + FIELD_NOTES["carrier_metadata"])
    st.write(f"**Geographic range:** {report.range_description}")
    st.caption("ℹ️ " + FIELD_NOTES["range_description"])
    st.write(f"**Candidate time zones:** {', '.join(report.time_zones)}")
    st.caption("ℹ️ " + FIELD_NOTES["time_zones"])

    st.warning(
        "Interpretation limits: carrier metadata may refer to the original range "
        "assignee (numbers can be ported); a region or time zone is not the phone's "
        "present location; and a valid range does not prove the number is currently "
        "allocated, active, reachable, or owned by anyone.",
        icon="⚠️",
    )

    st.markdown("#### Export this report")
    exp = st.columns(2)
    exp[0].download_button(
        "⬇️ Download JSON",
        data=json.dumps(report.as_dict(), indent=2),
        file_name=f"numberscope_{report.e164.lstrip('+') or 'report'}.json",
        mime="application/json",
        use_container_width=True,
    )
    csv_buf = io.StringIO()
    pd.DataFrame([report.as_flat_row()]).to_csv(csv_buf, index=False)
    exp[1].download_button(
        "⬇️ Download CSV",
        data=csv_buf.getvalue(),
        file_name=f"numberscope_{report.e164.lstrip('+') or 'report'}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ---- Tab: Analyse ---------------------------------------------------------
with tab_analyse:
    example_choice = st.selectbox("Load an example (optional)", list(EXAMPLES))
    with st.form("single"):
        phone_input = st.text_input(
            "Phone number",
            value=EXAMPLES[example_choice],
            placeholder="+91XXXXXXXXXX",
            help="Use international format with a + country code when possible.",
        )
        default_region = st.selectbox(
            "Default region (used only when the number has no leading +)",
            options=REGIONS,
            index=0,
        )
        submitted = st.form_submit_button(
            "Analyse number", type="primary", use_container_width=True
        )
    if submitted:
        try:
            report = analyse_number(phone_input, default_region)
        except ValueError as error:
            st.error(str(error))
        else:
            render_report(report)


# ---- Tab: Batch -----------------------------------------------------------
with tab_batch:
    st.markdown(
        "Analyse many **test** numbers at once. Upload a CSV/TXT with one number "
        "per line (or a `number` column), or paste numbers below. "
        "**Only use numbers you own or are authorised to test.**"
    )
    paste = st.text_area(
        "Paste numbers (one per line)",
        placeholder="+919876543210\n+14155552671\n+442071838750",
        height=120,
    )
    uploaded = st.file_uploader("…or upload a .csv / .txt file", type=["csv", "txt"])
    batch_region = st.selectbox("Default region for batch", REGIONS, index=0, key="batch_region")

    raw_numbers: list[str] = []
    if paste.strip():
        raw_numbers += [line.strip() for line in paste.splitlines() if line.strip()]
    if uploaded is not None:
        text = uploaded.getvalue().decode("utf-8", errors="ignore")
        try:
            frame = pd.read_csv(io.StringIO(text))
            col = "number" if "number" in frame.columns else frame.columns[0]
            raw_numbers += [str(v).strip() for v in frame[col].dropna()]
        except Exception:  # noqa: BLE001 — fall back to line-by-line parsing
            raw_numbers += [line.strip() for line in text.splitlines() if line.strip()]

    if st.button("Analyse batch", type="primary", disabled=not raw_numbers):
        rows, errors = [], []
        for number in raw_numbers:
            try:
                rows.append(analyse_number(number, batch_region).as_flat_row())
            except ValueError as exc:
                errors.append({"input": number, "error": str(exc)})
        if rows:
            frame = pd.DataFrame(rows)
            st.success(f"Analysed {len(rows)} number(s).")

            # ---- Analytics summary -----------------------------------
            st.markdown("#### Summary")
            k = st.columns(4)
            k[0].metric("Total", len(frame))
            k[1].metric("Valid range", int(frame["valid_range"].sum()))
            k[2].metric("Countries", frame["region_code"].nunique())
            k[3].metric("Mobile", int((frame["number_type"] == "Mobile").sum()))

            viz = st.columns(2)
            with viz[0]:
                render_bar(count_by(frame, "number_type"), "category", "Count", "By number type")
            with viz[1]:
                render_bar(count_by(frame, "region_code"), "category", "Count", "By region")

            st.markdown("#### Details")
            st.dataframe(frame, use_container_width=True, hide_index=True)
            out = io.StringIO()
            frame.to_csv(out, index=False)
            st.download_button(
                "⬇️ Download results CSV",
                data=out.getvalue(),
                file_name="numberscope_batch.csv",
                mime="text/csv",
            )
        if errors:
            st.warning(f"{len(errors)} input(s) could not be parsed.")
            st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True)


# ---- Tab: Learn -----------------------------------------------------------
with tab_learn:
    st.markdown("### How to read a number responsibly")
    st.markdown(
        "- **Possible vs. valid.** *Possible* only checks the length fits the plan. "
        "*Valid* checks the number falls in an assigned range. Neither means the "
        "number is actually allocated to anyone right now.\n"
        "- **Carrier ≠ current operator.** The carrier field names the operator a "
        "*range* was assigned to. **Mobile Number Portability** lets a subscriber "
        "keep a number while switching operators, so this can be out of date.\n"
        "- **Geography is coarse.** The geographic range describes the numbering "
        "block, historically tied to a circle/region — not where the handset is.\n"
        "- **Time zones are candidates**, derived from the range, not the device."
    )
    st.markdown("### Defensive OSINT: reduce your own exposure")
    st.markdown(
        "- Treat your primary number like an identifier: avoid posting it publicly "
        "and use a separate number for sign-ups where possible.\n"
        "- Enable a **SIM-swap / port-out PIN** with your operator and use "
        "app-based or hardware 2FA instead of SMS where you can.\n"
        "- Be sceptical of services that claim to 'track any number live' — in most "
        "jurisdictions precise location is held by licensed operators and released "
        "only to law enforcement under lawful process. Such sites are typically "
        "scams or unlawful."
    )
    st.markdown("### Why real-time tracking is *not* in this tool")
    st.markdown(
        "Locating a person from their number requires privileged access to carrier "
        "signalling (e.g. SS7/Diameter) or on-device GPS with consent. This lab "
        "intentionally implements none of that; the trilateration tab is pure, "
        "synthetic geometry."
    )


# ---- Tab: Trilateration demo ---------------------------------------------
with tab_demo:
    st.info(
        "Educational simulation only. Fictional towers and sample ranges on an "
        "arbitrary plane — no phone numbers, radio signals, carrier systems, maps, "
        "or real locations. It cannot track anyone.",
        icon="📐",
    )
    noise = st.slider(
        "Measurement noise added to the demo (demo km)",
        0.0, 3.0, 0.0, 0.1,
        help="Increase to see how inconsistent ranges blur the estimate.",
    )
    cols = st.columns(3)
    base_ranges = (4.2, 5.8, 4.1)
    sample_ranges = tuple(
        cols[i].slider(
            f"{DEMO_TOWERS[i][0]} range (km)",
            1.0, 15.0, base_ranges[i], 0.1, key=f"r{i}",
        )
        for i in range(3)
    )
    noisy = tuple(max(0.1, r + (noise if i == 1 else -noise)) for i, r in enumerate(sample_ranges))

    try:
        result = solve(noisy)
    except ValueError as error:
        st.error(f"Could not calculate the demo estimate: {error}")
    else:
        m = st.columns(2)
        m[0].metric("Estimated coordinates", f"E {result.x:.2f} · N {result.y:.2f} km")
        m[1].metric(
            "Fit quality (RMS error)",
            f"{result.rms_error:.3f} km",
            help="0 means the three ranges agree perfectly.",
        )
        if not result.is_consistent:
            st.caption(
                "⚠️ The ranges disagree, so no single point satisfies all three. "
                "The estimate is a least-geometry compromise — exactly why real "
                "positioning is uncertain."
            )

        # Towers + estimate + range circles for a readable teaching chart.
        points = [
            {"label": t[0], "x": t[1], "y": t[2], "kind": "Tower"} for t in DEMO_TOWERS
        ]
        points.append({"label": "Estimate", "x": result.x, "y": result.y, "kind": "Estimate"})
        circles = []
        for (label, tx, ty), rng in zip(DEMO_TOWERS, noisy, strict=True):
            for deg in range(0, 360, 6):
                rad = math.radians(deg)
                circles.append(
                    {"tower": label, "x": tx + rng * math.cos(rad),
                     "y": ty + rng * math.sin(rad)}
                )
        st.vega_lite_chart(
            {
                "layer": [
                    {
                        "data": {"values": circles},
                        "mark": {"type": "point", "size": 6, "opacity": 0.35},
                        "encoding": {
                            "x": {"field": "x", "type": "quantitative", "title": "East (demo km)"},
                            "y": {"field": "y", "type": "quantitative", "title": "North (demo km)"},
                            "color": {"field": "tower", "type": "nominal", "title": "Range circle"},
                        },
                    },
                    {
                        "data": {"values": points},
                        "mark": {"type": "point", "filled": True, "size": 220},
                        "encoding": {
                            "x": {"field": "x", "type": "quantitative"},
                            "y": {"field": "y", "type": "quantitative"},
                            "shape": {"field": "kind", "type": "nominal", "title": "Point"},
                            "color": {"field": "label", "type": "nominal", "title": "Point"},
                            "tooltip": [
                                {"field": "label"},
                                {"field": "x", "type": "quantitative"},
                                {"field": "y", "type": "quantitative"},
                            ],
                        },
                    },
                ],
                "height": 420,
            },
            use_container_width=True,
        )
        st.dataframe(
            [
                {
                    "Fictional tower": t[0],
                    "Entered range (km)": round(rng, 2),
                    "Residual (km)": round(res, 3),
                }
                for t, rng, res in zip(DEMO_TOWERS, noisy, result.residuals, strict=True)
            ],
            hide_index=True,
            use_container_width=True,
        )


# ---- Tab: Ethics & limits -------------------------------------------------
with tab_ethics:
    st.markdown("### What this lab deliberately does **not** do")
    st.markdown(
        "- ❌ No GPS tracking, cell-tower queries, SS7/Diameter access, or subscriber lookup.\n"
        "- ❌ No requests to lookup websites, data brokers, or third-party APIs.\n"
        "- ❌ No phone numbers written to a database or saved by this app.\n"
        "- ✅ Only offline numbering-plan metadata from libphonenumber."
    )
    st.markdown("### Responsible-use checklist")
    st.markdown(
        "1. Start with your own number, or one whose owner explicitly agreed.\n"
        "2. Prefer international `+<country><number>` format.\n"
        "3. Treat carrier / geographic / time-zone fields as approximate plan "
        "metadata, not device telemetry.\n"
        "4. Do not add scraping, data-broker lookups, messaging, or tracking "
        "without a clearly lawful purpose and the subject's authorisation."
    )
    st.caption(
        "Metadata source: the open-source `phonenumbers` port of Google's "
        f"libphonenumber (installed version `{metadata_version()}`). "
        "Results depend on the installed metadata."
    )
