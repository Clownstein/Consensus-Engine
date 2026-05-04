_GITHUB_BODY_LIMIT = 65_000


def render_review_body(result: dict) -> str:
    status = "APPROVED" if result["approved"] else "CHANGES REQUESTED"
    icon = "✅" if result["approved"] else "\U0001f6d1"
    lines = [
        f"# {icon} {status}",
        "",
        result["final_summary"],
        "",
        f"**Debate rounds completed:** {result['round_number']}",
        "",
        "---",
        "",
    ]

    for review in result["reviews"]:
        verdict_icon = "✅" if review["verdict"] == "approve" else "❌"
        lines += [
            f"## {verdict_icon} {review['agent_name']} `({review['provider']})`",
            "",
            f"| Verdict | Confidence | Correct | Secure | Working |",
            f"|---------|------------|---------|--------|---------|",
            (
                f"| `{review['verdict']}` "
                f"| `{review['confidence']:.0%}` "
                f"| `{review['correct']}` "
                f"| `{review['secure']}` "
                f"| `{review['working']}` |"
            ),
            "",
            review["summary"],
            "",
        ]

        if review["issues"]:
            lines.append("### Issues")
            lines.append("")
            for issue in review["issues"]:
                if issue["file"] and issue["line"]:
                    loc = f"`{issue['file']}:{issue['line']}`"
                elif issue["file"]:
                    loc = f"`{issue['file']}`"
                else:
                    loc = "_general_"

                blocking = " **[BLOCKS APPROVAL]**" if issue["blocks_approval"] else ""
                lines.append(
                    f"- **{issue['severity'].upper()} {issue['type']}**{blocking} "
                    f"at {loc}: {issue['description']}  \n"
                    f"  _Recommendation:_ {issue['recommendation']}"
                )
            lines.append("")

        rebuttal = review["rebuttal"]
        if rebuttal["accepted_points"] or rebuttal["rejected_points"]:
            lines.append("### Rebuttal")
            lines.append("")
            if rebuttal["changed_mind"]:
                lines.append("> This agent **changed its verdict** based on peer feedback.")
                lines.append("")
            if rebuttal["accepted_points"]:
                lines.append("**Accepted points from peers:**")
                for point in rebuttal["accepted_points"]:
                    lines.append(f"- {point}")
                lines.append("")
            if rebuttal["rejected_points"]:
                lines.append("**Rejected points from peers:**")
                for point in rebuttal["rejected_points"]:
                    lines.append(f"- {point}")
                lines.append("")

        lines.append("---")
        lines.append("")

    body = "\n".join(lines)
    if len(body.encode("utf-8")) > _GITHUB_BODY_LIMIT:
        body = body.encode("utf-8")[:_GITHUB_BODY_LIMIT].decode("utf-8", errors="ignore")
        body += "\n\n_(Review body truncated to fit GitHub limits.)_"
    return body
