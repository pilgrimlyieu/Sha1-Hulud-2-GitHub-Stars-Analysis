import os
from pathlib import Path

import polars as pl
import plotly.graph_objects as go

from .config import load_config


def analyze_attack_data(
    main_csv_path: str | None = None,
    awesome_files: dict | None = None,
    output_dir: str | None = None,
    config_path: str | None = None,
):
    cfg = load_config(config_path)
    main_csv_path = main_csv_path or cfg.get(
        "encrypted_output", "attack_data_encrypted.csv"
    )
    output_dir = output_dir or cfg.get("output_dir", "analysis_report")
    if awesome_files is None:
        awesome_files = cfg.get("awesome_files", {})

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    df = pl.read_csv(main_csv_path, try_parse_dates=True)
    df.columns = [c.strip().lower() for c in df.columns]
    # Keep only canonical columns
    df = df.select(["victim_user", "target_repo", "starred_at"])

    # Ensure timestamp is parsed
    try:
        df = df.with_columns(
            pl.col("starred_at").str.to_datetime(strict=False).alias("starred_at")
        )
    except Exception:
        pass

    # Add owner and repo name
    df = df.with_columns([
        pl.col("target_repo").str.split("/").list.get(0).alias("target_owner"),
        pl.col("target_repo").str.split("/").list.get(1).alias("repo_name"),
    ])

    # Owner stats
    owner_stats = (
        df.group_by("target_owner")
        .agg(pl.count().alias("attacks"))
        .sort("attacks", descending=True)
    )
    owner_stats.write_csv(os.path.join(output_dir, "owners.csv"))

    top_owners = owner_stats.head(20)
    fig_owner = go.Figure(
        data=[go.Bar(x=top_owners["target_owner"], y=top_owners["attacks"])]
    )
    fig_owner.update_layout(
        title="Top 20 attacked repository owners",
        xaxis_title="owner",
        yaxis_title="attack_count"
    )
    fig_owner.write_html(os.path.join(output_dir, "chart_1_top_owners.html"))
    fig_owner.write_image(os.path.join(output_dir, "chart_1_top_owners.png"))

    # Repo stats
    repo_stats = (
        df.group_by("target_repo")
        .agg(pl.count().alias("attacks"))
        .sort("attacks", descending=True)
    )
    repo_stats.write_csv(os.path.join(output_dir, "repos.csv"))

    top_repos = repo_stats.head(20)
    fig_repo = go.Figure(
        data=[go.Bar(x=top_repos["attacks"], y=top_repos["target_repo"], orientation="h")]
    )
    fig_repo.update_layout(
        title="Top 20 most attacked repositories",
        xaxis_title="attack_count",
        yaxis_title="repository",
        yaxis={"categoryorder": "total ascending"}
    )
    fig_repo.write_html(os.path.join(output_dir, "chart_2_top_repos.html"))
    fig_repo.write_image(os.path.join(output_dir, "chart_2_top_repos.png"))

    # Awesome list cross-check (uses implode to aggregate list)
    if awesome_files:
        summary_stats = []
        for list_name, file_path in awesome_files.items():
            try:
                aws_df = pl.read_csv(file_path, ignore_errors=True)
                aws_df.columns = [c.strip().lower() for c in aws_df.columns]

                if "username" in aws_df.columns and "repository" in aws_df.columns:
                    aws_df = aws_df.with_columns(
                        pl.format(
                            "{}/{}", pl.col("username"), pl.col("repository")
                        ).alias("full_name")
                    )
                else:
                    # skip if required columns are missing
                    continue

                imploded = aws_df.select(pl.col("full_name").implode())
                if imploded.height == 0:
                    continue
                target_repos = imploded.row(0)[0]

                matched_attacks = df.filter(pl.col("target_repo").is_in(target_repos))
                if matched_attacks.height == 0:
                    continue

                total_attacks = matched_attacks.height
                unique_repos_attacked = matched_attacks["target_repo"].n_unique()
                total_repos_in_list = aws_df.height

                summary_stats.append({
                    "list_name": list_name,
                    "total_attacks": total_attacks,
                    "attacked_repos_count": unique_repos_attacked,
                    "total_repos_in_list": total_repos_in_list,
                    "attack_coverage_pct": round(
                        (unique_repos_attacked / total_repos_in_list) * 100, 2
                    ),
                })

                list_detail_stats = (
                    matched_attacks.group_by("target_repo")
                    .agg(pl.count().alias("attacks"))
                    .sort("attacks", descending=True)
                )
                safe_name = list_name.replace(" ", "_")
                list_detail_stats.write_csv(
                    os.path.join(output_dir, f"awesome_detail_{safe_name}.csv")
                )

                top_list = list_detail_stats.head(20)
                fig_list = go.Figure(
                    data=[go.Bar(x=top_list["attacks"], y=top_list["target_repo"], orientation="h")]
                )
                fig_list.update_layout(
                    title=f"[{list_name}] Most attacked repos in list",
                    xaxis_title="attack_count",
                    yaxis_title="repository",
                    yaxis={"categoryorder": "total ascending"}
                )
                fig_list.write_html(
                    os.path.join(output_dir, f"awesome_chart_{safe_name}.html")
                )
                fig_list.write_image(
                    os.path.join(output_dir, f"awesome_chart_{safe_name}.png")
                )

            except Exception:
                continue

        if summary_stats:
            summary_df = pl.DataFrame(summary_stats).sort(
                "total_attacks", descending=True
            )
            summary_df.write_csv(os.path.join(output_dir, "awesome_summary.csv"))

            fig_summary = go.Figure(
                data=[go.Bar(
                    x=summary_df["list_name"],
                    y=summary_df["total_attacks"],
                    marker=dict(color=summary_df["attacked_repos_count"], colorscale="Viridis")
                )]
            )
            fig_summary.update_layout(
                title="Awesome lists comparison (total attacks)",
                xaxis_title="list_name",
                yaxis_title="total_attacks"
            )
            fig_summary.write_html(
                os.path.join(output_dir, "chart_3_awesome_comparison.html")
            )
            fig_summary.write_image(
                os.path.join(output_dir, "chart_3_awesome_comparison.png")
            )

    return True


if __name__ == "__main__":
    analyze_attack_data()
